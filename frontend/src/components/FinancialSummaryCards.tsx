"use client";

import React, { useEffect, useRef } from "react";
import { AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Scale, ShieldCheck, HelpCircle } from "lucide-react";
import { motion, animate } from "framer-motion";
import { cardHoverVariants, motionTokens } from "@/lib/motion-tokens";

interface FinancialSummaryProps {
  grossReceipts: string;
  grossPayments: string;
  netMovement: string;
  reconciled: boolean;
  thresholdBreached: boolean;
}

function AnimatedNumber({ value }: { value: string }) {
  const numericVal = parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0;
  const nodeRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const node = nodeRef.current;
    if (!node) return;

    const controls = animate(0, numericVal, {
      duration: motionTokens.duration.normal,
      ease: motionTokens.easing.smooth,
      onUpdate: (latest) => {
        node.textContent = latest.toLocaleString("en-GB", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
      },
    });

    return () => controls.stop();
  }, [numericVal]);

  return <span ref={nodeRef} className="font-num">{value}</span>;
}

export const FinancialSummaryCards: React.FC<FinancialSummaryProps> = ({
  grossReceipts,
  grossPayments,
  netMovement,
  reconciled,
  thresholdBreached,
}) => {
  return (
    <div className="tour-financial-cards space-y-4">
      {thresholdBreached && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-red-50 dark:bg-red-950/40 border-2 border-red-500 rounded-3xl p-5 sm:p-6 flex items-start gap-4 text-red-800 dark:text-red-200 shadow-md"
        >
          <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-sm sm:text-base font-bold text-red-900 dark:text-red-100 flex items-center gap-2 font-serif">
              <span>Statutory Income Threshold Limit Reached (£250,000)</span>
            </h3>
            <p className="text-xs text-red-700 dark:text-red-300 leading-relaxed">
              Gross income has reached or exceeded £250,000. Simplified Receipts & Payments accounting is halted under Scottish charity regulations. The charity trustees must appoint an independent auditor for full accruals accounting.
            </p>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {/* 1. Gross Receipts (Income) */}
        <motion.div 
          variants={cardHoverVariants}
          initial="initial"
          whileHover="hover"
          whileTap="tap"
          className="royal-card royal-card-gold rounded-3xl p-5 sm:p-6 flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <div>
              <span className="text-slate-800 dark:text-slate-200 uppercase tracking-wider font-bold text-[11px] block">
                Total Receipts (Income)
              </span>
              <span className="text-[10px] text-stone-500 dark:text-slate-400">
                All money received in 2026
              </span>
            </div>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          
          <div className="my-1">
            <div className="text-2xl sm:text-3xl font-bold text-emerald-700 dark:text-emerald-400 flex items-baseline gap-1">
              <span>£</span>
              <AnimatedNumber value={grossReceipts} />
            </div>
          </div>

          <div className="pt-2 border-t border-stone-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-400 font-medium">
            <span>Sunday Tithes & Offerings</span>
            <span className="text-emerald-700 dark:text-emerald-400 font-semibold font-mono text-[10px]">Verified</span>
          </div>
        </motion.div>

        {/* 2. Gross Payments (Expenditure) */}
        <motion.div 
          variants={cardHoverVariants}
          initial="initial"
          whileHover="hover"
          whileTap="tap"
          className="royal-card royal-card-crimson rounded-3xl p-5 sm:p-6 flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <div>
              <span className="text-slate-800 dark:text-slate-200 uppercase tracking-wider font-bold text-[11px] block">
                Total Payments (Expenses)
              </span>
              <span className="text-[10px] text-stone-500 dark:text-slate-400">
                All money spent on operations
              </span>
            </div>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/30">
              <TrendingDown className="h-4 w-4" />
            </div>
          </div>

          <div className="my-1">
            <div className="text-2xl sm:text-3xl font-bold text-rose-700 dark:text-rose-400 flex items-baseline gap-1">
              <span>£</span>
              <AnimatedNumber value={grossPayments} />
            </div>
          </div>

          <div className="pt-2 border-t border-stone-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-400 font-medium">
            <span>Ministry, Rent & Outreach</span>
            <span className="text-rose-700 dark:text-rose-400 font-semibold font-mono text-[10px]">Disbursed</span>
          </div>
        </motion.div>

        {/* 3. Net Annual Movement */}
        <motion.div 
          variants={cardHoverVariants}
          initial="initial"
          whileHover="hover"
          whileTap="tap"
          className="royal-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <div>
              <span className="text-slate-800 dark:text-slate-200 uppercase tracking-wider font-bold text-[11px] block">
                Net Annual Movement
              </span>
              <span className="text-[10px] text-stone-500 dark:text-slate-400">
                Surplus added to reserves
              </span>
            </div>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30">
              <Scale className="h-4 w-4" />
            </div>
          </div>

          <div className="my-1">
            <div className="text-2xl sm:text-3xl font-bold text-amber-800 dark:text-amber-300 flex items-baseline gap-1">
              <span>£</span>
              <AnimatedNumber value={netMovement} />
            </div>
          </div>

          <div className="pt-2 border-t border-stone-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-400 font-medium">
            <span>Carried Forward to 2027</span>
            <span className="text-amber-800 dark:text-amber-300 font-semibold font-mono text-[10px]">Retained</span>
          </div>
        </motion.div>

        {/* 4. Bank Reconciliation & Statutory Status */}
        <motion.div 
          variants={cardHoverVariants}
          initial="initial"
          whileHover="hover"
          whileTap="tap"
          className="royal-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <div>
              <span className="text-slate-800 dark:text-slate-200 uppercase tracking-wider font-bold text-[11px] block">
                Bank Statement Balances
              </span>
              <span className="text-[10px] text-stone-500 dark:text-slate-400">
                Reconciliation & Statutory Limit Check
              </span>
            </div>
            <div className={`p-2 rounded-xl border ${
              reconciled 
                ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30" 
                : "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30"
            }`}>
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>

          <div className="my-1">
            <div className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle2 className={`h-5 w-5 ${reconciled ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600"}`} />
              <span>{reconciled ? "Fully Reconciled" : "Pending Review"}</span>
            </div>
          </div>

          <div className="pt-2 border-t border-stone-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-400 font-medium">
            <span>Under £250k Limit</span>
            <span className="font-mono text-[10px] bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded font-bold">
              Receipts & Payments Eligible
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
