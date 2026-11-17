import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.schemas.models import LoginRequest, Token, UserResponse, UserRole, UserCreate
from app.core.security import create_access_token
from app.core.config import settings, supabase
from app.api.dependencies import get_current_user, require_role

router = APIRouter()


def ensure_roles_and_admin_accounts():
    """Ensure roles table has default roles and seed Admin/Editor accounts in Supabase Auth."""
    try:
        # 1. Seed roles if not present
        existing_roles = {r['name']: r['id'] for r in (supabase.table('roles').select('*').execute().data or [])}
        for r_name, desc in [('admin', 'Full Administrator'), ('editor', 'Content Editor'), ('viewer', 'Standard Viewer')]:
            if r_name not in existing_roles:
                res = supabase.table('roles').insert({'id': str(uuid.uuid4()), 'name': r_name, 'description': desc}).execute()
                existing_roles[r_name] = res.data[0]['id']

        # 2. Existing auth users
        auth_users = {u.email.lower(): u for u in supabase.auth.admin.list_users()}

        admin_email = settings.ADMIN_EMAIL.strip().lower()
        editor_email = settings.EDITOR_EMAIL.strip().lower()

        # Seed Admin if not exists
        if admin_email not in auth_users:
            adm_res = supabase.auth.admin.create_user({
                "email": admin_email,
                "password": settings.ADMIN_INITIAL_PASSWORD,
                "email_confirm": True,
                "user_metadata": {"role": "admin", "full_name": "System Administrator"}
            })
            supabase.table("users").upsert({
                "id": adm_res.user.id,
                "email": admin_email,
                "full_name": "System Administrator",
                "role_id": existing_roles.get("admin")
            }).execute()

        # Seed Editor if not exists
        if editor_email not in auth_users:
            ed_res = supabase.auth.admin.create_user({
                "email": editor_email,
                "password": settings.EDITOR_INITIAL_PASSWORD,
                "email_confirm": True,
                "user_metadata": {"role": "editor", "full_name": "Content Editor"}
            })
            supabase.table("users").upsert({
                "id": ed_res.user.id,
                "email": editor_email,
                "full_name": "Content Editor",
                "role_id": existing_roles.get("editor")
            }).execute()
    except Exception as e:
        print(f"[Warning] Failed to initialize default roles and accounts: {e}")

# Run setup
ensure_roles_and_admin_accounts()


