"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { LoginForm } from "@/components/LoginForm";
import { FirstLoginResetModal } from "@/components/FirstLoginResetModal";
import { Header } from "@/components/Header";
import { Play, Sparkles, Award, ShieldCheck, FileCheck } from "lucide-react";
import { useComplianceOS } from "@/hooks/useComplianceOS";
import { FinancialSummaryCards } from "@/components/FinancialSummaryCards";
import { UploadIngestCenter } from "@/components/UploadIngestCenter";
import { DeliverableDownloadGrid } from "@/components/DeliverableDownloadGrid";
import { TrusteeSignoffModal } from "@/components/TrusteeSignoffModal";
import { AdminProvisioningModal } from "@/components/AdminProvisioningModal";
import { ComplianceChatDrawer } from "@/components/ComplianceChatDrawer";
import { motion } from "framer-motion";
import { containerStaggerVariants, itemFadeUpVariants } from "@/lib/motion-tokens";

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
      <div className="min-h-screen bg-[#FBF9F5] dark:bg-[#070A11] flex items-center justify-center text-amber-800 dark:text-amber-400 font-mono text-sm">
        <div className="flex items-center gap-3 p-6 rounded-3xl bg-white dark:bg-[#0E1524] border border-stone-200 dark:border-slate-800 shadow-xl">
          <div className="h-5 w-5 rounded-full border-2 border-amber-600 border-t-transparent animate-spin" />
          <span className="font-serif">Verifying trustee access...</span>
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
    <div className="min-h-screen bg-[#FBF9F5] dark:bg-[#070A11] text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-300">
      <Header onOpenAdminModal={() => setAdminModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6 sm:space-y-8">
        <motion.div
          variants={containerStaggerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-6 sm:space-y-8"
        >
          {/* 1. Executive Filing Hero Banner */}
          <motion.div 
            variants={itemFadeUpVariants}
            className="tour-pipeline-runner flex flex-col md:flex-row md:items-center justify-between gap-5 bg-white dark:bg-[#0E1524] p-6 sm:p-7 rounded-3xl border border-stone-200/90 dark:border-slate-800/80 shadow-xs royal-card"
          >
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-50 font-serif">
                  Annual Statutory Compliance & Filing
                </h2>
                <span className="inline-flex items-center gap-1 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-500/30 text-[11px] font-mono px-3 py-0.5 rounded-full font-bold">
                  Financial Year 2026
                </span>
                <span className="inline-flex items-center gap-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-full font-semibold">
                  <ShieldCheck className="h-3 w-3" />
                  SC054652
                </span>
              </div>
              <p className="text-xs font-medium text-stone-600 dark:text-slate-400">
                Financial Year Ended 31 December 2026 • Scottish Charitable Incorporated Organisation (SCIO)
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={runCompliancePipeline}
                disabled={loading}
                className="royal-btn-crimson font-bold px-6 py-3.5 rounded-2xl shadow-md transition-all flex items-center justify-center gap-2.5 text-xs sm:text-sm disabled:opacity-50 active:scale-[0.98]"
              >
                <Play className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                <span>{loading ? "Preparing Accounts & Filing Packages..." : "Generate Annual Return & Accounts"}</span>
              </button>
            </div>
          </motion.div>

          {/* 2. Document & Transaction Ingest Center */}
          <motion.div variants={itemFadeUpVariants}>
            <UploadIngestCenter onIngestSuccess={runCompliancePipeline} />
          </motion.div>

          {/* 3. Financial State & Receipts & Payments Tracking */}
          <motion.div variants={itemFadeUpVariants} className="tour-dashboard-stats space-y-3">
            <div className="flex items-center justify-between border-b border-stone-200/80 dark:border-slate-800 pb-2">
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2">
                <Award className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                <span>Financial Ledger & Reconciliation Overview</span>
              </h3>
              <span className="text-[11px] font-mono text-stone-500 dark:text-slate-400">
                Statutory Currency: GBP (£)
              </span>
            </div>

            {loading && !pipelineResult ? (
              <div className="p-8 text-center bg-white dark:bg-[#111827] rounded-3xl border border-stone-200 dark:border-slate-800 shadow-xs animate-pulse text-amber-800 dark:text-amber-400 font-serif text-sm flex flex-col items-center justify-center gap-3">
                <div className="h-6 w-6 rounded-full border-2 border-red-600 border-t-transparent animate-spin" />
                <span>Reconciling bank accounts and preparing statutory balances...</span>
              </div>
            ) : (
              <FinancialSummaryCards
                grossReceipts={rnp.gross_receipts_decimal || "0.00"}
                grossPayments={rnp.gross_payments_decimal || "0.00"}
                netMovement={rnp.net_movement_decimal || "0.00"}
                reconciled={balances.reconciled ?? Boolean(pipelineResult)}
                thresholdBreached={pipelineResult?.income_threshold_breach ?? false}
              />
            )}
          </motion.div>

          {/* 4. Statutory Deliverables & Trustee Sign-off Center */}
          <motion.div variants={itemFadeUpVariants}>
            <DeliverableDownloadGrid
              deliverables={deliverables}
              onOpenSignoff={(hash) => setActiveSignoffHash(hash)}
              signatures={signatures}
            />
          </motion.div>
        </motion.div>

        {/* Modals & Drawers */}
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

        {/* Floating Beacon Statutory Advisor */}
        <ComplianceChatDrawer />
      </main>

      <footer className="border-t border-stone-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-[#070A11]/90 py-6 text-center text-xs font-medium text-stone-600 dark:text-slate-400 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 space-y-1">
          <p className="font-semibold text-slate-800 dark:text-slate-200">
            © 2026 Potter&apos;s House Christian Mission UK. Registered Scottish Charity (SCIO, SC054652).
          </p>
          <p className="text-[11px] text-stone-500 dark:text-slate-500">
            Principal Office: 5B Beachmont Court, Dunbar, Scotland, EH42 1YF • Regulated by the Office of the Scottish Charity Regulator (OSCR)
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return <DashboardContent />;
}
