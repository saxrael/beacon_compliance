"use client";

import React, { useState } from "react";
import { UserPlus, Key, CheckCircle, AlertCircle, Copy, Check, X, Shield, Landmark } from "lucide-react";
import { API_BASE_URL } from "@/config";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";
import { ClientPortal } from "./ClientPortal";

interface AdminProvisioningModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AdminProvisioningModal: React.FC<AdminProvisioningModalProps> = ({ isOpen, onClose }) => {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("Treasurer");
  const [adminSecret, setAdminSecret] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ email: string; temp_password: string; role: string } | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/provision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Secret": adminSecret,
        },
        body: JSON.stringify({ email, name, role }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Account creation failed (error ${res.status}).`);
      }

      const data = await res.json();
      setResult(data);
      setEmail("");
      setName("");
      setAdminSecret("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create trustee account.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result?.temp_password) {
      navigator.clipboard.writeText(result.temp_password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <ClientPortal>
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-provision-title"
      >
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 12 }}
          transition={springs.gentle}
          className="royal-card bg-white dark:bg-[#0E1626] border border-stone-200 dark:border-slate-800/80 rounded-3xl shadow-2xl max-w-md w-full p-6 sm:p-7 space-y-5 relative overflow-hidden"
        >
          {/* Header Accent Ribbon */}
          <div className="absolute top-0 left-0 right-0 h-1 gold-ribbon" />

          <div className="flex items-center justify-between border-b border-stone-200/80 dark:border-slate-800/80 pb-4 pt-1">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 flex items-center justify-center shadow-xs">
                <UserPlus className="h-5 w-5 text-red-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 id="admin-provision-title" className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 font-serif">
                  Register New Trustee
                </h3>
                <p className="text-xs font-medium text-stone-500 dark:text-slate-400">
                  Trustee Account Provisioning & Governance
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close registration modal"
              className="p-1.5 rounded-xl text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {error && (
            <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-2xl text-xs text-red-700 dark:text-red-300 flex items-start gap-2.5 shadow-xs">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
              <span className="font-medium">{error}</span>
            </div>
          )}

          {result ? (
            <div className="space-y-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-500/30 p-5 rounded-2xl">
              <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-xs sm:text-sm">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>Trustee Account Created Successfully!</span>
              </div>
              
              <div className="text-xs text-slate-700 dark:text-slate-200 space-y-2 font-mono bg-white dark:bg-[#080D18] p-3.5 rounded-xl border border-stone-200 dark:border-slate-800 shadow-xs">
                <p><span className="text-stone-400 dark:text-slate-500">Email:</span> {result.email}</p>
                <p><span className="text-stone-400 dark:text-slate-500">Role:</span> {result.role}</p>
                
                <div className="flex items-center justify-between gap-2 pt-2.5 border-t border-stone-200 dark:border-slate-800">
                  <div>
                    <span className="text-stone-400 dark:text-slate-500 block text-[10px] uppercase font-bold">Temporary Password:</span>
                    <span className="text-red-700 dark:text-amber-400 font-bold text-sm select-all">{result.temp_password}</span>
                  </div>
                  <button
                    onClick={copyToClipboard}
                    className="px-3 py-1.5 royal-btn-gold rounded-lg text-xs flex items-center gap-1.5 active:scale-95 transition-all"
                  >
                    {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                </div>
              </div>

              <p className="text-[11px] text-stone-600 dark:text-slate-400 leading-relaxed">
                Share this temporary password securely with the trustee. They will be required to set their permanent password and configure two-step verification upon initial login.
              </p>

              <button
                onClick={() => setResult(null)}
                className="w-full py-2.5 bg-stone-100 dark:bg-slate-800 hover:bg-stone-200 dark:hover:bg-slate-700 text-stone-800 dark:text-slate-200 rounded-xl text-xs font-semibold transition-colors"
              >
                Register Another Trustee
              </button>
            </div>
          ) : (
            <form onSubmit={handleProvision} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="block text-slate-700 dark:text-slate-200 font-semibold uppercase text-[11px] tracking-wider">
                  Trustee Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-[#080D18] border border-stone-300 dark:border-slate-700/80 rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-slate-700 dark:text-slate-200 font-semibold uppercase text-[11px] tracking-wider">
                  Trustee Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. trustee@pottershouse.org.uk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-[#080D18] border border-stone-300 dark:border-slate-700/80 rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-slate-700 dark:text-slate-200 font-semibold uppercase text-[11px] tracking-wider">
                  Trustee Governance Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-[#080D18] border border-stone-300 dark:border-slate-700/80 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs font-semibold"
                >
                  <option value="Chair">Chair of Trustees (Executive Signatory)</option>
                  <option value="Secretary">Charity Secretary (Executive Signatory)</option>
                  <option value="Treasurer">Charity Treasurer (Executive Signatory)</option>
                  <option value="Trustee">General Charity Trustee</option>
                  <option value="Developer">System Administrator</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-slate-700 dark:text-slate-200 font-semibold uppercase text-[11px] tracking-wider flex items-center justify-between">
                  <span>Administrator Authorization Key</span>
                  <Key className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                </label>
                <input
                  type="password"
                  required
                  placeholder="Enter administrator authorization key"
                  value={adminSecret}
                  onChange={(e) => setAdminSecret(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-[#080D18] border border-stone-300 dark:border-slate-700/80 rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 shadow-xs"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-stone-200/80 dark:border-slate-800/80">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl text-stone-600 dark:text-slate-300 hover:bg-stone-100 dark:hover:bg-slate-800 font-semibold transition-colors text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2.5 royal-btn-crimson font-bold rounded-xl shadow-md transition-all disabled:opacity-50 active:scale-[0.98] text-xs flex items-center justify-center gap-2"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  <span>{loading ? "Creating Account..." : "Create Trustee Account"}</span>
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </ClientPortal>
  );
};

