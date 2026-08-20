"use client";

import React, { useState, useEffect, useRef } from "react";
import { Brain, ChevronDown, ChevronUp, Loader2, CheckCircle2, Sparkles } from "lucide-react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

export interface ActionItem {
  id?: string;
  label: string;
  status: "running" | "completed" | "failed";
  detail?: string;
}

interface ThinkingProcessBlockProps {
  isActive?: boolean;
  thinking?: string | null;
  actions?: (ActionItem | string)[];
  durationSeconds?: number | null;
  startTime?: number | null;
  defaultExpanded?: boolean;
  className?: string;
}

const COGNITIVE_VERBS = ["Thinking...", "Mulling...", "Cogitating...", "Pondering..."];

export const ThinkingProcessBlock: React.FC<ThinkingProcessBlockProps> = ({
  isActive = false,
  thinking,
  actions = [],
  durationSeconds,
  startTime,
  defaultExpanded = false,
  className = "",
}) => {
  const prefersReducedMotion = useReducedMotion();
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || isActive);
  const [elapsed, setElapsed] = useState<number>(durationSeconds || 0);
  const [verbIndex, setVerbIndex] = useState<number>(0);
  const startTimestampRef = useRef<number>(startTime || Date.now());

  // Elapsed timer during active streaming
  useEffect(() => {
    if (!isActive) {
      if (durationSeconds !== undefined && durationSeconds !== null) {
        setElapsed(durationSeconds);
      }
      return;
    }

    startTimestampRef.current = startTime || Date.now();
    const interval = setInterval(() => {
      const now = Date.now();
      const diffSec = (now - startTimestampRef.current) / 1000;
      setElapsed(diffSec);
    }, 100);

    return () => clearInterval(interval);
  }, [isActive, startTime, durationSeconds]);

  // Subtle cognitive verb rotation while active
  useEffect(() => {
    if (!isActive) return;

    const verbInterval = setInterval(() => {
      setVerbIndex((prev) => (prev + 1) % COGNITIVE_VERBS.length);
    }, 2800);

    return () => clearInterval(verbInterval);
  }, [isActive]);

  // Auto-expand when active if there are thoughts or actions
  useEffect(() => {
    if (isActive) {
      setIsExpanded(true);
    }
  }, [isActive]);

  const hasContent = Boolean(
    (thinking && thinking.trim().length > 0) || (actions && actions.length > 0)
  );

  const formattedTime = elapsed < 1 ? "1s" : `${elapsed.toFixed(1)}s`;

  // Standardized Action item formatter
  const formattedActions: ActionItem[] = actions.map((act, idx) => {
    if (typeof act === "string") {
      return { id: `act_${idx}`, label: act, status: "completed" };
    }
    return act;
  });

  return (
    <div className={`my-2 select-text ${className}`}>
      {/* Header Pill / Toggle Bar */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        disabled={isActive && !hasContent}
        aria-expanded={isExpanded}
        aria-label={isActive ? "Reasoning in progress" : "Toggle thought process audit trail"}
        className={`group flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono transition-all border text-left ${
          isActive
            ? "bg-amber-500/10 dark:bg-[#0E1626] border-amber-500/30 text-amber-900 dark:text-amber-300 shadow-xs"
            : "bg-stone-100/80 dark:bg-[#0A101D] border-stone-200/80 dark:border-slate-800 text-stone-600 hover:text-stone-900 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-stone-200/60 dark:hover:bg-slate-800/80"
        }`}
      >
        {/* Animated Cognitive Orb or Brain Icon */}
        <div className="relative flex items-center justify-center shrink-0">
          {isActive ? (
            <motion.div
              animate={
                prefersReducedMotion
                  ? {}
                  : {
                      scale: [1, 1.25, 1],
                      opacity: [0.8, 1, 0.8],
                    }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="h-2.5 w-2.5 rounded-full bg-amber-500 dark:bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.6)]"
            />
          ) : (
            <Brain className="h-3.5 w-3.5 text-stone-400 dark:text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors" />
          )}
        </div>

        {/* State Label & Timer */}
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          {isActive ? (
            <span className="font-semibold text-[11px] text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
              <AnimatePresence mode="wait">
                <motion.span
                  key={verbIndex}
                  initial={{ opacity: 0, y: 3 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -3 }}
                  transition={{ duration: 0.2 }}
                  className="inline-block font-sans font-medium"
                >
                  {COGNITIVE_VERBS[verbIndex]}
                </motion.span>
              </AnimatePresence>
              <span className="text-[10px] text-amber-700/70 dark:text-amber-400/70 font-mono font-normal">
                ({formattedTime})
              </span>
            </span>
          ) : (
            <span className="text-[11px] font-medium flex items-center gap-1.5">
              <span>Thought for {formattedTime}</span>
              {formattedActions.length > 0 && (
                <span className="text-[10px] text-stone-400 dark:text-slate-500 font-normal">
                  • {formattedActions.length} statutory {formattedActions.length === 1 ? "action" : "actions"}
                </span>
              )}
            </span>
          )}
        </div>

        {/* Expand / Collapse Chevron */}
        {(hasContent || !isActive) && (
          <div className="shrink-0 text-stone-400 dark:text-slate-500 group-hover:text-stone-600 dark:group-hover:text-slate-300 transition-colors">
            {isExpanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </div>
        )}
      </button>

      {/* Expandable Reasoning & Actions Body */}
      <AnimatePresence initial={false}>
        {isExpanded && hasContent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={springs.gentle}
            className="overflow-hidden mt-1.5 rounded-xl border border-stone-200/80 dark:border-slate-800/90 bg-stone-50/90 dark:bg-[#070B12] shadow-inner text-xs"
          >
            <div className="p-3 space-y-2.5">
              {/* Real-time Executed Action Chips */}
              {formattedActions.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] uppercase font-bold tracking-wider text-stone-400 dark:text-slate-500 flex items-center gap-1">
                    <Sparkles className="h-3 w-3 text-amber-500" />
                    <span>Statutory Audit Actions</span>
                  </div>
                  <div className="flex flex-col gap-1">
                    {formattedActions.map((act, i) => (
                      <motion.div
                        key={act.id || i}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={springs.gentle}
                        className={`flex items-center gap-2 px-2.5 py-1 rounded-lg text-[11px] font-mono border ${
                          act.status === "running"
                            ? "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-300"
                            : act.status === "failed"
                            ? "bg-red-500/10 border-red-500/30 text-red-700 dark:text-red-300"
                            : "bg-emerald-500/10 border-emerald-500/20 text-emerald-800 dark:text-emerald-300"
                        }`}
                      >
                        {act.status === "running" ? (
                          <Loader2 className="h-3 w-3 animate-spin shrink-0 text-amber-600 dark:text-amber-400" />
                        ) : act.status === "failed" ? (
                          <span className="h-2 w-2 rounded-full bg-red-500 shrink-0" />
                        ) : (
                          <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-600 dark:text-emerald-400" />
                        )}
                        <span className="font-medium truncate">{act.label}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Streamed or Persisted Thoughts */}
              {thinking && thinking.trim().length > 0 && (
                <div className="space-y-1">
                  <div className="text-[10px] uppercase font-bold tracking-wider text-stone-400 dark:text-slate-500 flex items-center gap-1">
                    <Brain className="h-3 w-3 text-stone-400 dark:text-slate-400" />
                    <span>Chain of Thought</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-stone-100/70 dark:bg-[#0A101D] border border-stone-200/60 dark:border-slate-800/80 font-mono text-[11px] text-stone-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto select-text">
                    {thinking}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
