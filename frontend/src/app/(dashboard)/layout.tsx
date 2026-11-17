'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Bot, MessageSquare, Files, ShieldCheck, LogOut, User as UserIcon } from 'lucide-react';
import { authApi } from '@/lib/apiClient';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [userRole, setUserRole] = useState<string>('viewer');
  const [userEmail, setUserEmail] = useState<string>('');
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('rag_token');
      if (!token) {
        router.push('/login');
        return;
      }
      const role = localStorage.getItem('rag_role') || 'viewer';
      const email = localStorage.getItem('rag_email') || 'User';
      setUserRole(role);
      setUserEmail(email);
      setIsReady(true);

      // Guard /admin route for non-admins
      if (pathname === '/admin' && role !== 'admin') {
        router.push('/chat');
      }
    }
  }, [pathname, router]);

  const handleLogout = () => {
    authApi.logout();
    router.push('/login');
  };

  const navLinks = [
    {
      name: 'RAG Chat',
      href: '/chat',
      icon: MessageSquare,
      description: 'AI query with citations',
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: Files,
      description: 'PDF & Word ingestion',
    },
    {
      name: 'Admin & RBAC',
      href: '/admin',
      icon: ShieldCheck,
      description: 'User roles & permissions',
      adminOnly: true,
    },
  ];

  const visibleLinks = navLinks.filter((link) => !link.adminOnly || userRole === 'admin');

  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col justify-between shrink-0 shadow-sm">
        <div>
          {/* Brand Logo Header */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-sm text-gray-900 leading-tight">RAG Knowledge</h1>
              <span className="text-[10px] text-gray-400 font-medium">Enterprise Assistant</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            {visibleLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                  <div className="truncate">
                    <div>{link.name}</div>
                    <div className="text-[10px] text-gray-400 font-normal">{link.description}</div>
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Account / Role & Logout */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-gray-700 shrink-0">
                <UserIcon className="w-3.5 h-3.5" />
              </div>
              <div className="truncate min-w-0">
                <span className="text-xs font-semibold text-gray-800 block truncate" title={userEmail}>
                  {userEmail || 'Active Session'}
                </span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-wider inline-block ${
                    userRole === 'admin'
                      ? 'bg-purple-100 text-purple-700'
                      : userRole === 'editor'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {userRole}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-gray-200"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>
    </div>
  );
}
