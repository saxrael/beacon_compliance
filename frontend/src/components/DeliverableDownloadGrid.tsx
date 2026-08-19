"use client";

import React, { useState } from "react";
import { API_BASE_URL } from "@/config";
import { Download, FileCheck, Copy, Check, ShieldCheck, Clock, FileText, Award, HelpCircle } from "lucide-react";
import { motion } from "framer-motion";
import { cardHoverVariants } from "@/lib/motion-tokens";

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

  const deliverableMeta: Record<string, {
    fullTitle: string;
    badgeLabel: string;
    subtitle: string;
    description: string;
    statutoryRole: string;
  }> = {
    OAR: {
      fullTitle: "OSCR Online Annual Return (OAR)",
      badgeLabel: "Online Annual Return",
      subtitle: "Official Scottish Charity Questionnaire",
      description: "Statutory online return containing verified charity data, trustee details, and regulatory compliance confirmations required for submission to OSCR.",
      statutoryRole: "Required for all Scottish charities (SCIOs) within 9 months of financial year end.",
    },
    TAR: {
      fullTitle: "Trustees' Annual Report (TAR)",
      badgeLabel: "Trustees' Annual Report",
      subtitle: "Formal Narrative & Activity Review",
      description: "Full statutory narrative documenting the charity's mission, religious activities, Dunbar community outreach, governance management, and reserves policy.",
      statutoryRole: "Statutory report presented to OSCR, trustees, and the public.",
    },
    RP: {
      fullTitle: "Annual Receipts & Payments Accounts",
      badgeLabel: "Receipts & Payments Accounts",
      subtitle: "Statement of Financial Movements & Balances",
      description: "Comprehensive financial statement detailing all money received (receipts) and spent (payments), segregated between General Unrestricted and Building Funds.",
      statutoryRole: "Scottish statutory accounting format for charities with gross income under £250,000.",
    },
    IE: {
      fullTitle: "Independent Examiner's Review Pack (IE)",
      badgeLabel: "Independent Examiner Pack",
      subtitle: "External Scrutiny & Certification File",
      description: "Audit-ready scrutiny documentation, financial reconciliation schedules, and statutory examiner declaration prepared for the independent examiner's review.",
      statutoryRole: "Independent external examination required prior to final OSCR submission.",
    },
  };

  return (
    <div className="tour-deliverables-grid space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-200/80 dark:border-slate-800 pb-3.5">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30">
              <FileCheck className="h-5 w-5" />
            </div>
            <span>Statutory OSCR Annual Filing Packages</span>
          </h2>
          <p className="text-xs text-stone-600 dark:text-slate-400 mt-1">
            The four official legal documents required for Potter&apos;s House Christian Mission UK annual filing to the Scottish Charity Regulator (OSCR).
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-500/30 text-[11px] font-mono font-semibold self-start sm:self-auto">
          <Award className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
          <span>Scottish Charity (SCIO) Compliant</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {deliverables.map((item) => {
          const meta = deliverableMeta[item.type] || {
            fullTitle: `Statutory Package: ${item.type}`,
            badgeLabel: item.type,
            subtitle: "Statutory Compliance Document",
            description: "Official statutory compliance document prepared for Scottish Charity Regulator (OSCR) review.",
            statutoryRole: "Scottish Charity Statutory Requirement.",
          };
          const hash = item.content_hash || "";
          const signed = Boolean(signatures[hash]);

          return (
            <motion.div
              key={item.deliverable_id}
              variants={cardHoverVariants}
              initial="initial"
              whileHover="hover"
              whileTap="tap"
              className="royal-card rounded-3xl p-6 sm:p-7 flex flex-col justify-between space-y-5"
            >
              <div className="space-y-3.5">
                {/* Header row: Badge and Sign-off Status */}
                <div className="flex items-center justify-between gap-2">
                  <span className="bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-amber-300 border border-red-200 dark:border-red-500/30 text-[11px] font-mono px-3 py-0.5 rounded-full font-bold tracking-wide">
                    {meta.badgeLabel}
                  </span>
                  <span
                    className={`text-xs font-semibold px-3 py-0.5 rounded-full flex items-center gap-1.5 ${
                      signed
                        ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30"
                        : "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30"
                    }`}
                  >
                    {signed ? (
                      <>
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>Trustee Approved</span>
                      </>
                    ) : (
                      <>
                        <Clock className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                        <span>Awaiting Signature</span>
                      </>
                    )}
                  </span>
                </div>

                {/* Document Title & Subtitle */}
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 font-serif">
                    <FileText className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    <span>{meta.fullTitle}</span>
                  </h3>
                  <p className="text-xs font-semibold text-amber-800 dark:text-amber-400 mt-0.5">
                    {meta.subtitle}
                  </p>
                  <p className="text-xs text-stone-600 dark:text-slate-400 mt-2 leading-relaxed">
                    {meta.description}
                  </p>
                </div>

                {/* Statutory Role Note */}
                <div className="p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950/60 border border-stone-200/80 dark:border-slate-800/80 text-[11px] text-stone-500 dark:text-slate-400 flex items-start gap-2">
                  <HelpCircle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <span>{meta.statutoryRole}</span>
                </div>

                {/* Verification Seal Fingerprint */}
                <div className="flex items-center justify-between bg-stone-100/60 dark:bg-slate-950 p-2.5 rounded-2xl border border-stone-200 dark:border-slate-800 text-xs font-mono">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="text-[10px] uppercase font-bold text-stone-500 dark:text-slate-500 shrink-0">Document Seal:</span>
                    <span className="truncate text-stone-700 dark:text-amber-300 text-[11px] font-semibold">
                      {hash ? `${hash.substring(0, 24)}...` : "Calculating..."}
                    </span>
                  </div>
                  <button
                    onClick={() => copyHash(hash)}
                    title="Copy document security verification seal"
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

              {/* Action Button */}
              <div className="pt-3.5 border-t border-stone-200/80 dark:border-slate-800">
                {!signed ? (
                  <button
                    onClick={() => onOpenSignoff(hash)}
                    className="w-full royal-btn-gold text-xs font-bold py-3 px-4 rounded-xl transition-all shadow-xs flex items-center justify-center gap-2 active:scale-[0.99]"
                  >
                    <ShieldCheck className="h-4 w-4" />
                    <span>Review & Apply Trustee Signature</span>
                  </button>
                ) : (
                  <a
                    href={`${API_BASE_URL}/api/deliverables/run_001`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full royal-btn-crimson text-xs font-bold py-3 px-4 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download Official Package (Print / PDF)</span>
                  </a>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
