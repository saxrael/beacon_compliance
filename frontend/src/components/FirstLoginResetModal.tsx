"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { KeyRound, ShieldAlert, CheckCircle } from "lucide-react";

export const FirstLoginResetModal: React.FC = () => {
  const { user, completeFirstLoginReset } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || user.first_login_complete) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await completeFirstLoginReset(user.email, currentPassword, newPassword);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update password.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-6 sm:p-8 space-y-5 text-slate-900 dark:text-slate-100">
        <div className="flex items-center gap-3 border-b border-stone-100 dark:border-slate-800 pb-4">
          <div className="p-2.5 rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30 shadow-xs">
            <KeyRound className="h-6 w-6 text-red-600 dark:text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold font-serif">Set Permanent Password</h3>
            <p className="text-xs text-stone-500 dark:text-slate-400">First-Login Credential Security Gate</p>
          </div>
        </div>

        <div className="p-3.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-500/30 rounded-2xl text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
          <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
          <span className="leading-relaxed">
            You are signed in with a temporary password. UK OSCR security regulations require setting a permanent password before accessing compliance records.
          </span>
        </div>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-xl text-xs text-red-700 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="block text-stone-700 dark:text-slate-300 font-semibold">Temporary Password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-500/20 shadow-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-stone-700 dark:text-slate-300 font-semibold">New Permanent Password</label>
            <input
              type="password"
              required
              placeholder="At least 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-500/20 shadow-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-stone-700 dark:text-slate-300 font-semibold">Confirm New Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-red-600 focus:ring-2 focus:ring-red-500/20 shadow-xs"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white rounded-xl font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50 mt-2"
          >
            <CheckCircle className="h-4 w-4" />
            <span>{loading ? "Updating Credentials..." : "Update Password & Enter Portal"}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
