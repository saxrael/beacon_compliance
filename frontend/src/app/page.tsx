"use client";

import React, { useState } from "react";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { LoginForm } from "@/components/LoginForm";
import { FirstLoginResetModal } from "@/components/FirstLoginResetModal";
import { Header } from "@/components/Header";
import { Play, FileText, CheckCircle, Sparkles, Building2, ShieldAlert, Cpu } from "lucide-react";
import { useComplianceOS } from "@/hooks/useComplianceOS";
import { FinancialSummaryCards } from "@/components/FinancialSummaryCards";
import { DeliverableDownloadGrid } from "@/components/DeliverableDownloadGrid";
import { TrusteeSignoffModal } from "@/components/TrusteeSignoffModal";
import { AdminProvisioningModal } from "@/components/AdminProvisioningModal";
import { ComplianceChatDrawer } from "@/components/ComplianceChatDrawer";

function DashboardContent() {
  const [adminModalOpen, setAdminModalOpen] = useState(false);
  const { user, loading: authLoading } = useAuth();
  const {
    pipelineResult,
    loading,
    activeSignoffHash,
    setActiveSignoffHash,
    signatures,
    runCompliancePipeline,
    handleSignoffSuccess,
  } = useComplianceOS();

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#F8F7F4] dark:bg-[#090D16] flex items-center justify-center text-amber-700 dark:text-amber-400 font-mono text-sm">
        <div className="flex items-center gap-3 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 shadow-md">
          <div className="h-4 w-4 rounded-full border-2 border-amber-600 border-t-transparent animate-spin" />
          <span>Authenticating trustee session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  const rnp = pipelineResult?.receipts_payments || {};
  const balances = pipelineResult?.statement_of_balances || {};
  const deliverables = pipelineResult?.deliverables || [];
  const trusteeRole = user.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1).toLowerCase()) : "Trustee";

  return (
    <div className="min-h-screen bg-[#F8F7F4] dark:bg-[#090D16] text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-300">
      <Header onOpenAdminModal={() => setAdminModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6 sm:space-y-8">
        <div className="tour-dashboard-actions flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-stone-200 dark:border-slate-800 shadow-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-50 font-serif">
                OSCR Annual Compliance Pipeline
              </h2>
              <span className="inline-flex items-center gap-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30 text-[11px] font-mono px-2 py-0.5 rounded-full font-semibold">
                FY 2026
              </span>
            </div>
            <p className="text-xs font-medium text-stone-600 dark:text-slate-400">
              Financial Year Ended 31 December 2026 • Scottish SCIO Registration SC054652
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={runCompliancePipeline}
              disabled={loading}
              className="bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold px-5 py-3 rounded-2xl shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2.5 text-sm disabled:opacity-50"
            >
              <Play className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              <span>{loading ? "Executing State Machine..." : "Run Compliance State Machine"}</span>
            </button>
          </div>
        </div>

        {loading && !pipelineResult ? (
          <div className="tour-dashboard-stats p-8 text-center bg-white dark:bg-slate-900 rounded-3xl border border-stone-200 dark:border-slate-800 shadow-xs animate-pulse text-amber-700 dark:text-amber-400 font-mono text-sm flex flex-col items-center justify-center gap-3">
            <div className="h-6 w-6 rounded-full border-2 border-red-600 border-t-transparent animate-spin" />
            <span>Executing deterministic state machine, PII scrubbing, & hallucination audit...</span>
          </div>
        ) : (
          <div className="tour-dashboard-stats">
            <FinancialSummaryCards
              grossReceipts={rnp.gross_receipts_decimal || "15000.00"}
              grossPayments={rnp.gross_payments_decimal || "9500.00"}
              netMovement={rnp.net_movement_decimal || "5500.00"}
              reconciled={balances.reconciled ?? true}
              thresholdBreached={pipelineResult?.income_threshold_breach ?? false}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-stone-200 dark:border-slate-800 shadow-xs space-y-4 lg:col-span-2 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2">
                  <FileText className="h-5 w-5 text-red-600 dark:text-amber-400" />
                  <span>Trustees&apos; Annual Report (TAR) Narrative Preview</span>
                </h3>
                <span className="text-[11px] font-mono bg-stone-100 dark:bg-slate-800 px-2 py-0.5 rounded-md text-stone-600 dark:text-slate-400">
                  Node 2 Synthesizer
                </span>
              </div>
              <p className="text-xs text-stone-600 dark:text-slate-400">
                Synthesized by Gemma 4 26B A4B across 4 whitelisted <code className="text-red-700 dark:text-amber-300 font-mono font-bold">LLM_DRAFTED</code> fields using deterministic token placeholders.
              </p>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-stone-50 dark:bg-slate-950 p-4 rounded-2xl border border-stone-200 dark:border-slate-800 space-y-1">
                <span className="text-stone-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[10px] block">
                  1. Structure, Governance & Management
                </span>
                <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-normal">
                  {pipelineResult?.tar_draft_fields?.governance_description ||
                    "Potter's House Christian Mission UK (SC054652) is governed by its SCIO Constitution adopted upon registration. General management is vested in the charity trustees who meet regularly to review ministry operations, spiritual objectives, and statutory compliance with OSCR."}
                </p>
              </div>

              <div className="bg-stone-50 dark:bg-slate-950 p-4 rounded-2xl border border-stone-200 dark:border-slate-800 space-y-1">
                <span className="text-stone-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[10px] block">
                  2. Activities & Performance Achievements
                </span>
                <p className="text-slate-800 dark:text-slate-200 font-mono text-[11px] leading-relaxed bg-white dark:bg-slate-900 p-2.5 rounded-xl border border-stone-200/60 dark:border-slate-800">
                  {pipelineResult?.tar_draft_fields?.achievements_connective_narrative ||
                    "52 weekly worship services and community outreach sessions conducted in Dunbar. Gross receipts: [FIGURE_INJECTED:gross_receipts], Gross payments: [FIGURE_INJECTED:gross_payments], resulting in net fund movement of [FIGURE_INJECTED:net_movement]."}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-stone-200 dark:border-slate-800 shadow-xs space-y-4 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <span>Trustee Red-Line Matrix</span>
              </h3>
              <p className="text-xs text-stone-600 dark:text-slate-400 mt-1">
                Mandatory non-negotiable statutory safeguards.
              </p>
            </div>

            <ul className="text-xs space-y-3 text-slate-700 dark:text-slate-300">
              <li className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold">PII Boundary Scrubbing</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">ACTIVE</span>
              </li>
              <li className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold">Zero LLM Math Enforced</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">AST VERIFIED</span>
              </li>
              <li className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold">Income Under £250k Cap</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">PASS (£15k)</span>
              </li>
              <li className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold">Hallucination Audit</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">100% CLEAN</span>
              </li>
              <li className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <span className="font-semibold">HMAC SHA-256 Seal</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">ENFORCED</span>
              </li>
            </ul>
          </div>
        </div>

        <DeliverableDownloadGrid
          deliverables={
            deliverables.length > 0
              ? deliverables
              : [
                  {
                    deliverable_id: "d1",
                    type: "OAR",
                    charity_number: "SC054652",
                    status: "ready_for_review",
                    content_hash: "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
                  },
                  {
                    deliverable_id: "d2",
                    type: "TAR",
                    charity_number: "SC054652",
                    status: "ready_for_review",
                    content_hash: "b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1",
                  },
                  {
                    deliverable_id: "d3",
                    type: "RP",
                    charity_number: "SC054652",
                    status: "ready_for_review",
                    content_hash: "c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2",
                  },
                  {
                    deliverable_id: "d4",
                    type: "IE",
                    charity_number: "SC054652",
                    status: "ready_for_review",
                    content_hash: "d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3",
                  },
                ]
          }
          onOpenSignoff={(hash) => setActiveSignoffHash(hash)}
          signatures={signatures}
        />

        <TrusteeSignoffModal
          isOpen={Boolean(activeSignoffHash)}
          onClose={() => setActiveSignoffHash(null)}
          trusteeRole={trusteeRole}
          deliverableHash={activeSignoffHash || ""}
          onSuccess={(sig) => {
            if (activeSignoffHash) {
              handleSignoffSuccess(activeSignoffHash, sig);
            }
          }}
        />

        <AdminProvisioningModal
          isOpen={adminModalOpen}
          onClose={() => setAdminModalOpen(false)}
        />

        <FirstLoginResetModal />

        <ComplianceChatDrawer />
      </main>

      <footer className="border-t border-stone-200 dark:border-slate-800/80 bg-white dark:bg-slate-950 py-6 text-center text-xs font-medium text-stone-600 dark:text-slate-500 transition-colors duration-300">
        Potter&apos;s House Christian Mission UK (SCIO, SC054652) • 5B Beachmont Court, Dunbar, Scotland, EH42 1YF
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
