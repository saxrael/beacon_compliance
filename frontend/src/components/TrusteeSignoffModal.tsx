"use client";

import React, { useState } from "react";
import { KeyRound, ShieldCheck, X } from "lucide-react";
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
      const res = await fetch(`${API_BASE_URL}/api/signoff/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="glass-card max-w-md w-full rounded-2xl p-6 border border-slate-700 space-y-5 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/assets/trustee_seal.png" alt="Trustee Seal" className="h-10 w-10 object-contain rounded-full shadow-md" onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }} />
            <div>
              <h3 id="modal-title" className="text-base font-bold text-slate-100">
                Trustee Sign-off Approval
              </h3>
              <p className="text-xs text-slate-400 capitalize">Role: {trusteeRole}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close sign-off modal"
            className="text-slate-400 hover:text-slate-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800 text-xs space-y-1 font-mono text-slate-300">
          <span className="text-slate-500 block">Deliverable SHA-256 Hash:</span>
          <span className="break-all text-amber-400">{deliverableHash}</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="trustee-secret-input" className="block text-xs font-medium text-slate-300 mb-1">
              Trustee Secret Key
            </label>
            <input
              id="trustee-secret-input"
              type="password"
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Enter your HMAC trustee secret"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-amber-500"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full brand-gradient font-bold text-white rounded-lg py-2.5 text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-md shadow-red-900/30"
          >
            <ShieldCheck className="h-4 w-4" />
            {loading ? "Verifying Sign-off..." : "Apply Trustee Signature"}
          </button>
        </form>
      </div>
    </div>
  );
};

