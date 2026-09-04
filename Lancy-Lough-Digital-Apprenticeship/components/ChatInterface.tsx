import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import { getChatResponse } from '../services/geminiService';
import Card from './Card';

// Performance optimization: Memoize ChatInterface component to prevent redundant re-renders
// when parent component updates state (e.g. active scroll section during user scrolling).
const ChatInterface: React.FC = React.memo(() => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!isCollapsed) {
      scrollToBottom();
    }
  }, [messages, isCollapsed]);

  // Sentinel Security Enhancement: Limit input length to mitigate DoS / prompt bloat risks.
  const MAX_INPUT_LENGTH = 500;

  const handleSendMessage = async () => {
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
  };

  return (
    <Card className={`fixed bottom-4 right-4 w-80 ${isCollapsed ? 'h-auto' : 'h-96'} flex flex-col bg-gray-900 shadow-2xl z-50 p-0 overflow-hidden transition-all duration-300 ease-in-out`}>
      <div
        className="bg-teal-700 text-white px-4 py-3 font-bold flex items-center justify-between cursor-pointer select-none"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center space-x-2">
          <span>DeepSeek AI Chat</span>
          <img src="https://picsum.photos/20/20" alt="AI Icon" className="rounded-full" />
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setIsCollapsed(!isCollapsed);
          }}
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? 'Expand DeepSeek AI chat widget' : 'Collapse DeepSeek AI chat widget'}
          className="text-teal-100 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-200 rounded px-1.5 py-0.5 transition-colors duration-150 text-xs"
        >
          {isCollapsed ? '▲' : '▼'}
        </button>
      </div>

      {!isCollapsed && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {messages.length === 0 && (
              <p className="text-gray-400 text-sm text-center italic mt-4">
                Ask me anything about the LOUGH system or Lancy Lough's techniques! (Unlike Mikey's advice, these insights won't blow out your linework.)
              </p>
            )}
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[75%] px-4 py-2 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg">
                  <span className="animate-pulse">Typing...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="border-t border-gray-700 p-4 flex items-center">
            <input
              type="text"
              aria-label="Type your message"
              className="flex-1 bg-gray-700 text-white border border-gray-600 rounded-lg px-3 py-2 mr-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus:border-teal-500 disabled:opacity-50"
              placeholder="Type your message..."
              value={input}
              maxLength={MAX_INPUT_LENGTH}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isLoading && input.trim()) {
                  handleSendMessage();
                }
              }}
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              aria-label="Send message"
              className="bg-teal-600 hover:bg-teal-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[70px]"
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                'Send'
              )}
            </button>
          </div>
        </>
      )}
    </Card>
  );
});

export default ChatInterface;
