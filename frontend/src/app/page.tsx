import Link from 'next/link';
import { Bot, FileText, Shield, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen justify-center items-center px-4 bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="max-w-2xl w-full text-center space-y-6">
        <div className="inline-flex p-3 bg-blue-100 text-blue-600 rounded-2xl shadow-sm">
          <Bot className="w-8 h-8" />
        </div>

        <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl">
          RAG Knowledge Base
        </h1>
        
        <p className="text-base text-gray-600 max-w-lg mx-auto">
          Chat with your PDFs and Word documents with pinpoint citations down to the page number. Built with Next.js, FastAPI, and LangChain.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 shadow-md transition-all"
          >
            Open Chat Interface
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/documents"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white border border-gray-200 text-gray-700 font-medium hover:bg-gray-50 shadow-sm transition-all"
          >
            <FileText className="w-4 h-4" />
            Upload Documents
          </Link>
        </div>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 text-left">
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <Bot className="w-5 h-5 text-blue-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">Accurate Citations</h3>
            <p className="text-xs text-gray-500 mt-1">Cites exact source files and page numbers for complete transparency.</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <FileText className="w-5 h-5 text-blue-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">Multi-Format RAG</h3>
            <p className="text-xs text-gray-500 mt-1">PyMuPDF-powered page extraction for PDF and docx documents.</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <Shield className="w-5 h-5 text-blue-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">RBAC Security</h3>
            <p className="text-xs text-gray-500 mt-1">Role-based access control for Admins, Editors, and Viewers.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
