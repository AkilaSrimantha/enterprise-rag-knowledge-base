'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, DocumentItem } from '@/types';
import { MessageBubble } from './MessageBubble';
import { chatApi, documentsApi } from '@/lib/apiClient';
import { Send, Sparkles, Filter, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your Enterprise RAG assistant. Ask me anything about your uploaded documents, and I will provide answers with exact source page citations.',
      timestamp: 'Just now',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [availableDocs, setAvailableDocs] = useState<DocumentItem[]>([]);
  const [selectedDocFilter, setSelectedDocFilter] = useState<string>('all');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load available indexed documents for source filtering
    documentsApi.getDocuments()
      .then((docs) => setAvailableDocs(docs))
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputQuery.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentQuery = inputQuery;
    setInputQuery('');
    setIsLoading(true);

    try {
      const filter = selectedDocFilter !== 'all' ? [selectedDocFilter] : undefined;
      const res = await chatApi.sendQuery(currentQuery, filter);

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ Failed to retrieve answer. Please make sure the FastAPI backend is running and your API key is configured.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Chat cleared. How can I help you with your knowledge base?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Chat Header Toolbar */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-100 text-blue-600 rounded-lg">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-gray-900">RAG Assistant</h2>
            <p className="text-[11px] text-gray-500">Retrieval Augmented Generation with verified page citations</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Document Scope Filter */}
          <div className="flex items-center gap-1.5 text-xs text-gray-600">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={selectedDocFilter}
              onChange={(e) => setSelectedDocFilter(e.target.value)}
              className="text-xs bg-white border border-gray-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">All Documents ({availableDocs.length})</option>
              {availableDocs.map((doc) => (
                <option key={doc.id} value={doc.filename}>
                  {doc.filename}
                </option>
              ))}
            </select>
          </div>

          <Button variant="ghost" size="sm" onClick={handleClearHistory} title="Clear conversation">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex gap-3 my-4">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-gray-100 rounded-2xl p-4 text-xs text-gray-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
              Searching vector embeddings and synthesizing answer with citations...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Footer */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-100 bg-gray-50/50">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask questions about your uploaded documents (e.g. 'What are the termination clauses?')..."
            className="flex-1 bg-white border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 shadow-sm transition-all"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !inputQuery.trim()} className="px-5 rounded-xl">
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
      </form>
    </div>
  );
};
