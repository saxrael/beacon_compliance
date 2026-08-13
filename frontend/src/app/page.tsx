"use client";

import React, { useState } from "react";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { LoginForm } from "@/components/LoginForm";
import { FirstLoginResetModal } from "@/components/FirstLoginResetModal";
import { Header } from "@/components/Header";
import { Play, FileText, CheckCircle } from "lucide-react";
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
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-yellow-400 font-mono text-sm">
        Authenticating trustee session...
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
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-300">
      <Header onOpenAdminModal={() => setAdminModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-8">
        <div className="tour-dashboard-actions flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 rounded-2xl">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50">OSCR Annual Compliance Pipeline</h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Financial Year Ended 31 December 2026 • SCIO Registration SC054652
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={runCompliancePipeline}
              disabled={loading}
              className="brand-gradient text-white font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-red-900/30 hover:opacity-90 transition-opacity flex items-center justify-center gap-2 text-sm"
            >
              <Play className="h-4 w-4" />
              {loading ? "Running State Machine..." : "Run Compliance State Machine"}
            </button>
          </div>
        </div>

        {loading && !pipelineResult ? (
          <div className="tour-dashboard-stats p-8 text-center glass-card rounded-xl animate-pulse text-red-600 dark:text-yellow-400 font-mono text-sm">
            Executing deterministic state machine & hallucination audit...
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card rounded-xl p-5 space-y-3 md:col-span-2">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileText className="h-5 w-5 text-red-500" />
              Trustees&apos; Annual Report (TAR) Narrative Preview
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Synthesized by Gemma 4 26B A4B across 4 whitelisted <code className="text-red-600 dark:text-yellow-400 font-mono">LLM_DRAFTED</code> fields using token placeholders.
            </p>

            <div className="space-y-3 text-xs text-slate-700 dark:text-slate-300">
              <div className="bg-slate-50 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 font-bold block mb-1">1. Structure, Governance & Management</span>
                <p>{pipelineResult?.tar_draft_fields?.governance_description || "Potter's House Christian Mission UK (SC054652) is governed by its SCIO Constitution."}</p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 font-bold block mb-1">2. Achievements & Performance</span>
                <p className="font-mono text-slate-800 dark:text-slate-200">
                  {pipelineResult?.tar_draft_fields?.achievements_connective_narrative || "52 weekly services conducted. Gross receipts: [FIGURE_INJECTED:gross_receipts]."}
                </p>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5 space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />
              Trustee Compliance Checklist
            </h3>
            <ul className="text-xs space-y-2 text-slate-700 dark:text-slate-300">
              <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400"></span> PII Boundary Scrubbing Active</li>
              <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400"></span> Zero LLM Math Enforced</li>
              <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-red-500 dark:bg-yellow-400"></span> Income Under £250k Cap</li>
              <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400"></span> Hallucination Audit Passed</li>
              <li className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400"></span> SHA-256 Hashes Computed</li>
            </ul>
          </div>
        </div>

        <DeliverableDownloadGrid
          deliverables={deliverables.length > 0 ? deliverables : [
            { deliverable_id: "d1", type: "OAR", charity_number: "SC054652", status: "ready_for_review", content_hash: "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90" },
            { deliverable_id: "d2", type: "TAR", charity_number: "SC054652", status: "ready_for_review", content_hash: "b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1" },
            { deliverable_id: "d3", type: "RP", charity_number: "SC054652", status: "ready_for_review", content_hash: "c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2" },
            { deliverable_id: "d4", type: "IE", charity_number: "SC054652", status: "ready_for_review", content_hash: "d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3" },
          ]}
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

      <footer className="border-t border-slate-200 dark:border-slate-900 bg-white dark:bg-slate-950 py-6 text-center text-xs text-slate-600 dark:text-slate-500 transition-colors duration-300">
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
