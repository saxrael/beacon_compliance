"use client";

import React, { useState } from "react";
import { Send, X, Sparkles, Scale, BookOpen, ShieldCheck, Landmark } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { API_BASE_URL } from "@/config";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

export const ComplianceChatDrawer: React.FC = () => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: "assistant",
      content:
        "Welcome to the **Beacon Compliance Advisor** for Potter's House Christian Mission UK (SC054652).\n\nI am here to assist the charity trustees with:\n- **Scottish Charity Regulator (OSCR) Statutory Reporting** & filing timelines\n- **Receipts & Payments Accounts** classification\n- **Trustees' Annual Report (TAR)** narrative guidance\n- **Independent Examination (IE)** governance obligations\n\nHow may I support your statutory duties today?",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setLoading(true);

    try {
      const activeToken = token || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null);
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (activeToken) {
        headers["Authorization"] = `Bearer ${activeToken}`;
      }

      const res = await fetch(`${API_BASE_URL}/api/chat/message`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: userText, run_id: "run_001" }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Apologies, unable to process compliance query at this time. Please try again shortly." },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Unable to connect to the Compliance Advisor. Please check your connection and try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "What is the OSCR annual return deadline?",
    "Explain Receipts & Payments reserve policy",
    "What is required for Independent Examination?",
  ];

  return (
    <>
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
          className="fixed bottom-6 right-6 royal-btn-crimson p-2.5 sm:px-4 sm:py-3 rounded-2xl shadow-2xl z-40 flex items-center gap-3 border border-amber-500/40 group transition-all"
        >
          <div className="relative h-9 w-9 rounded-xl bg-slate-950/40 border border-amber-400/40 p-1 flex items-center justify-center shrink-0">
            <img
              src="/assets/logo_mark.png"
              alt="Beacon Sentinel"
              className="h-full w-full object-contain filter drop-shadow-xs"
            />
            <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-amber-400 border-2 border-red-900 animate-pulse" />
          </div>
          <div className="text-left hidden sm:block">
            <span className="text-xs font-bold font-serif block leading-tight text-white">Statutory Intelligence</span>
            <span className="text-[10px] text-amber-200 font-mono block leading-none opacity-90">OSCR Sentinel</span>
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
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={springs.gentle}
              className="fixed inset-y-0 right-0 w-full max-w-md bg-white dark:bg-[#0B0F19] border-l border-stone-200 dark:border-slate-800 shadow-2xl z-50 flex flex-col justify-between overflow-hidden"
            >
              {/* Header */}
              <div className="p-4 sm:p-5 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between bg-stone-50/80 dark:bg-slate-900/60 backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="h-11 w-11 rounded-2xl bg-stone-100 dark:bg-slate-950 border border-amber-500/40 p-1.5 flex items-center justify-center shadow-xs shrink-0 relative">
                    <img
                      src="/assets/logo_mark.png"
                      alt="Potter's House Emblem"
                      className="h-full w-full object-contain"
                    />
                    <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-950" />
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

              {/* Chat Body */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-stone-50/30 dark:bg-slate-950/30">
                {messages.map((m, idx) => (
                  <motion.div 
                    key={idx} 
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={springs.gentle}
                    className={`flex gap-2.5 ${m.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {m.role === "assistant" && (
                      <div className="h-7 w-7 rounded-lg bg-stone-100 dark:bg-slate-900 border border-stone-300/80 dark:border-slate-700 p-0.5 shrink-0 mt-0.5 flex items-center justify-center">
                        <img
                          src="/assets/logo_mark.png"
                          alt="Advisor"
                          className="h-full w-full object-contain"
                        />
                      </div>
                    )}
                    <div
                      className={`max-w-[84%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-xs ${
                        m.role === "user"
                          ? "royal-btn-crimson text-white font-medium rounded-tr-xs"
                          : "bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-stone-200/80 dark:border-slate-800 rounded-tl-xs"
                      }`}
                    >
                      {m.role === "assistant" ? (
                        <MarkdownRenderer content={m.content} />
                      ) : (
                        m.content
                      )}
                    </div>
                  </motion.div>
                ))}
                {loading && (
                  <div className="text-xs text-amber-800 dark:text-amber-400 italic flex items-center gap-2 p-2">
                    <span className="h-2 w-2 rounded-full bg-amber-600 animate-pulse" />
                    <span>Searching Scottish charity regulatory guidance...</span>
                  </div>
                )}
              </div>

              {/* Quick Questions & Input Area */}
              <div className="p-3.5 border-t border-stone-200 dark:border-slate-800 bg-white dark:bg-[#0B0F19] space-y-3">
                {messages.length === 1 && (
                  <div className="space-y-1.5">
                    <p className="text-[10px] uppercase font-bold text-stone-400 dark:text-slate-500 tracking-wider">Suggested Inquiries:</p>
                    <div className="flex flex-col gap-1">
                      {quickPrompts.map((q, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setInput(q)}
                          className="text-left text-[11px] p-2 rounded-xl bg-stone-100 dark:bg-slate-900 hover:bg-amber-500/10 hover:text-amber-700 dark:hover:text-amber-400 border border-stone-200 dark:border-slate-800 transition-colors text-slate-700 dark:text-slate-300"
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
                    className="flex-1 bg-stone-50 dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
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
    </>
  );
};
