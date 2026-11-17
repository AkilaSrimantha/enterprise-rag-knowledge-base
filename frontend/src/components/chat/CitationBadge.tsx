'use client';

import React, { useState } from 'react';
import { Citation } from '@/types';
import { FileText, ExternalLink, X, BookOpen } from 'lucide-react';

interface CitationBadgeProps {
  citation: Citation;
  index: number;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, index }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors shadow-sm"
        title="View source citation"
      >
        <FileText className="w-3.5 h-3.5 text-blue-600" />
        <span className="max-w-[140px] truncate">{citation.document_name}</span>
        <span className="bg-blue-200 text-blue-800 px-1.5 py-0.2 rounded-full text-[10px] font-semibold">
          p. {citation.page_number}
        </span>
      </button>

      {/* Modal / Drawer for citation preview */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-lg bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50/75">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900 text-sm">Citation Reference #{index + 1}</h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between text-xs text-gray-500 bg-gray-50 p-2.5 rounded-lg border border-gray-100">
                <div className="flex items-center gap-1.5">
                  <span className="font-medium text-gray-700">Source:</span>
                  <span className="truncate max-w-[200px] text-gray-900 font-semibold">{citation.document_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-medium">
                    Page {citation.page_number}
                  </span>
                  {citation.score !== undefined && (
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">
                      Score: {citation.score}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">
                  Extracted Context Passage
                </label>
                <div className="text-sm text-gray-700 bg-gray-50/50 p-3.5 rounded-lg border border-gray-200 font-mono leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {citation.snippet}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end px-5 py-3 border-t border-gray-100 bg-gray-50">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
