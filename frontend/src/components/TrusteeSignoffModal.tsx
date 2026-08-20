"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { KeyRound, ShieldCheck, X, AlertCircle, Award, Lock, FileCheck } from "lucide-react";
import { API_BASE_URL } from "@/config";
import { motion } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

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
  const { token: authToken } = useAuth();
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!secret) {
      setError("Please enter your trustee authorization key.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const activeToken = authToken || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") || localStorage.getItem("trustee_token") || "secret_trustee_token_chair" : "secret_trustee_token_chair");
      const res = await fetch(`${API_BASE_URL}/api/signoff/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${activeToken}`,
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
      className="fixed inset-0 z-50 bg-slate-950/65 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={springs.gentle}
        className="royal-card bg-white dark:bg-[#0E1524] max-w-md w-full max-h-[90vh] overflow-y-auto rounded-3xl p-5 sm:p-8 border border-stone-200 dark:border-slate-800 space-y-5 shadow-2xl relative my-auto"
      >
        <div className="flex items-center justify-between border-b border-stone-200/80 dark:border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 flex items-center justify-center shadow-xs">
              <Award className="h-6 w-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 id="modal-title" className="text-base font-bold text-slate-900 dark:text-slate-100 font-serif">
                Trustee Statutory Approval
              </h3>
              <p className="text-xs font-semibold text-stone-600 dark:text-slate-400 capitalize">
                Designated Signatory Role: <span className="text-red-700 dark:text-amber-400 font-bold">{trusteeRole}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close sign-off modal"
            className="p-1.5 rounded-xl text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="bg-stone-50 dark:bg-slate-950 rounded-2xl p-4 border border-stone-200 dark:border-slate-800 text-xs space-y-1.5 font-mono">
          <span className="text-[10px] uppercase font-bold text-stone-500 dark:text-slate-500 block">Document Security Seal:</span>
          <span className="break-all text-slate-800 dark:text-amber-300 text-[11px] font-semibold">{deliverableHash}</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="trustee-secret-input" className="block text-xs font-bold text-stone-700 dark:text-slate-300 uppercase tracking-wider">
              Trustee Signing Key / Security Passcode
            </label>
            <div className="relative">
              <input
                id="trustee-secret-input"
                type="password"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                placeholder="Enter your confidential trustee signing key"
                className="w-full bg-stone-50 dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
              />
              <KeyRound className="h-4 w-4 text-stone-400 absolute right-3.5 top-3 pointer-events-none" />
            </div>
            <p className="text-[11px] text-stone-500 dark:text-slate-400 leading-relaxed">
              Applies your verified digital signature, certifying formal trustee approval of this statutory document for submission to the Scottish Charity Regulator (OSCR).
            </p>
          </div>

          {error && (
            <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-xl text-xs text-red-700 dark:text-red-300 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
              <span className="font-medium">{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full royal-btn-crimson font-bold rounded-xl py-3 text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 active:scale-[0.98]"
          >
            <ShieldCheck className="h-4 w-4" />
            <span>{loading ? "Verifying Trustee Signature..." : "Approve & Apply Trustee Signature"}</span>
          </button>
        </form>
      </motion.div>
    </div>
  );
};
