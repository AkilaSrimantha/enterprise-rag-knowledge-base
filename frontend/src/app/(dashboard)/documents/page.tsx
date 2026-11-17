'use client';

import React, { useState, useEffect } from 'react';
import { FileDropzone } from '@/components/documents/FileDropzone';
import { DocumentItem } from '@/types';
import { documentsApi } from '@/lib/apiClient';
import { FileText, Trash2, RefreshCw, FileCheck, Layers, Calendar, HardDrive } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const data = await documentsApi.getDocuments();
      setDocuments(data);
    } catch {
      // Mock data for initial preview if backend is empty
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to remove this document and delete its vector embeddings?')) return;

    setDeletingId(docId);
    try {
      await documentsApi.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Document Management</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Upload PDF & Word documents to chunk and index into the RAG vector store
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchDocuments} className="gap-2">
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh List
        </Button>
      </div>

      {/* Multi-File Upload Dropzone */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-800 mb-3">Upload New Documents</h2>
        <FileDropzone onUploadSuccess={fetchDocuments} />
      </div>

      {/* Indexed Documents Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-blue-600" />
            <h2 className="text-sm font-semibold text-gray-900">
              Indexed Documents ({documents.length})
            </h2>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="p-12 text-center text-gray-400 space-y-2">
            <Layers className="w-8 h-8 mx-auto text-gray-300" />
            <p className="text-sm">No documents indexed in vector store yet.</p>
            <p className="text-xs text-gray-400">Use the dropzone above to upload your first PDF or Word document.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-600">
              <thead className="bg-gray-50/75 text-gray-500 font-semibold border-b border-gray-100 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Document Name</th>
                  <th className="px-6 py-3">Format</th>
                  <th className="px-6 py-3">Pages</th>
                  <th className="px-6 py-3">Vector Chunks</th>
                  <th className="px-6 py-3">Uploaded</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-3.5 font-medium text-gray-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="px-6 py-3.5">{doc.page_count} pages</td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700">
                        {doc.chunk_count} chunks
                      </span>
                    </td>
                    <td suppressHydrationWarning={true} className="px-6 py-3.5 text-gray-400">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id}
                        className="text-gray-400 hover:text-red-600 p-1 rounded-md transition-colors disabled:opacity-50"
                        title="Delete document and vector embeddings"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
