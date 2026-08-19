"use client";

import React, { useState } from "react";
import { UploadCloud, FileText, CheckCircle2, ShieldCheck, AlertCircle, Plus, Sparkles, ArrowRight, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";
import { API_BASE_URL } from "@/config";
import { useAuth } from "@/context/AuthContext";

interface UploadIngestProps {
  onIngestSuccess?: () => void;
}

export const UploadIngestCenter: React.FC<UploadIngestProps> = ({ onIngestSuccess }) => {
  const { token } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [fundType, setFundType] = useState("unrestricted_general");
  const [amount, setAmount] = useState("");
  const [isReceipt, setIsReceipt] = useState(true);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!selectedFile && !description.trim()) {
      setErrorMessage("Please attach a bank statement/receipt file or enter a transaction description.");
      return;
    }

    setLoading(true);
    try {
      const activeToken = token || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null);
      const formData = new FormData();
      
      if (selectedFile) {
        formData.append("files", selectedFile);
      } else {
        const textPayload = `Transaction: ${description}\nType: ${isReceipt ? "receipt" : "payment"}\nFund: ${fundType}\nAmount: £${amount || "0.00"}`;
        const blob = new Blob([textPayload], { type: "text/plain" });
        formData.append("files", blob, "transaction_entry.txt");
      }

      const headers: Record<string, string> = {};
      if (activeToken) {
        headers["Authorization"] = `Bearer ${activeToken}`;
      }

      const res = await fetch(`${API_BASE_URL}/api/ingest/upload?run_id=run_001`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to process document upload.");
      }

      const data = await res.json();
      setSuccessMessage(`Document successfully processed. Personal and banking details were automatically protected and saved to the ledger.`);
      setSelectedFile(null);
      setDescription("");
      setAmount("");
      if (onIngestSuccess) {
        onIngestSuccess();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error uploading document.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tour-upload-center royal-card rounded-3xl p-6 sm:p-7 border border-stone-200 dark:border-slate-800 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-200/80 dark:border-slate-800/80 pb-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 font-serif flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30">
              <UploadCloud className="h-5 w-5" />
            </div>
            <span>Document & Transaction Upload Center</span>
          </h2>
          <p className="text-xs text-stone-600 dark:text-slate-400 mt-1">
            Upload bank statements, donation records, invoices, or enter transactions directly to update the charity ledger.
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30 text-[11px] font-mono font-semibold self-start sm:self-auto">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>Donor Privacy & Data Protection Active</span>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 rounded-2xl text-xs text-red-700 dark:text-red-300 flex items-start gap-2.5 shadow-xs">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
          <span className="font-medium">{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 rounded-2xl text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5 shadow-xs">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
          <span className="font-medium">{successMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Dropzone */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-3">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
              isDragOver
                ? "border-amber-500 bg-amber-50/50 dark:bg-amber-950/20 scale-[1.01]"
                : selectedFile
                ? "border-emerald-500/60 bg-emerald-50/30 dark:bg-emerald-950/10"
                : "border-stone-300 dark:border-slate-700 bg-stone-50/50 dark:bg-slate-900/30 hover:border-amber-500/60 hover:bg-stone-50 dark:hover:bg-slate-900/50"
            }`}
            onClick={() => document.getElementById("file-upload-input")?.click()}
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf,.csv,.txt,.xlsx,.docx,.png,.jpg"
              className="hidden"
              onChange={handleFileChange}
            />

            <div className="h-12 w-12 rounded-2xl bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center mb-3">
              <UploadCloud className="h-6 w-6" />
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate max-w-xs">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-stone-500 dark:text-slate-400 font-mono">
                  {(selectedFile.size / 1024).toFixed(1)} KB • Ready to Upload
                </p>
                <span className="inline-block mt-2 text-[11px] text-amber-700 dark:text-amber-400 underline font-semibold">
                  Click to replace file
                </span>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                  Drop bank statements, receipts or logs here
                </p>
                <p className="text-xs text-stone-500 dark:text-slate-400">
                  Supports PDF bank statements, Excel spreadsheets, CSVs, or Scanned receipts
                </p>
                <span className="inline-block mt-2 text-xs font-semibold text-red-600 dark:text-amber-400">
                  or Browse Local Files
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Transaction Log / Description Capture */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-4 bg-stone-50/60 dark:bg-slate-950/40 p-5 rounded-2xl border border-stone-200 dark:border-slate-800">
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                Transaction Description & Details
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Sunday weekly tithes & offerings / Church hall lease payment"
                className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Amount (£)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs font-num text-slate-900 dark:text-slate-100 placeholder:text-stone-400 focus:outline-none focus:border-amber-500 shadow-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Charity Fund Category
                </label>
                <select
                  value={fundType}
                  onChange={(e) => setFundType(e.target.value)}
                  className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-amber-500 shadow-xs"
                >
                  <option value="unrestricted_general">General Unrestricted Fund</option>
                  <option value="restricted_building">Building & Capital Reserve</option>
                  <option value="restricted_mission">Missions & Community Outreach</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Flow Type:</label>
              <button
                type="button"
                onClick={() => setIsReceipt(true)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  isReceipt
                    ? "bg-emerald-600 text-white shadow-xs"
                    : "bg-stone-200 dark:bg-slate-800 text-stone-600 dark:text-slate-400"
                }`}
              >
                Receipt (Money In)
              </button>
              <button
                type="button"
                onClick={() => setIsReceipt(false)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  !isReceipt
                    ? "bg-rose-600 text-white shadow-xs"
                    : "bg-stone-200 dark:bg-slate-800 text-stone-600 dark:text-slate-400"
                }`}
              >
                Payment (Money Out)
              </button>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || (!selectedFile && !description.trim())}
              className="w-full royal-btn-gold font-bold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center gap-2 disabled:opacity-50 transition-all active:scale-[0.99]"
            >
              <span>{loading ? "Processing & Protecting Personal Data..." : "Record into Charity Accounts"}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
