'use client';

import { Suspense, useEffect, useRef, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Send,
  Leaf,
  Download,
  Share2,
  ArrowLeft,
  User,
  Bot,
  Sun,
  Moon,
  Info,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ProfileSidebar } from '@/components/ProfileSidebar';
import { MistralLogo, MistralLogoAnimated } from '@/components/MistralLogo';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ProfileSummary {
  rfr?: number;
  household_size?: number;
  income_bracket?: string;
  bracket_color?: string;
  commune?: string;
  dpe_class?: string;
  property_type?: string;
  surface_m2?: number;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId || '');
  const [profile, setProfile] = useState<ProfileSummary>({});
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize session with welcome message
  useEffect(() => {
    if (!currentSessionId) return;

    const initSession = async () => {
      try {
        // Try to get existing history
        const res = await fetch(`${API_URL}/api/session/${currentSessionId}/history`);
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
            return;
          }
        }
      } catch (e) {
        // Session doesn't have history yet
      }

      // Add welcome message
      setMessages([
        {
          role: 'assistant',
          content:
            "Bonjour ! Je suis **GreenRights**, votre conseiller en aides à la transition écologique. 🌿\n\n" +
            "Je peux vous aider à découvrir les aides financières pour :\n" +
            "- 🏠 **La rénovation énergétique** de votre logement (MaPrimeRénov', CEE, Éco-PTZ…)\n" +
            "- 🚗 **La mobilité propre** (prime à la conversion, bonus vélo, prime ZFE…)\n\n" +
            "Par quoi souhaitez-vous commencer ?",
          timestamp: new Date().toISOString(),
        },
      ]);
    };

    initSession();
  }, [currentSessionId]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: Message = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // Add a placeholder assistant message that we'll stream into
    const placeholderMsg: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, placeholderMsg]);

    try {
      const res = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: trimmed,
          language: 'fr',
        }),
      });

      if (!res.ok) throw new Error('Chat request failed');

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE lines
        const lines = buffer.split('\n');
        // Keep the last potentially incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === 'session' && event.session_id) {
              if (event.session_id !== currentSessionId) {
                setCurrentSessionId(event.session_id);
              }
            } else if (event.type === 'token') {
              // Append token to the last (streaming) message
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + event.content,
                  };
                }
                return updated;
              });
            } else if (event.type === 'profile' && event.data) {
              setProfile(event.data);
            } else if (event.type === 'tool') {
              // Tool is being called — show a subtle indicator in the message
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant' && last.content === '') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: `_🔍 Consultation des données (${event.name})…_\n\n`,
                  };
                }
                return updated;
              });
            } else if (event.type === 'done') {
              // Clear the tool indicator prefix if it was the only content
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  // Remove the tool indicator line if the real content follows
                  const cleaned = last.content.replace(
                    /^_🔍 Consultation des données \([^)]+\)…_\n\n/,
                    ''
                  );
                  if (cleaned !== last.content) {
                    updated[updated.length - 1] = { ...last, content: cleaned };
                  }
                }
                return updated;
              });
            } else if (event.type === 'error') {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: event.message || "Désolé, une erreur s'est produite.",
                  };
                }
                return updated;
              });
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === 'assistant') {
          updated[updated.length - 1] = {
            ...last,
            content: "Désolé, une erreur s'est produite. Veuillez réessayer.",
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const downloadPDF = async () => {
    try {
      // First generate the report
      await fetch(`${API_URL}/api/report/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId }),
      });

      // Then download PDF
      const res = await fetch(`${API_URL}/api/report/${currentSessionId}/pdf`);
      if (!res.ok) throw new Error('PDF generation failed');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `greenrights-report.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF error:', err);
    }
  };

  const shareReport = async () => {
    try {
      const res = await fetch(`${API_URL}/api/report/${currentSessionId}/share`);
      if (!res.ok) throw new Error('Share failed');
      const data = await res.json();
      await navigator.clipboard.writeText(data.share_url);
      alert('Lien copié dans le presse-papier !');
    } catch (err) {
      console.error('Share error:', err);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Sidebar */}
      <ProfileSidebar profile={profile} isOpen={showSidebar} onClose={() => setShowSidebar(false)} />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-500" />
            </Link>
            <div className="flex items-center gap-2">
              <Leaf className="w-6 h-6 text-green-600" />
              <span className="font-semibold text-gray-900 dark:text-white">GreenRights</span>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] text-gray-400 dark:text-gray-500 ml-1">
                <MistralLogo className="w-3 h-3 inline" />
                Mistral
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors md:hidden"
              title="Voir le profil"
            >
              <Info className="w-5 h-5 text-gray-500" />
            </button>
            <button
              onClick={downloadPDF}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="Télécharger PDF"
            >
              <Download className="w-5 h-5 text-gray-500" />
            </button>
            <button
              onClick={shareReport}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title="Partager"
            >
              <Share2 className="w-5 h-5 text-gray-500" />
            </button>
            <ThemeToggle />
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.filter((msg) => msg.content !== '').map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 message-enter ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-green-600 dark:text-green-400" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose-chat text-gray-800 dark:text-gray-200 text-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {/* Typing indicator — show only while waiting for first token */}
          {isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && messages[messages.length - 1]?.content === '' && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex-shrink-0 p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Décrivez votre situation ou posez une question…"
              rows={1}
              className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              style={{ minHeight: '44px', maxHeight: '120px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 120) + 'px';
              }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-11 h-11 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-xl flex items-center justify-center transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-400 text-center mt-2 flex items-center justify-center gap-1">
            <MistralLogo className="w-3 h-3 inline" />
            GreenRights utilise des barèmes officiels. Les montants sont indicatifs — consultez un conseiller France Rénov&apos; pour validation.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <MistralLogoAnimated className="w-12 h-12" />
          <div className="w-6 h-6 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Chargement…</p>
        </div>
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}