"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, KeyRound, Sparkles } from "lucide-react";

export const LoginForm: React.FC = () => {
  const { loginWithEmail, loginWith2FA, getGoogleLoginUrl, error: authError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [pending2FA, setPending2FA] = useState(false);
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLocalError(null);

    try {
      if (pending2FA && tempToken) {
        await loginWith2FA(tempToken, totpCode);
      } else {
        const result = await loginWithEmail(email, password);
        if (result.requires_2fa) {
          setPending2FA(true);
          setTempToken(result.tempToken || null);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in.";
      setLocalError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setLocalError(null);
    try {
      const authUrl = await getGoogleLoginUrl();
      window.location.href = authUrl;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to launch Google Sign-In.";
      setLocalError(msg);
      setLoading(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="min-h-screen bg-[#070B14] relative overflow-hidden flex flex-col justify-center items-center p-6 text-slate-100 selection:bg-red-500/30">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full glass-card p-8 sm:p-10 rounded-3xl border border-white/10 shadow-2xl relative z-10 space-y-7">
        {/* Header Branding */}
        <div className="text-center space-y-3">
          <div className="inline-flex p-3.5 rounded-2xl bg-gradient-to-br from-red-500/20 to-amber-500/20 text-red-400 border border-red-500/30 shadow-lg shadow-red-500/5 mb-1">
            <ShieldCheck className="h-9 w-9 text-red-500" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
              Beacon Compliance
            </h1>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mt-2 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] font-mono font-medium">
              <Sparkles className="h-3 w-3 text-amber-400" />
              <span>SCIO SC054652 • Trustee Portal</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 max-w-xs mx-auto">
            Potter&apos;s House Christian Mission UK (Dunbar, Scotland)
          </p>
        </div>

        {activeError && (
          <div className="p-3.5 bg-red-950/40 border border-red-500/40 rounded-xl text-xs text-red-300 flex items-start gap-2.5 shadow-sm">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
            <span className="leading-relaxed">{activeError}</span>
          </div>
        )}

        {/* Google Auth Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full py-3.5 px-4 bg-white hover:bg-slate-100 active:bg-slate-200 text-slate-900 rounded-xl font-semibold text-sm flex items-center justify-center gap-3 shadow-lg shadow-black/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Sign in with Google</span>
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-[11px] text-slate-500 uppercase tracking-wider font-mono">Or Credentials</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {!pending2FA ? (
            <>
              <div className="space-y-1.5">
                <label className="block text-slate-300 font-medium text-xs flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  <span>Trustee Email</span>
                </label>
                <input
                  type="email"
                  required
                  placeholder="name@pottershouse.org.uk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-900/80 border border-white/10 rounded-xl text-slate-100 placeholder:text-slate-500 text-sm focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/50 transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-slate-300 font-medium text-xs flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-slate-400" />
                  <span>Password / Temporary Key</span>
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-900/80 border border-white/10 rounded-xl text-slate-100 placeholder:text-slate-500 text-sm focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/50 transition-all"
                />
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <label className="block text-slate-300 font-medium text-xs flex items-center gap-1.5">
                <KeyRound className="h-3.5 w-3.5 text-amber-400" />
                <span>Authenticator Code (2FA)</span>
              </label>
              <input
                type="text"
                required
                maxLength={6}
                placeholder="000000"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full px-4 py-3 bg-slate-900/80 border border-amber-500/40 rounded-xl text-white focus:outline-none focus:border-amber-400 focus:ring-1 focus:ring-amber-400/50 transition-all text-center text-xl tracking-[0.3em] font-mono"
              />
              <p className="text-[11px] text-slate-400 text-center pt-1">
                Enter the 6-digit code from Google Authenticator or your 2FA app.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 brand-gradient text-white font-semibold rounded-xl shadow-lg shadow-red-600/20 hover:opacity-95 active:scale-[0.99] transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50 pt-3"
          >
            <span>{loading ? "Authenticating..." : pending2FA ? "Verify Code" : "Sign In to Portal"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="text-center pt-2">
          <p className="text-[11px] text-slate-500">
            Access strictly restricted to authorized SCIO trustees.
          </p>
        </div>
      </div>
    </div>
  );
};
