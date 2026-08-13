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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-6 space-y-5 text-slate-100">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="p-2.5 rounded-2xl bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
            <KeyRound className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold">Set Permanent Password</h3>
            <p className="text-xs text-slate-400">First-Login Credential Security Gate</p>
          </div>
        </div>

        <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl text-xs text-yellow-400 flex items-start gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            You are signed in with a temporary password. UK OSCR security regulations require setting a permanent password before accessing compliance records.
          </span>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Temporary Password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">New Permanent Password</label>
            <input
              type="password"
              required
              placeholder="At least 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Confirm New Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 brand-gradient text-white rounded-xl font-bold shadow-lg shadow-red-900/30 hover:opacity-90 transition-opacity flex items-center justify-center gap-2 text-sm disabled:opacity-50 mt-2"
          >
            <CheckCircle className="h-4 w-4" />
            <span>{loading ? "Updating Credentials..." : "Update Password & Enter Portal"}</span>
          </button>
        </form>
      </div>
    </div>
  );
};
