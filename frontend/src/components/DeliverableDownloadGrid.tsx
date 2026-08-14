"use client";

import React, { useState } from "react";
import { API_BASE_URL } from "@/config";
import { Download, FileCheck, Copy, Check, ShieldCheck, Clock, FileText } from "lucide-react";

interface DeliverableItem {
  deliverable_id: string;
  type: string;
  charity_number: string;
  status: string;
  content_hash?: string;
}

interface DeliverableGridProps {
  deliverables: DeliverableItem[];
  onOpenSignoff: (hash: string) => void;
  signatures: Record<string, string>;
}

export const DeliverableDownloadGrid: React.FC<DeliverableGridProps> = ({
  deliverables,
  onOpenSignoff,
  signatures,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyHash = (hash?: string) => {
    if (!hash) return;
    navigator.clipboard.writeText(hash);
    setCopiedId(hash);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const titles: Record<string, string> = {
    OAR: "Deliverable 1: OSCR Online Annual Return (OAR) Sheet",
    TAR: "Deliverable 2: Trustees' Annual Report (TAR)",
    RP: "Deliverable 3: Annual Receipts & Payments Accounts",
    IE: "Deliverable 4: Independent Examiner (IE) Review Pack",
  };

  const descriptions: Record<string, string> = {
    OAR: "Statutory online return questionnaire and compliance confirmation fields.",
    TAR: "Full narrative report of charity objectives, governance, and annual achievements.",
    RP: "Receipts and payments schedule, statement of balances, and fund notes.",
    IE: "Independent examiner documentation, appointment record, and scrutiny pack.",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-red-600 dark:text-amber-400" />
            <span>Compiled OSCR Deliverables</span>
          </h2>
          <p className="text-xs text-stone-600 dark:text-slate-400 mt-0.5">
            Cryptographically sealed packages with SHA-256 content hashes requiring HMAC trustee sign-off.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {deliverables.map((item) => {
          const title = titles[item.type] || item.type;
          const desc = descriptions[item.type] || "Statutory compliance deliverable.";
          const hash = item.content_hash || "";
          const signed = Boolean(signatures[hash]);

          return (
            <div
              key={item.deliverable_id}
              className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-stone-200 dark:border-slate-800 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-amber-300 border border-red-200 dark:border-red-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-md uppercase font-bold tracking-wider">
                    {item.type} Package
                  </span>
                  <span
                    className={`text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1.5 ${
                      signed
                        ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30"
                        : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30"
                    }`}
                  >
                    {signed ? (
                      <>
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>Trustee Signed</span>
                      </>
                    ) : (
                      <>
                        <Clock className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                        <span>Pending Sign-off</span>
                      </>
                    )}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                    <FileText className="h-4 w-4 text-stone-400 shrink-0" />
                    <span>{title}</span>
                  </h3>
                  <p className="text-xs text-stone-600 dark:text-slate-400 mt-1 leading-relaxed">
                    {desc}
                  </p>
                </div>

                <div className="flex items-center justify-between bg-stone-50 dark:bg-slate-950 p-2.5 rounded-xl border border-stone-200 dark:border-slate-800 text-xs font-mono">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="text-[10px] uppercase font-bold text-stone-500 dark:text-slate-500 shrink-0">SHA-256:</span>
                    <span className="truncate text-stone-700 dark:text-amber-300 text-[11px]">
                      {hash ? `${hash.substring(0, 20)}...` : "Calculating..."}
                    </span>
                  </div>
                  <button
                    onClick={() => copyHash(hash)}
                    title="Copy full cryptographic hash"
                    className="p-1 rounded-md text-stone-500 hover:text-stone-900 dark:hover:text-amber-300 hover:bg-stone-200 dark:hover:bg-slate-800 transition-colors"
                  >
                    {copiedId === hash ? (
                      <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 dark:border-slate-800">
                {!signed ? (
                  <button
                    onClick={() => onOpenSignoff(hash)}
                    className="w-full bg-stone-900 hover:bg-stone-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-amber-300 dark:text-amber-400 border border-stone-800 dark:border-slate-700 text-xs font-bold py-2.5 px-4 rounded-xl transition-all shadow-xs flex items-center justify-center gap-2 active:scale-[0.99]"
                  >
                    <ShieldCheck className="h-4 w-4" />
                    <span>Sign Off Deliverable</span>
                  </button>
                ) : (
                  <a
                    href={`${API_BASE_URL}/api/deliverables/run_001`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full bg-red-600 hover:bg-red-700 active:bg-red-800 text-white text-xs font-bold py-2.5 px-4 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download Signed Package</span>
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
