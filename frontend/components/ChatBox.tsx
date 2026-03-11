'use client';
import { useState } from 'react';
import ChatMessage from './ChatMessage';

type Message = { role: 'user' | 'assistant'; text: string };

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: "Hello! I'm FertiGuide AI. Ask me anything about fertility treatments, protocols, or procedures." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setLoading(true);

    try {
      if (!BACKEND_URL) {
        throw new Error('Missing NEXT_PUBLIC_BACKEND_URL');
      }

      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) {
        throw new Error(`Backend request failed with ${res.status}`);
      }

      const data = (await res.json()) as { response?: string };
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.response ?? 'Sorry, I could not generate a response.'
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Sorry, I had trouble connecting. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} text={msg.text} />
        ))}
        {loading && (
          <div className="flex justify-start mb-3">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <span className="text-gray-400 text-sm">FertiGuide is thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white p-4 flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about IVF, IUI, FET protocols..."
          className="flex-1 rounded-xl border border-gray-300 px-4 py-2 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-emerald-600 text-white px-5 py-2 rounded-xl text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
