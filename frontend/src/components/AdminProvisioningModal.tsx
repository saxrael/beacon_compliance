"use client";

import React, { useState } from "react";
import { UserPlus, Key, CheckCircle, AlertCircle, Copy, Check } from "lucide-react";
import { API_BASE_URL } from "@/config";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-red-500/10 text-red-600 dark:text-yellow-400">
              <UserPlus className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Create Trustee Account</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Trustee Registration & Access Management</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-lg font-bold"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result ? (
          <div className="space-y-4 bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-xl">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
              <CheckCircle className="h-5 w-5" />
              <span>Trustee Account Created Successfully!</span>
            </div>
            <div className="text-xs text-slate-700 dark:text-slate-300 space-y-2 font-mono bg-white dark:bg-slate-950 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
              <p><span className="text-slate-400">Email:</span> {result.email}</p>
              <p><span className="text-slate-400">Role:</span> {result.role}</p>
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <div>
                  <span className="text-slate-400 block text-[10px]">Temporary Password:</span>
                  <span className="text-red-600 dark:text-yellow-400 font-bold text-sm">{result.temp_password}</span>
                </div>
                <button
                  onClick={copyToClipboard}
                  className="px-2.5 py-1.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1 text-[11px]"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Share this temporary password securely with the trustee (for example, by direct message or in person). They will be asked to choose a permanent password when they first sign in.
            </p>
            <button
              onClick={() => setResult(null)}
              className="w-full py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold hover:bg-slate-200"
            >
              Register Another Trustee
            </button>
          </div>
        ) : (
          <form onSubmit={handleProvision} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Trustee Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Trustee Email Address</label>
              <input
                type="email"
                required
                placeholder="e.g. trustee@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-500 font-semibold"
              >
                <option value="Chair">Chair (Executive Trustee)</option>
                <option value="Secretary">Secretary (Executive Trustee)</option>
                <option value="Treasurer">Treasurer (Executive Trustee)</option>
                <option value="Trustee">General Trustee</option>
                <option value="Developer">System Administrator</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1 flex items-center justify-between">
                <span>Administrator Authorisation Code</span>
                <Key className="h-3 w-3 text-slate-400" />
              </label>
              <input
                type="password"
                required
                value={adminSecret}
                onChange={(e) => setAdminSecret(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl font-semibold hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 brand-gradient text-white rounded-xl font-bold shadow-lg shadow-red-900/30 hover:opacity-90 disabled:opacity-50"
              >
                {loading ? "Creating Account..." : "Create Trustee Account"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
