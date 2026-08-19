"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, KeyRound, Landmark, Building2, Award, Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

export const LoginForm: React.FC = () => {
  const { loginWithEmail, loginWith2FA, getGoogleLoginUrl, error: authError, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [totpCode, setTotpCode] = useState("");
  const [pending2FA, setPending2FA] = useState(false);
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(false);
    clearError();
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        setLoading(false);
        clearError();
      }
    };
    window.addEventListener("pageshow", handlePageShow);
    return () => window.removeEventListener("pageshow", handlePageShow);
  }, [clearError]);

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
    <div className="min-h-screen bg-[#FBF9F5] dark:bg-[#070A11] relative overflow-hidden flex flex-col justify-center items-center p-4 sm:p-6 text-slate-900 dark:text-slate-100 transition-colors duration-300">
      <div className="fixed top-0 left-0 right-0 h-1.5 gold-ribbon z-50" />

      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-red-500/5 dark:bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-amber-500/5 dark:bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.gentle}
        className="max-w-md w-full royal-card bg-white dark:bg-[#0E1524] p-8 sm:p-10 rounded-3xl border border-stone-200 dark:border-slate-800 shadow-xl relative z-10 space-y-6"
      >
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-1">
            <img
              src="/assets/logo.png"
              alt="Potter's House Christian Mission UK Crest"
              className="h-16 w-auto object-contain dark:hidden drop-shadow-xs"
            />
            <img
              src="/assets/logo_dark.png"
              alt="Potter's House Christian Mission UK Crest"
              className="h-16 w-auto object-contain hidden dark:block drop-shadow-xs"
            />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white font-serif">
              Beacon Compliance
            </h1>
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 mt-2 rounded-full bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-mono font-medium">
              <Landmark className="h-3 w-3 text-amber-600 dark:text-amber-400" />
              <span>Scottish Charity SC054652 • Trustee Portal</span>
            </div>
          </div>
          <p className="text-xs font-medium text-stone-600 dark:text-slate-400 max-w-xs mx-auto">
            Potter&apos;s House Christian Mission UK <br />
            <span className="text-[11px] text-stone-500 dark:text-slate-500 italic font-editorial">&quot;Building Lives, Strengthening Homes, Shaping Nations for Christ&quot;</span>
          </p>
        </div>

        {activeError && (
          <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-xl text-xs text-red-700 dark:text-red-300 flex items-start gap-2.5 shadow-xs">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
            <span className="leading-relaxed font-medium">{activeError}</span>
          </div>
        )}

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full py-3 px-4 bg-white dark:bg-slate-800 hover:bg-stone-50 dark:hover:bg-slate-700 active:bg-stone-100 text-slate-800 dark:text-slate-100 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-3 border border-stone-300 dark:border-slate-700 shadow-xs transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
        >
          <svg className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" viewBox="0 0 24 24">
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

        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-stone-200 dark:bg-slate-800" />
          <span className="text-[11px] text-stone-500 dark:text-slate-500 uppercase tracking-wider font-mono font-medium">Or sign in with email</span>
          <div className="h-px flex-1 bg-stone-200 dark:bg-slate-800" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!pending2FA ? (
            <>
              <div className="space-y-1.5">
                <label className="block text-stone-700 dark:text-slate-300 font-semibold text-xs flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-stone-500 dark:text-slate-400" />
                  <span>Trustee Email</span>
                </label>
                <input
                  type="email"
                  required
                  placeholder="name@pottershouse.org.uk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-stone-50 dark:bg-slate-800/80 border border-stone-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 text-sm focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all shadow-xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-stone-700 dark:text-slate-300 font-semibold text-xs flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-stone-500 dark:text-slate-400" />
                  <span>Password</span>
                </label>
                <div className="relative flex items-center">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 pr-10 bg-stone-50 dark:bg-slate-800/80 border border-stone-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-stone-400 dark:placeholder:text-slate-500 text-sm focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all shadow-xs"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 text-stone-400 hover:text-stone-600 dark:text-slate-500 dark:hover:text-slate-300 focus:outline-none transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <label className="block text-stone-700 dark:text-slate-300 font-semibold text-xs flex items-center gap-1.5">
                <KeyRound className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                <span>6-Digit Authenticator App Code</span>
              </label>
              <input
                type="text"
                required
                maxLength={6}
                placeholder="000000"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full px-4 py-3 bg-stone-50 dark:bg-slate-800/80 border border-amber-500/50 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-amber-600 focus:ring-2 focus:ring-amber-500/20 transition-all text-center text-xl tracking-[0.3em] font-mono shadow-xs"
              />
              <p className="text-[11px] text-stone-500 dark:text-slate-400 text-center pt-1">
                Enter the 6-digit code from your authenticator app (e.g. Google or Microsoft Authenticator).
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 royal-btn-crimson font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50 active:scale-[0.98]"
          >
            <span>{loading ? "Signing in..." : pending2FA ? "Verify Code" : "Sign In to Portal"}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </form>

        <div className="text-center pt-1 border-t border-stone-100 dark:border-slate-800/60">
          <p className="text-[11px] text-stone-500 dark:text-slate-500">
            Access restricted to authorised Potter&apos;s House charity trustees (SC054652).
          </p>
        </div>
      </motion.div>
    </div>
  );
};
