"use client";

import React, { useState } from "react";
import { MessageSquare, Send, X, Bot, Sparkles } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { API_BASE_URL } from "@/config";
import { useAuth } from "@/context/AuthContext";

export const ComplianceChatDrawer: React.FC = () => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: "assistant",
      content:
        "Hello! I am your **Gemma 4 26B Compliance Assistant** for Potter's House Christian Mission UK (SC054652).\n\nHow can I assist with OSCR governance rules, Receipts & Payments accounting, or narrative review?",
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
          { role: "assistant", content: "Apologies, unable to process compliance query at this time." },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Network error contacting compliance assistant endpoint." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          aria-label="Open compliance chat assistant"
          title="OSCR Compliance Assistant"
          className="fixed bottom-6 right-6 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white p-4 rounded-2xl shadow-xl hover:scale-105 active:scale-95 transition-all z-50 flex items-center justify-center border border-red-500/40"
        >
          <MessageSquare className="h-6 w-6" />
        </button>
      )}

      {isOpen && (
        <div className="fixed inset-y-0 right-0 w-full max-w-md bg-white dark:bg-slate-900 border-l border-stone-200 dark:border-slate-800 shadow-2xl z-50 flex flex-col transition-colors duration-300">
          <div className="p-4 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between bg-stone-50/80 dark:bg-slate-950/80 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 flex items-center justify-center text-red-600 dark:text-red-400">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 font-serif">
                  <span>OSCR Compliance Assistant</span>
                </h3>
                <span className="text-[10px] text-amber-700 dark:text-amber-400 font-mono font-medium flex items-center gap-1">
                  <Sparkles className="h-2.5 w-2.5" />
                  Gemma 4 26B A4B • Zero LLM Math
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-stone-50/40 dark:bg-slate-900/40">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-xs ${
                    m.role === "user"
                      ? "bg-red-600 text-white font-medium rounded-tr-xs"
                      : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-stone-200 dark:border-slate-700/60 rounded-tl-xs"
                  }`}
                >
                  {m.role === "assistant" ? (
                    <MarkdownRenderer content={m.content} />
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-xs text-stone-500 dark:text-slate-400 italic flex items-center gap-2 p-2">
                <span className="h-2 w-2 rounded-full bg-red-600 animate-pulse" />
                <span>Assistant retrieving guidance from knowledge base...</span>
              </div>
            )}
          </div>

          <form onSubmit={sendMessage} className="p-3.5 border-t border-stone-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about OSCR reporting, R&P rules..."
              className="flex-1 bg-stone-50 dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-500/20 shadow-xs"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-red-600 hover:bg-red-700 text-white px-3.5 py-2 rounded-xl font-bold shadow-xs transition-opacity flex items-center justify-center disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
};
