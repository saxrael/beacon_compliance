"use client";

import React, { useState } from "react";
import { KeyRound, ShieldCheck, X, AlertCircle } from "lucide-react";
import { API_BASE_URL } from "@/config";

interface SignoffModalProps {
  isOpen: boolean;
  onClose: () => void;
  trusteeRole: string;
  deliverableHash: string;
  onSuccess: (signature: string) => void;
}

export const TrusteeSignoffModal: React.FC<SignoffModalProps> = ({
  isOpen,
  onClose,
  trusteeRole,
  deliverableHash,
  onSuccess,
}) => {
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!secret) {
      setError("Please enter your secret trustee key.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("trustee_token") || "secret_trustee_token_chair" : "secret_trustee_token_chair";
      const res = await fetch(`${API_BASE_URL}/api/signoff/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          trustee_role: trusteeRole,
          trustee_secret: secret,
          deliverable_hash: deliverableHash,
          run_id: "run_001",
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Sign-off verification failed.");
      }

      const data = await res.json();
      onSuccess(data.hmac_signature);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to complete sign-off.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white dark:bg-slate-900 max-w-md w-full rounded-3xl p-6 sm:p-8 border border-stone-200 dark:border-slate-800 space-y-5 shadow-2xl relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30 flex items-center justify-center shadow-xs">
              <ShieldCheck className="h-6 w-6 text-red-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 id="modal-title" className="text-base font-bold text-slate-900 dark:text-slate-100 font-serif">
                Trustee Sign-off Approval
              </h3>
              <p className="text-xs font-semibold text-stone-600 dark:text-slate-400 capitalize">
                Designated Signatory: <span className="text-red-700 dark:text-amber-400">{trusteeRole}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close sign-off modal"
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="bg-stone-50 dark:bg-slate-950 rounded-xl p-3.5 border border-stone-200 dark:border-slate-800 text-xs space-y-1.5 font-mono">
          <span className="text-[10px] uppercase font-bold text-stone-500 dark:text-slate-500 block">Deliverable SHA-256 Hash:</span>
          <span className="break-all text-slate-800 dark:text-amber-300 text-[11px] font-semibold">{deliverableHash}</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="trustee-secret-input" className="block text-xs font-semibold text-stone-700 dark:text-slate-300">
              Trustee Secret HMAC Key
            </label>
            <div className="relative">
              <input
                id="trustee-secret-input"
                type="password"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                placeholder="Enter your secret trustee key"
                className="w-full bg-stone-50 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-500/20 shadow-xs"
              />
              <KeyRound className="h-4 w-4 text-stone-400 absolute right-3 top-3 pointer-events-none" />
            </div>
            <p className="text-[11px] text-stone-500 dark:text-slate-500">
              Signs the SHA-256 package using per-trustee HMAC-SHA256 cryptography per Red-Line 3.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-xl text-xs text-red-700 dark:text-red-300 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
              <span className="font-medium">{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 active:bg-red-800 font-bold text-white rounded-xl py-3 text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>{loading ? "Verifying HMAC Signature..." : "Apply Trustee Digital Signature"}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
