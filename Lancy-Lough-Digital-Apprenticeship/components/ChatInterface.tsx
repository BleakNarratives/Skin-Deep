import React, { useState, useEffect, useRef, useCallback } from 'react';
import Card from './Card';
import { ChatMessage } from '../types';
import { getChatResponse } from '../services/geminiService';

// Performance optimization: Memoize ChatMessageItem component to avoid re-rendering existing
// chat bubble DOM elements on every keystroke in the input text field.
const ChatMessageItem = React.memo(({ message }: { message: ChatMessage }) => {
  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] px-4 py-2 rounded-lg ${
          message.role === 'user' ? 'bg-teal-600 text-white' : 'bg-gray-700 text-gray-100'
        }`}
      >
        {message.text}
      </div>
    </div>
  );
});

// Performance optimization: Memoize ChatInterface component to prevent redundant re-renders
// when parent component updates state (e.g. active scroll section during user scrolling).
const ChatInterface: React.FC = React.memo(() => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (!isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    if (!isMinimized) {
      scrollToBottom();
    }
  }, [messages, isMinimized]);

  // Sentinel Security Enhancement: Limit input length to mitigate DoS / prompt bloat risks.
  const MAX_INPUT_LENGTH = 500;

  // Performance optimization: Wrap handleSendMessage in useCallback to stabilize function reference
  // across keystrokes and prevent unnecessary child component updates.
  const handleSendMessage = useCallback(async () => {
    const sanitizedInput = input.trim().slice(0, MAX_INPUT_LENGTH);
    if (sanitizedInput === '') return;

    const userMessage: ChatMessage = { role: 'user', text: sanitizedInput };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const geminiResponse = await getChatResponse(messages, sanitizedInput);
      const modelMessage: ChatMessage = { role: 'model', text: geminiResponse };
      setMessages((prevMessages) => [...prevMessages, modelMessage]);
    } catch (error) {
      // Sentinel Security: Avoid logging raw internal error objects to prevent leaking stack traces or sensitive data
      console.error("Error sending message to DeepSeek AI chat service");
      const errorMessage: ChatMessage = { role: 'model', text: "Sorry, I couldn't get a response. Please try again." };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, messages]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  }, []);

  if (isMinimized) {
    return (
      <button
        type="button"
        onClick={() => setIsMinimized(false)}
        aria-label="Open DeepSeek AI Chat (Unlike Mikey, our AI actually has answers!)"
        aria-expanded={false}
        className="fixed bottom-4 right-4 bg-teal-700 hover:bg-teal-600 text-white font-bold py-3 px-4 rounded-full shadow-2xl z-50 flex items-center space-x-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-all duration-200"
      >
        <img src="https://picsum.photos/24/24" alt="AI Icon" className="rounded-full" />
        <span className="text-sm">DeepSeek AI Chat</span>
      </button>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 w-80 h-96 flex flex-col bg-gray-900 shadow-2xl z-50 p-0 overflow-hidden border border-teal-500/30">
      <div className="bg-teal-700 text-white p-4 font-bold flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <img src="https://picsum.photos/20/20" alt="AI Icon" className="rounded-full" />
          <span>DeepSeek AI Chat</span>
        </div>
        <button
          type="button"
          onClick={() => setIsMinimized(true)}
          aria-label="Minimize DeepSeek AI Chat panel"
          aria-expanded={true}
          className="text-teal-100 hover:text-white p-1 rounded hover:bg-teal-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-300 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm text-center italic mt-4">
            Ask anything about LOUGH bio-telemetry or Lancy Lough's techniques (Unlike Mikey, our AI actually gives useful answers!).
          </p>
        )}
        {messages.map((msg, index) => (
          <ChatMessageItem key={index} message={msg} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg flex items-center space-x-2">
              <svg className="animate-spin h-4 w-4 text-teal-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="animate-pulse text-sm">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-700 p-3 flex items-center space-x-2 bg-gray-800">
        <input
          type="text"
          aria-label="Type your chat message to DeepSeek AI"
          className="flex-1 bg-gray-700 text-white border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus:border-teal-500 disabled:opacity-50"
          placeholder="Ask AI a question..."
          value={input}
          maxLength={MAX_INPUT_LENGTH}
          onChange={handleInputChange}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !isLoading && input.trim()) {
              handleSendMessage();
            }
          }}
          disabled={isLoading}
        />
        <button
          type="button"
          onClick={handleSendMessage}
          aria-label="Send message"
          className="bg-teal-600 hover:bg-teal-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 text-white font-medium text-sm py-2 px-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[60px]"
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? (
            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </Card>
  );
});

export default ChatInterface;