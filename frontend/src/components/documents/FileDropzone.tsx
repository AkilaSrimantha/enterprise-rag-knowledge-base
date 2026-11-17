'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { documentsApi } from '@/lib/apiClient';

interface FileDropzoneProps {
  onUploadSuccess?: () => void;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({ onUploadSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['pdf', 'docx', 'doc'];

  const validateAndAddFiles = (files: FileList | File[]) => {
    setStatusMessage(null);
    const validFiles: File[] = [];
    const invalidNames: string[] = [];

    Array.from(files).forEach((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext && allowedExtensions.includes(ext)) {
        validFiles.push(file);
      } else {
        invalidNames.push(file.name);
      }
    });

    if (invalidNames.length > 0) {
      setStatusMessage({
        type: 'error',
        text: `Skipped unsupported files: ${invalidNames.join(', ')}. Only PDF and DOCX are accepted.`,
      });
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || isUploading) return;

    setIsUploading(true);
    setStatusMessage(null);

    try {
      const response = await documentsApi.uploadDocuments(selectedFiles);
      setSelectedFiles([]);

      if (response.failed_documents && response.failed_documents.length > 0 && (!response.processed_documents || response.processed_documents.length === 0)) {
        const errorDetails = response.failed_documents.map((d: any) => `${d.filename}: ${d.error}`).join('; ');
        setStatusMessage({
          type: 'error',
          text: `Upload failed: ${errorDetails}`,
        });
      } else {
        setStatusMessage({
          type: 'success',
          text: response.message || `Successfully uploaded and indexed ${selectedFiles.length} document(s).`,
        });
        if (onUploadSuccess) onUploadSuccess();
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to upload documents. Please check backend status.';
      setStatusMessage({ type: 'error', text: msg });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50/50 scale-[1.01]'
            : 'border-gray-300 hover:border-gray-400 bg-gray-50/50'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple
          accept=".pdf,.docx,.doc"
          onChange={(e) => e.target.files && validateAndAddFiles(e.target.files)}
          className="hidden"
        />

        <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3 shadow-inner">
          <UploadCloud className="w-6 h-6" />
        </div>

        <h3 className="text-sm font-semibold text-gray-800">
          Click to upload or drag & drop documents
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Supports multi-file upload for <span className="font-semibold text-gray-700">PDF (.pdf)</span> and{' '}
          <span className="font-semibold text-gray-700">Word (.docx)</span> files
        </p>
      </div>

      {/* Selected File Previews */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-700">
              Files queued for vector indexing ({selectedFiles.length})
            </span>
            <Button
              variant="primary"
              size="sm"
              disabled={isUploading}
              onClick={handleUpload}
              className="gap-1.5"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Parsing & Embedding...
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  Upload All ({selectedFiles.length})
                </>
              )}
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {selectedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg border border-gray-100 text-xs"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                  <span className="truncate font-medium text-gray-800">{file.name}</span>
                  <span className="text-[10px] text-gray-400">
                    ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                {!isUploading && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFile(idx);
                    }}
                    className="text-gray-400 hover:text-red-500 p-1"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Feedback Banner */}
      {statusMessage && (
        <div
          className={`flex items-center gap-2 text-xs p-3.5 rounded-xl border ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-red-50 text-red-800 border-red-200'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}
    </div>
  );
};
