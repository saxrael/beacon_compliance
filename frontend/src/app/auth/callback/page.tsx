"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, AlertCircle, ArrowLeft, Loader2, Award, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loginWithGoogle } = useAuth();

  const [statusText, setStatusText] = useState("Verifying Google Trustee credentials...");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const hasExecutedRef = React.useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");
    const errorDesc = searchParams.get("error_description");

    if (errorParam) {
      setErrorMessage(errorDesc || `Google authorization was cancelled or failed (${errorParam}).`);
      return;
    }

    if (!code) {
      setErrorMessage("No authorization code was received from Google OAuth service.");
      return;
    }

    if (hasExecutedRef.current) {
      return;
    }
    hasExecutedRef.current = true;

    let isMounted = true;

    async function completeOAuth() {
      try {
        setStatusText("Exchanging authorization token and verifying SCIO trustee permissions...");
        await loginWithGoogle(code!, state || undefined);
        if (isMounted) {
          setIsSuccess(true);
          setStatusText("Authentication verified. Redirecting to Trustee Compliance Portal...");
          setTimeout(() => {
            router.push("/");
          }, 800);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : "Google OAuth sign-in failed. Please ensure your Google account email matches your provisioned trustee profile.";
          setErrorMessage(msg);
        }
      }
    }

    completeOAuth();

    return () => {
      isMounted = false;
    };
  }, [searchParams, loginWithGoogle, router]);

  return (
    <div className="min-h-screen bg-[#FBF9F5] dark:bg-[#070A11] relative overflow-hidden flex flex-col justify-center items-center p-4 sm:p-6 text-slate-900 dark:text-slate-100 transition-colors duration-300">
      <div className="fixed top-0 left-0 right-0 h-1.5 gold-ribbon z-50" />

      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-red-500/5 dark:bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-amber-500/5 dark:bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.gentle}
        className="max-w-md w-full royal-card bg-white dark:bg-[#0E1524] p-8 sm:p-10 rounded-3xl border border-stone-200 dark:border-slate-800 shadow-xl relative z-10 space-y-6 text-center"
      >
        <div className="space-y-2">
          <div className="flex justify-center mb-1">
            <img
              src="/assets/logo.png"
              alt="Potter's House Crest"
              className="h-16 w-auto object-contain dark:hidden drop-shadow-xs"
            />
            <img
              src="/assets/logo_dark.png"
              alt="Potter's House Crest"
              className="h-16 w-auto object-contain hidden dark:block drop-shadow-xs"
            />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white font-serif">
            Beacon Compliance
          </h1>
          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-mono font-medium">
            <Sparkles className="h-3 w-3 text-amber-600 dark:text-amber-400" />
            <span>SCIO SC054652 • OAuth Gateway</span>
          </div>
        </div>

        {errorMessage ? (
          <div className="space-y-4">
            <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 rounded-2xl text-xs text-red-700 dark:text-red-300 text-left flex items-start gap-3 shadow-xs">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-600 dark:text-red-400 mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold block">Authentication Unsuccessful</span>
                <span className="leading-relaxed block">{errorMessage}</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => router.push("/")}
              className="w-full py-3 royal-btn-crimson font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2 text-xs sm:text-sm active:scale-[0.98]"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Portal Sign In</span>
            </button>
          </div>
        ) : (
          <div className="py-6 space-y-4">
            <div className="flex justify-center">
              {isSuccess ? (
                <div className="h-12 w-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
                  <ShieldCheck className="h-7 w-7" />
                </div>
              ) : (
                <div className="h-12 w-12 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 flex items-center justify-center shadow-xs">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              )}
            </div>

            <p className="text-xs sm:text-sm font-medium text-stone-700 dark:text-slate-300">
              {statusText}
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#FBF9F5] dark:bg-[#0B0F19] flex items-center justify-center text-amber-700 dark:text-amber-400 font-mono text-sm">
          <div className="flex items-center gap-3 p-6 rounded-2xl bg-white dark:bg-slate-900 border border-stone-200 dark:border-slate-800 shadow-md">
            <div className="h-4 w-4 rounded-full border-2 border-amber-600 border-t-transparent animate-spin" />
            <span>Loading authentication gateway...</span>
          </div>
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}
