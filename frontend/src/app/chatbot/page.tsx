'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Bot, Loader2, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api-client';

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

const QUICK_REPLIES = [
  '我的保單有哪些保障？',
  '如何申請理賠？',
  '理賠進度查詢',
  '續保相關問題',
  '保費怎麼算的？',
];

export default function ChatbotPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '您好！我是車險智能客服，請問有什麼可以幫您的嗎？' },
  ]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const createSession = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/chatbot/sessions');
      return res.data.data as { id: string; messages: Message[] };
    },
  });

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      let sid = sessionId;
      if (!sid) {
        const session = await createSession.mutateAsync();
        sid = session.id;
        setSessionId(sid);
      }
      const res = await api.post(`/api/v1/chatbot/sessions/${sid}/messages`, { content });
      return res.data.data as Message[];
    },
    onSuccess: (newMessages) => {
      const botMessages = newMessages.filter((m) => m.role === 'assistant');
      if (botMessages.length > 0) {
        setMessages((prev) => [...prev, ...botMessages]);
      }
    },
  });

  const handleSend = (text?: string) => {
    const content = text ?? input.trim();
    if (!content || sendMessage.isPending) return;

    setMessages((prev) => [...prev, { role: 'user', content }]);
    setInput('');
    sendMessage.mutate(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Chat Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 bg-white">
        <button onClick={() => router.back()} className="text-primary-500">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100">
            <Bot className="h-4 w-4 text-primary-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">智能客服</p>
            <p className="text-[10px] text-green-500">在線</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto chat-scroll px-4 py-4 space-y-3 bg-gray-50">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 mr-2 mt-0.5">
                <Bot className="h-3.5 w-3.5 text-primary-500" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary-500 text-white rounded-br-md'
                  : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-md'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {sendMessage.isPending && (
          <div className="flex justify-start">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 mr-2">
              <Bot className="h-3.5 w-3.5 text-primary-500" />
            </div>
            <div className="rounded-2xl bg-white px-4 py-3 shadow-sm border border-gray-100 rounded-bl-md">
              <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
            </div>
          </div>
        )}
      </div>

      {/* Quick Replies */}
      <div className="px-4 py-2 bg-white border-t border-gray-100 overflow-x-auto">
        <div className="flex gap-2">
          {QUICK_REPLIES.map((qr) => (
            <button
              key={qr}
              onClick={() => handleSend(qr)}
              disabled={sendMessage.isPending}
              className="shrink-0 rounded-full border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs text-primary-600 font-medium hover:bg-primary-100 transition disabled:opacity-50"
            >
              {qr}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-white border-t border-gray-100">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="輸入您的問題..."
            className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || sendMessage.isPending}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-500 text-white disabled:opacity-50 transition"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
