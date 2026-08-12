"use client";

import React from "react";
import { AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Scale } from "lucide-react";

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
        <div className="bg-red-500/10 border-2 border-red-500/60 rounded-xl p-4 flex items-start gap-4 text-red-300 shadow-xl">
          <AlertTriangle className="h-6 w-6 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-base font-bold text-red-200">Red-Line 5 Income Threshold Hard-Halt Triggered</h3>
            <p className="text-xs text-red-300/90 mt-1 leading-relaxed">
              Gross income reached or exceeded £250,000. Receipts & Payments accounting generation is halted per OSCR regulations.
              The charity must engage a fully audited accounting route.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-xl p-5 border border-slate-700/60">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Gross Receipts</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-emerald-400">£{grossReceipts}</div>
          <span className="text-[10px] text-slate-500 mt-1 block">Deterministic Node 3 Total</span>
        </div>

        <div className="glass-card rounded-xl p-5 border border-slate-700/60">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Gross Payments</span>
            <TrendingDown className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-rose-400">£{grossPayments}</div>
          <span className="text-[10px] text-slate-500 mt-1 block">Deterministic Node 3 Total</span>
        </div>

        <div className="glass-card rounded-xl p-5 border border-slate-700/60">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Net Surplus / (Deficit)</span>
            <Scale className="h-4 w-4 text-yellow-400" />
          </div>
          <div className="mt-3 text-2xl font-bold font-mono text-yellow-400">£{netMovement}</div>
          <span className="text-[10px] text-slate-500 mt-1 block">Fund Net Movement</span>
        </div>

        <div className="glass-card rounded-xl p-5 border border-slate-700/60">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Bank Statement Status</span>
            <CheckCircle2 className={`h-4 w-4 ${reconciled ? "text-emerald-400" : "text-amber-400"}`} />
          </div>
          <div className="mt-3 text-lg font-semibold text-slate-100">
            {reconciled ? "Reconciled" : "Pending Reconciliation"}
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">Statement of Balances</span>
        </div>
      </div>
    </div>
  );
};
