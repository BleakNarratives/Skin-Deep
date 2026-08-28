
import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import { getChatResponse } from '../services/geminiService';
import Card from './Card';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      console.error("Error sending message to Gemini:", error);
      const errorMessage: ChatMessage = { role: 'model', text: "Sorry, I couldn't get a response. Please try again." };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="fixed bottom-4 right-4 w-80 h-96 flex flex-col bg-gray-900 shadow-2xl z-50 p-0 overflow-hidden">
      <div className="bg-teal-700 text-white p-4 font-bold flex items-center justify-between">
        <span>DeepSeek AI Chat</span>
        <img src="https://picsum.photos/20/20" alt="AI Icon" className="rounded-full" />
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm text-center italic mt-4">
            Ask me anything about the LOUGH system, Lancy Lough's techniques, or digital apprenticeship!
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
          className="flex-1 bg-gray-700 text-white border border-gray-600 rounded-lg px-3 py-2 mr-2 focus:outline-none focus:border-teal-500"
          placeholder="Type your message..."
          value={input}
          maxLength={MAX_INPUT_LENGTH}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !isLoading) {
              handleSendMessage();
            }
          }}
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200"
          disabled={isLoading}
        >
          Send
        </button>
      </div>
      {/* Removed billing info link as API key selection is no longer required. */}
    </Card>
  );
};

export default ChatInterface;
