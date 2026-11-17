'use client';

import React from 'react';
import { ChatMessage } from '@/types';
import { CitationBadge } from './CitationBadge';
import { Bot, User as UserIcon } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex gap-3 my-4 ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      {/* Bot Icon */}
      {isAssistant && (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
      )}

      {/* Bubble Container */}
      <div
        className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${
          isAssistant
            ? 'bg-white border border-gray-200 text-gray-800'
            : 'bg-blue-600 text-white rounded-br-none'
        }`}
      >
        {/* Message Content */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
          {message.content}
        </div>

        {/* Citations Section */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-100">
            <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block mb-2">
              Verified Sources & Citations
            </span>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, index) => (
                <CitationBadge key={index} citation={citation} index={index} />
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div
          suppressHydrationWarning={true}
          className={`text-[10px] mt-2 flex items-center gap-1 ${
            isAssistant ? 'text-gray-400' : 'text-blue-100 justify-end'
          }`}
        >
          {message.timestamp}
        </div>
      </div>

      {/* User Icon */}
      {!isAssistant && (
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm">
          <UserIcon className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
