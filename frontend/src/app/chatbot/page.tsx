'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, BookOpen, Loader2, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api-client';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';

// 後端回傳格式：sender = 'user' | 'bot' | 'agent'
// 前端顯示：'user' 靠右藍底；'bot' / 'agent' 靠左白底（一律當客服訊息）
interface Message {
  id?: string;
  sender: 'user' | 'bot' | 'agent';
  content: string;
  created_at?: string;
}

const QUICK_REPLIES = [
  '保單怎麼查',
  '理賠如何申請',
  '續保比價在哪',
  '車禍/SOS 怎麼用',
  '帳戶資料修改',
  '法規查詢',
  '轉人工客服',
];

export default function ChatbotPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      content: '您好！這裡是 BOPINAN 服務導引中心 📖\n從下方按鈕快速找到您需要的功能,或輸入關鍵字（如「保單」「理賠」「續保」「SOS」）查詢操作說明。\n\n若需專人協助,輸入「轉人工」會直接通知業務員或客服。',
    },
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
      // 後端會把使用者剛送的訊息 + bot/agent 回覆都回傳;前端只追加 bot/agent 的(使用者訊息 handleSend 已 optimistic 加過)
      const botMessages = newMessages.filter((m) => m.sender !== 'user');
      if (botMessages.length > 0) {
        setMessages((prev) => [...prev, ...botMessages]);
      }
    },
  });

  const handleSend = (text?: string) => {
    const content = text ?? input.trim();
    if (!content || sendMessage.isPending) return;

    setMessages((prev) => [...prev, { sender: 'user', content }]);
    setInput('');
    sendMessage.mutate(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!__authReady) return null;

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Chat Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 bg-white">
        <button onClick={() => router.back()} className="text-primary-500">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100">
            <BookOpen className="h-4 w-4 text-primary-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">服務導引</p>
            <p className="text-[10px] text-gray-500">FAQ · 操作指引</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto chat-scroll px-4 py-4 space-y-3 bg-gray-50">
        {messages.map((msg, i) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={i}
              className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 mr-2 mt-0.5">
                  <BookOpen className="h-3.5 w-3.5 text-primary-500" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-line ${
                  isUser
                    ? 'bg-primary-500 text-white rounded-br-md'
                    : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-md'
                }`}
              >
                {msg.content}
              </div>
            </div>
          );
        })}
        {sendMessage.isPending && (
          <div className="flex justify-start">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 mr-2">
              <BookOpen className="h-3.5 w-3.5 text-primary-500" />
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
            placeholder="輸入關鍵字找操作指引..."
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
