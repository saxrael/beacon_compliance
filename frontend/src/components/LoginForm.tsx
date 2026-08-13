"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";

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
    } catch (err: any) {
      setLocalError(err.message || "Failed to sign in.");
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
    } catch (err: any) {
      setLocalError(err.message || "Failed to launch Google Sign-In.");
      setLoading(false);
    }
  };

  const activeError = localError || authError;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 text-slate-100 transition-colors duration-300">
      <div className="max-w-md w-full glass-card p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-red-500/10 text-red-500 border border-red-500/20 mb-2">
            <ShieldCheck className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Beacon Compliance OS</h2>
          <p className="text-xs text-slate-400">
            Trustee Sign-In Portal • SCIO SC054652
          </p>
        </div>

        {activeError && (
          <div className="p-3.5 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 flex items-start gap-2.5">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{activeError}</span>
          </div>
        )}

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full py-3 px-4 bg-white hover:bg-slate-100 text-slate-900 rounded-xl font-semibold text-sm flex items-center justify-center gap-3 shadow-lg transition-all active:scale-[0.98] disabled:opacity-50"
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

        <div className="flex items-center gap-3 my-4">
          <div className="h-px flex-1 bg-slate-800"></div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider font-mono">Or Password</span>
          <div className="h-px flex-1 bg-slate-800"></div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {!pending2FA ? (
            <>
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  <span>Email Address</span>
                </label>
                <input
                  type="email"
                  required
                  placeholder="trustee@pottershouse.org.uk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-slate-400" />
                  <span>Password</span>
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-slate-400" />
                <span>Authenticator Code (2FA)</span>
              </label>
              <input
                type="text"
                required
                maxLength={6}
                placeholder="123456"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 focus:outline-none focus:border-red-500 transition-colors text-center text-lg tracking-widest font-mono"
              />
              <p className="text-[10px] text-slate-500 mt-2 text-center">
                Open your authenticator app to get your 6-digit code.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 brand-gradient text-white rounded-xl font-bold shadow-lg shadow-red-900/30 hover:opacity-90 transition-opacity flex items-center justify-center gap-2 text-sm disabled:opacity-50 mt-2"
          >
            <span>{loading ? "Authenticating..." : pending2FA ? "Verify 2FA" : "Sign In to Portal"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="text-center pt-2">
          <p className="text-[11px] text-slate-500">
            Account provisioning is restricted to pre-authorized trustees.
          </p>
        </div>
      </div>
    </div>
  );
};
