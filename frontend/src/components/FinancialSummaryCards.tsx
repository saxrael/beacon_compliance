"use client";

import React from "react";
import { AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Scale, ShieldCheck } from "lucide-react";

interface FinancialSummaryProps {
  grossReceipts: string;
  grossPayments: string;
  netMovement: string;
  reconciled: boolean;
  thresholdBreached: boolean;
}

export const FinancialSummaryCards: React.FC<FinancialSummaryProps> = ({
  grossReceipts,
  grossPayments,
  netMovement,
  reconciled,
  thresholdBreached,
}) => {
  return (
    <div className="space-y-4">
      {thresholdBreached && (
        <div className="bg-red-50 dark:bg-red-950/40 border-2 border-red-500 rounded-2xl p-5 flex items-start gap-4 text-red-800 dark:text-red-200 shadow-md">
          <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-sm sm:text-base font-bold text-red-900 dark:text-red-100 flex items-center gap-2">
              <span>Red-Line 5 Income Threshold Hard-Halt Triggered</span>
            </h3>
            <p className="text-xs text-red-700 dark:text-red-300 leading-relaxed">
              Gross income reached or exceeded £250,000. Receipts & Payments accounting generation is halted per OSCR statutory regulations.
              The charity must engage a fully audited accruals accounting route.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-stone-200 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <span>Gross Receipts</span>
            <div className="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-emerald-700 dark:text-emerald-400">
            £{grossReceipts}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-500 font-medium">
            <span>Deterministic Node 3 Total</span>
            <span className="font-mono text-[10px] text-emerald-600 dark:text-emerald-500">Verified</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-stone-200 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <span>Gross Payments</span>
            <div className="p-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-500/30">
              <TrendingDown className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-rose-700 dark:text-rose-400">
            £{grossPayments}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-500 font-medium">
            <span>Deterministic Node 3 Total</span>
            <span className="font-mono text-[10px] text-rose-600 dark:text-rose-500">Disbursed</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-stone-200 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <span>Net Surplus / (Deficit)</span>
            <div className="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30">
              <Scale className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-amber-700 dark:text-amber-400">
            £{netMovement}
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-500 font-medium">
            <span>Fund Net Movement</span>
            <span className="font-mono text-[10px] text-amber-600 dark:text-amber-500">Reconciled</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-stone-200 dark:border-slate-800 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-stone-600 dark:text-slate-400 text-xs font-semibold">
            <span>Bank Statement Status</span>
            <div className={`p-1.5 rounded-lg border ${reconciled ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30" : "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-500/30"}`}>
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <CheckCircle2 className={`h-5 w-5 ${reconciled ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`} />
            <span>{reconciled ? "Reconciled" : "Pending Match"}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-[11px] text-stone-500 dark:text-slate-500 font-medium">
            <span>Statement of Balances</span>
            <span className="font-mono text-[10px]">SCIO Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