@router.post("/register")
async def register(user_in: UserCreate):
    """
    Register a user account.
    - If special ADMIN_EMAIL: auto-provisioned as Admin with confirmed email.
    - If special EDITOR_EMAIL: auto-provisioned as Editor with confirmed email.
    - Any other email: registered as Viewer via Supabase Auth with real email confirmation.
    """
    email = user_in.email.strip().lower()
    full_name = user_in.full_name or email.split("@")[0].capitalize()

    is_admin = email == settings.ADMIN_EMAIL.strip().lower()
    is_editor = email == settings.EDITOR_EMAIL.strip().lower()

    role_str = "admin" if is_admin else ("editor" if is_editor else "viewer")

    try:
        if is_admin or is_editor:
            # Check if user already exists
            existing_user = next((u for u in supabase.auth.admin.list_users() if u.email.lower() == email), None)
            if existing_user:
                raise HTTPException(status_code=400, detail="An account with this special email already exists. Please log in.")

            auth_res = supabase.auth.admin.create_user({
                "email": email,
                "password": user_in.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "role": role_str
                }
            })
            user_id = auth_res.user.id
            needs_verification = False
        else:
            # Regular user: Supabase sends a real verification email!
            auth_res = supabase.auth.sign_up({
                "email": email,
                "password": user_in.password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "role": role_str
                    }
                }
            })
            if not auth_res.user:
                raise HTTPException(status_code=400, detail="Could not create user account.")
            user_id = auth_res.user.id
            needs_verification = auth_res.user.email_confirmed_at is None
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        if "already registered" in err_msg.lower() or "already exists" in err_msg.lower():
            raise HTTPException(status_code=400, detail="An account with this email address already exists.")
        if "rate limit" in err_msg.lower():
            # In Supabase Free tier, default SMTP is capped at 3-4 emails/hr.
            # Auto-confirm so registration doesn't block developers during testing
            try:
                auth_res = supabase.auth.admin.create_user({
                    "email": email,
                    "password": user_in.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name,
                        "role": role_str
                    }
                })
                user_id = auth_res.user.id
                needs_verification = False
            except Exception:
                raise HTTPException(status_code=400, detail=f"Registration failed: {err_msg}")
        else:
            raise HTTPException(status_code=400, detail=f"Registration failed: {err_msg}")

    # Sync to public.users table
    try:
        roles_data = supabase.table("roles").select("id").eq("name", role_str).execute().data
        role_id = roles_data[0]["id"] if roles_data else None
        supabase.table("users").upsert({
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role_id": role_id
        }).execute()
    except Exception as db_err:
        print(f"[Warning] Failed syncing to public.users table: {db_err}")

    if needs_verification:
        return {
            "message": f"Verification email sent to {email}! Please check your email inbox and click the verification link before signing in.",
            "needs_verification": True,
            "access_token": "",
            "role": role_str,
            "user_id": user_id
        }

    token = create_access_token(
        subject=email,
        role=role_str,
        user_id=user_id
    )
    return {
        "message": "Account created successfully!",
        "needs_verification": False,
        "access_token": token,
        "role": role_str,
        "user_id": user_id
    }


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """
    Authenticate user via Supabase Auth.
    Checks password and enforces real email confirmation.
    """
    email = credentials.email.strip().lower()

    # Supabase sign_in_with_password
    try:
        auth_res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": credentials.password
        })
    except Exception as e:
        err_msg = str(e)
        if "Email not confirmed" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your email has not been verified yet! Please check your email inbox and click the verification link before logging in."
            )
        elif "Invalid login credentials" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Please verify your credentials and try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Login failed: {err_msg}"
            )

    user = auth_res.user
    user_id = str(user.id)

    # Determine role
    is_admin = email == settings.ADMIN_EMAIL.strip().lower()
    is_editor = email == settings.EDITOR_EMAIL.strip().lower()

    if is_admin:
        role_str = "admin"
    elif is_editor:
        role_str = "editor"
    else:
        role_str = (user.user_metadata or {}).get("role")
        if not role_str:
            # Fallback to public.users table
            try:
                u_row = supabase.table("users").select("role_id").eq("id", user_id).execute().data
                if u_row and u_row[0].get("role_id"):
                    r_row = supabase.table("roles").select("name").eq("id", u_row[0]["role_id"]).execute().data
                    if r_row:
                        role_str = r_row[0]["name"]
            except Exception:
                pass
        role_str = role_str or "viewer"

    token = create_access_token(
        subject=email,
        role=role_str,
        user_id=user_id
    )

    return Token(
        access_token=token,
        role=role_str,
        user_id=user_id
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Return profile and permissions for currently authenticated user."""
    return current_user


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_role([UserRole.ADMIN]))])
async def list_all_users():
    """Admin-only: Retrieve all registered users from Supabase Auth & DB."""
    try:
        auth_users = supabase.auth.admin.list_users()
        user_list = []
        for u in auth_users:
            em = (u.email or "").lower()
            if em == settings.ADMIN_EMAIL.lower():
                r_val = UserRole.ADMIN
            elif em == settings.EDITOR_EMAIL.lower():
                r_val = UserRole.EDITOR
            else:
                meta_role = (u.user_metadata or {}).get("role", "viewer")
                r_val = UserRole(meta_role) if meta_role in UserRole.__members__.values() else UserRole.VIEWER

            user_list.append(UserResponse(
                id=str(u.id),
                email=u.email,
                full_name=(u.user_metadata or {}).get("full_name") or u.email.split("@")[0].capitalize(),
                role=r_val,
                is_active=u.email_confirmed_at is not None,
                created_at=datetime.fromisoformat(u.created_at.replace("Z", "+00:00")) if isinstance(u.created_at, str) else None
            ))
        return user_list
    except Exception as e:
        print(f"Error listing users: {e}")
        return []


@router.put("/users/{identifier}/role", dependencies=[Depends(require_role([UserRole.ADMIN]))])
async def update_user_role(identifier: str, new_role: UserRole):
    """Admin-only: Promote or demote user permissions in Supabase."""
    try:
        # Find user by ID or Email
        target_user = None
        for u in supabase.auth.admin.list_users():
            if str(u.id) == identifier or (u.email and u.email.lower() == identifier.lower()):
                target_user = u
                break

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found in Supabase Auth.")

        # Update Supabase user_metadata
        supabase.auth.admin.update_user_by_id(target_user.id, {
            "user_metadata": {
                **(target_user.user_metadata or {}),
                "role": new_role.value
            }
        })

        # Update public.users table role_id
        roles_data = supabase.table("roles").select("id").eq("name", new_role.value).execute().data
        if roles_data:
            supabase.table("users").update({"role_id": roles_data[0]["id"]}).eq("id", target_user.id).execute()

        return {"message": f"Successfully updated permissions for {target_user.email} to {new_role.value}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed updating user role: {str(e)}")
