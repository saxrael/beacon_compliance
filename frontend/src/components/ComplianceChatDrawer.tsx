'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send,
  X,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Bot,
  Activity,
  Lightbulb,
  Brain,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { API_BASE_URL } from '@/config';
import { useAuth } from '@/context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { springs } from '@/lib/motion-tokens';
import { ClientPortal } from './ClientPortal';

export interface ActionItem {
  id: string;
  label: string;
  status: 'running' | 'completed' | 'failed';
}

interface ChatTurn {
  message_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking?: string | null;
  tool_calls?: any[];
  sources?: string[];
  created_at?: string;
  actions?: (string | ActionItem)[];
}

const DEFAULT_WELCOME_MESSAGE: ChatTurn = {
  role: 'assistant',
  content:
    "Welcome to the **Beacon Compliance Advisor** for Potter's House Christian Mission UK (SCIO, SC054652).\n\nI am here to assist charity trustees with:\n- **Scottish Charity Regulator (OSCR) Statutory Reporting** & filing timelines\n- **Receipts & Payments Accounts** classification\n- **Trustees' Annual Report (TAR)** narrative guidance\n- **Independent Examination (IE)** governance obligations\n\nHow may I support your statutory duties today?",
  created_at: new Date().toISOString(),
};

export const ComplianceChatDrawer: React.FC = () => {
  const { token, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentThinking, setCurrentThinking] = useState<string>('');
  const [currentActions, setCurrentActions] = useState<ActionItem[]>([]);
  const [showThinking, setShowThinking] = useState<Record<number, boolean>>({});

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isAutoScrollEnabled = useRef<boolean>(true);

  const fetchChatHistory = useCallback(
    async (beforeTimestamp?: string, offset: number = 0) => {
      try {
        const activeToken =
          token ||
          (typeof window !== 'undefined'
            ? localStorage.getItem('beacon_auth_token')
            : null);
        const headers: Record<string, string> = {};
        if (activeToken) {
          headers['Authorization'] = `Bearer ${activeToken}`;
        }

        const queryParams = new URLSearchParams({
          limit: '50',
          offset: String(offset),
        });
        if (beforeTimestamp) {
          queryParams.append('before_timestamp', beforeTimestamp);
        }

        const res = await fetch(
          `${API_BASE_URL}/api/chat/history?${queryParams.toString()}`,
          {
            headers,
          }
        );

        if (res.ok) {
          const data = await res.json();
          const fetched: ChatTurn[] = data.messages || [];
          setHasMore(data.has_more || false);

          if (offset === 0) {
            if (fetched.length > 0) {
              setMessages(fetched);
            } else {
              setMessages([DEFAULT_WELCOME_MESSAGE]);
            }
          } else {
            setMessages((prev) => [...fetched, ...prev]);
          }
        } else if (offset === 0) {
          setMessages([DEFAULT_WELCOME_MESSAGE]);
        }
      } catch (err) {
        console.error('Failed to load chat history:', err);
        if (offset === 0) {
          setMessages([DEFAULT_WELCOME_MESSAGE]);
        }
      }
    },
    [token]
  );

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      fetchChatHistory();
    }
  }, [isOpen, fetchChatHistory, messages.length]);

  const scrollToBottom = () => {
    if (chatContainerRef.current && isAutoScrollEnabled.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentThinking, currentActions]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } =
      chatContainerRef.current;

    isAutoScrollEnabled.current = scrollHeight - scrollTop - clientHeight < 50;

    if (scrollTop === 0 && hasMore && !loadingMore && messages.length > 0) {
      setLoadingMore(true);
      const oldestTs = messages[0]?.created_at;
      const prevHeight = scrollHeight;

      fetchChatHistory(oldestTs, messages.length).finally(() => {
        setLoadingMore(false);
        setTimeout(() => {
          if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop =
              chatContainerRef.current.scrollHeight - prevHeight;
          }
        }, 50);
      });
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    const userTurn: ChatTurn = {
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userTurn]);
    setLoading(true);
    setCurrentThinking('');
    setCurrentActions([]);
    isAutoScrollEnabled.current = true;

    try {
      const activeToken =
        token ||
        (typeof window !== 'undefined'
          ? localStorage.getItem('beacon_auth_token')
          : null);
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (activeToken) {
        headers['Authorization'] = `Bearer ${activeToken}`;
      }

      const res = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: userText, run_id: 'run_001' }),
      });

      if (!res.ok || !res.body) {
        throw new Error('Failed to start streaming from chat endpoint.');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let streamThinking = '';
      let streamActions: ActionItem[] = [];
      let streamContent = '';

      const partialIndex = messages.length + 1;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const evt of events) {
          if (!evt.trim()) continue;
          const lines = evt.split('\n');
          let eventType = '';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.replace('event: ', '').trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.replace('data: ', '').trim();
            }
          }

          if (dataStr) {
            try {
              const parsed = JSON.parse(dataStr);
              if (eventType === 'thought') {
                streamThinking += parsed.chunk || '';
                setCurrentThinking(streamThinking);
              } else if (eventType === 'action') {
                const actId =
                  parsed.action_id ||
                  parsed.label ||
                  parsed.detail ||
                  `act_${streamActions.length}`;
                const actLabel =
                  parsed.label || parsed.detail || 'Processing...';
                const actStatus = (parsed.status || 'running') as
                  | 'running'
                  | 'completed'
                  | 'failed';

                const existingIdx = streamActions.findIndex(
                  (a) => a.id === actId
                );
                if (existingIdx >= 0) {
                  streamActions = streamActions.map((a, i) =>
                    i === existingIdx
                      ? { ...a, label: actLabel, status: actStatus }
                      : a
                  );
                } else {
                  streamActions = [
                    ...streamActions,
                    { id: actId, label: actLabel, status: actStatus },
                  ];
                }
                setCurrentActions(streamActions);
              } else if (eventType === 'token') {
                streamContent += parsed.chunk || '';
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (
                    lastIdx >= 0 &&
                    updated[lastIdx]?.role === 'assistant' &&
                    lastIdx === partialIndex
                  ) {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      content: streamContent,
                      thinking: streamThinking,
                      actions: streamActions,
                    };
                    return updated;
                  } else {
                    return [
                      ...prev,
                      {
                        role: 'assistant',
                        content: streamContent,
                        thinking: streamThinking,
                        actions: streamActions,
                        created_at: new Date().toISOString(),
                      },
                    ];
                  }
                });
              } else if (eventType === 'done') {
                setCurrentThinking('');
                setCurrentActions([]);
                setShowThinking((prev) => ({ ...prev, [partialIndex]: false }));
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx]?.role === 'assistant') {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      message_id: parsed.message_id,
                      content: parsed.full_message || streamContent,
                      thinking: parsed.thinking || streamThinking,
                      tool_calls: parsed.tool_calls || [],
                      sources: parsed.sources || [],
                      actions: streamActions,
                    };
                    return updated;
                  }
                  return prev;
                });
              }
            } catch (err) {
              console.error('Error parsing SSE packet:', err);
            }
          }
        }
      }
    } catch (err) {
      console.error('Streaming failed, fallback message appended:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Apologies, unable to complete streaming response at this time. Please check your connection and try again.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      setCurrentThinking('');
      setCurrentActions([]);
    }
  };

  const quickPrompts = [
    'What is the OSCR annual return deadline for SC054652?',
    'Explain Receipts & Payments reserve policy under Scottish law',
    'What are the requirements for Independent Examination sign-off?',
  ];

  const toggleThinking = (idx: number) => {
    setShowThinking((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  return (
    <ClientPortal>
      {!isOpen && (
        <motion.button
          onClick={() => setIsOpen(true)}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          aria-label="Open Beacon Statutory Intelligence Agent"
          title="Autonomous OSCR Compliance Sentinel"
          className="tour-chat-advisor fixed bottom-6 right-6 royal-btn-crimson p-2.5 sm:px-4 sm:py-3 rounded-2xl shadow-2xl z-40 flex items-center gap-3 border border-amber-500/40 group transition-all"
        >
          <div className="relative h-10 w-10 flex items-center justify-center shrink-0">
            <img
              src="/assets/logo_mark.png"
              alt="Beacon Sentinel"
              className="h-full w-full object-contain filter drop-shadow-md"
            />
            <span className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full bg-amber-400 border-2 border-red-900 animate-pulse shadow-xs" />
          </div>
          <div className="text-left hidden sm:block">
            <span className="text-xs font-bold font-serif block leading-tight text-white">
              Statutory Intelligence
            </span>
            <span className="text-[10px] text-amber-200 font-mono block leading-none opacity-90">
              OSCR Sentinel
            </span>
          </div>
        </motion.button>
      )}

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs z-50 lg:hidden"
              onClick={() => setIsOpen(false)}
            />

            {/* Slide-out Drawer */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={springs.gentle}
              className="fixed inset-y-0 right-0 w-full max-w-md bg-white dark:bg-[#080C14] border-l border-stone-200 dark:border-slate-800/80 shadow-2xl z-50 flex flex-col justify-between overflow-hidden"
            >
              {/* Header */}
              <div className="p-4 sm:p-5 border-b border-stone-200 dark:border-slate-800/80 flex items-center justify-between bg-stone-50/90 dark:bg-[#0E1626]/95 backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="h-11 w-11 flex items-center justify-center shrink-0 relative">
                    <img
                      src="/assets/logo_mark.png"
                      alt="Potter's House Emblem"
                      className="h-full w-full object-contain drop-shadow-md"
                    />
                    <span className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-white dark:border-[#080C14] shadow-xs" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-1.5">
                      <span>Beacon Statutory Intelligence</span>
                    </h3>
                    <span className="text-[10px] text-amber-700 dark:text-amber-400 font-mono font-semibold flex items-center gap-1">
                      <ShieldCheck className="h-3 w-3" />
                      Scottish Charity Sentinel (SC054652)
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-xl text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-200/60 dark:hover:bg-slate-800 transition-colors"
                  aria-label="Close Advisor"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Chat Body with Infinite Scroll-Up */}
              <div
                ref={chatContainerRef}
                onScroll={handleScroll}
                className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-stone-50/40 dark:bg-[#080C14]"
              >
                {loadingMore && (
                  <div className="text-center py-2">
                    <span className="text-[11px] text-amber-700 dark:text-amber-400 font-mono flex items-center justify-center gap-1.5">
                      <RotateCcw className="h-3 w-3 animate-spin" /> Loading
                      earlier messages...
                    </span>
                  </div>
                )}

                {hasMore && !loadingMore && (
                  <div className="text-center py-1">
                    <button
                      onClick={() =>
                        fetchChatHistory(
                          messages[0]?.created_at,
                          messages.length
                        )
                      }
                      className="text-[10px] text-stone-500 hover:text-amber-700 dark:hover:text-amber-400 underline font-mono"
                    >
                      Load older messages
                    </button>
                  </div>
                )}

                {messages.map((m, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={springs.gentle}
                    className={`flex flex-col ${
                      m.role === 'user' ? 'items-end' : 'items-start'
                    } gap-1.5`}
                  >
                    <div
                      className={`flex gap-2.5 ${
                        m.role === 'user' ? 'justify-end' : 'justify-start'
                      } w-full`}
                    >
                      {m.role === 'assistant' && (
                        <div className="h-7 w-7 shrink-0 mt-0.5 flex items-center justify-center">
                          <img
                            src="/assets/logo_mark.png"
                            alt="Advisor"
                            className="h-full w-full object-contain drop-shadow-xs"
                          />
                        </div>
                      )}
                      <div
                        className={`max-w-[86%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-xs ${
                          m.role === 'user'
                            ? 'royal-btn-crimson text-white font-medium rounded-tr-xs'
                            : 'bg-white dark:bg-[#0E1626] text-slate-800 dark:text-slate-200 border border-stone-200/80 dark:border-slate-800/80 rounded-tl-xs'
                        }`}
                      >
                        {/* Expandable Thinking Process Block */}
                        {m.thinking && (
                          <div className="mb-2.5 border border-stone-200/80 dark:border-slate-800 rounded-xl overflow-hidden bg-stone-50/60 dark:bg-slate-900/60">
                            <button
                              type="button"
                              onClick={() => toggleThinking(idx)}
                              className="w-full px-3 py-1.5 text-[11px] font-mono text-stone-500 hover:text-stone-700 dark:text-slate-400 dark:hover:text-slate-200 font-medium flex items-center justify-between hover:bg-stone-100/60 dark:hover:bg-slate-800/60 transition-colors"
                            >
                              <span className="flex items-center gap-1.5">
                                <Brain className="h-3.5 w-3.5 text-stone-400 dark:text-slate-400" />
                                <span>Thought process</span>
                              </span>
                              {showThinking[idx] ? (
                                <ChevronUp className="h-3.5 w-3.5" />
                              ) : (
                                <ChevronDown className="h-3.5 w-3.5" />
                              )}
                            </button>
                            {showThinking[idx] && (
                              <div className="p-2.5 text-[11px] font-mono text-stone-600 dark:text-slate-400 bg-stone-100/40 dark:bg-[#0A101D] border-t border-stone-200/60 dark:border-slate-800 leading-relaxed whitespace-pre-wrap">
                                {m.thinking}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Actions Executed */}
                        {m.actions && m.actions.length > 0 && (
                          <div className="mb-2 space-y-1">
                            {m.actions.map((act, aIdx) => {
                              const label =
                                typeof act === 'string' ? act : act.label;
                              const status =
                                typeof act === 'string'
                                  ? 'completed'
                                  : act.status;
                              return (
                                <div
                                  key={aIdx}
                                  className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-lg w-fit"
                                >
                                  {status === 'running' ? (
                                    <Loader2 className="h-3 w-3 animate-spin shrink-0 text-emerald-600" />
                                  ) : (
                                    <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-600 dark:text-emerald-400" />
                                  )}
                                  <span>{label}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {m.role === 'assistant' ? (
                          <MarkdownRenderer content={m.content} />
                        ) : (
                          m.content
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Live Real-Time Thought and Action Stream during generation */}
                {loading && (
                  <div className="space-y-2 p-2">
                    {currentThinking && (
                      <div className="p-3 bg-stone-50/80 dark:bg-slate-900/80 border border-stone-200 dark:border-slate-800 rounded-2xl text-[11px] font-mono text-stone-700 dark:text-slate-300 flex items-start gap-2">
                        <Brain className="h-4 w-4 shrink-0 mt-0.5 text-stone-400 dark:text-slate-400 animate-pulse" />
                        <div className="space-y-1 w-full">
                          <span className="font-semibold text-[10px] text-stone-400 dark:text-slate-400 uppercase tracking-wider block">
                            Thinking...
                          </span>
                          <span className="text-stone-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                            {currentThinking}
                          </span>
                        </div>
                      </div>
                    )}
                    {currentActions.length > 0 && (
                      <div className="space-y-1">
                        {currentActions.map((act, i) => (
                          <div
                            key={i}
                            className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-xl w-fit"
                          >
                            {act.status === 'running' ? (
                              <Loader2 className="h-3 w-3 animate-spin shrink-0 text-emerald-600" />
                            ) : (
                              <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-600" />
                            )}
                            <span>{act.label}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Quick Questions & Input Area */}
              <div className="p-3.5 border-t border-stone-200 dark:border-slate-800/80 bg-white dark:bg-[#0E1626] space-y-3">
                {messages.length <= 1 && (
                  <div className="space-y-1.5">
                    <p className="text-[10px] uppercase font-bold text-stone-400 dark:text-slate-400 tracking-wider">
                      Suggested Inquiries:
                    </p>
                    <div className="flex flex-col gap-1">
                      {quickPrompts.map((q, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setInput(q)}
                          className="text-left text-[11px] p-2 rounded-xl bg-stone-100 dark:bg-[#111A2E] hover:bg-amber-500/10 hover:text-amber-700 dark:hover:text-amber-300 border border-stone-200 dark:border-slate-700/80 transition-colors text-slate-700 dark:text-slate-200"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <form onSubmit={sendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about filing deadlines, annual accounts, trustee reports..."
                    className="flex-1 bg-stone-50 dark:bg-[#111A2E] border border-stone-300 dark:border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
                  />
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="royal-btn-crimson px-4 py-2.5 rounded-xl font-bold shadow-xs transition-opacity flex items-center justify-center disabled:opacity-50 active:scale-95"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </ClientPortal>
  );
};
