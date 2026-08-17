"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { X, Shield, Lock, Key, Copy, Check, ShieldAlert, ShieldCheck, Mail, User, Settings, QrCode, Smartphone, Info, ArrowRight } from "lucide-react";
import QRCode from "react-qr-code";
import { API_BASE_URL } from "@/config";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export const AccountSettingsModal: React.FC<AccountSettingsModalProps> = ({ onClose }) => {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");

  const [setup2FA, setSetup2FA] = useState(false);
  const [setupMode, setSetupMode] = useState<"qr" | "manual">("qr");
  const [qrCodeData, setQrCodeData] = useState<{ provisioning_uri: string; secret: string } | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwdTotpCode, setPwdTotpCode] = useState("");

  const formatSecretInGroups = (secret: string) => {
    return secret.match(/.{1,4}/g)?.join(" ") || secret;
  };

  const handleGenerate2FA = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const activeToken = token || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null);
      const res = await fetch(`${API_BASE_URL}/api/settings/2fa/generate`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${activeToken}`,
          "Content-Type": "application/json"
        }
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to generate 2-step verification key.");
      }
      const data = await res.json();
      setQrCodeData(data);
      setSetup2FA(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleEnable2FA = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const activeToken = token || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null);
      const res = await fetch(`${API_BASE_URL}/api/settings/2fa/enable`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${activeToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ totp_code: totpCode.trim() })
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid verification code. Please check your authenticator app and try again.");
      }
      
      setSuccessMsg("2-Step Verification has been successfully activated for your account!");
      setSetup2FA(false);
      setQrCodeData(null);
      setTotpCode("");

      setTimeout(() => window.location.reload(), 1800);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setErrorMsg("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setErrorMsg("New password must be at least 8 characters long.");
      return;
    }
    
    setLoading(true);
    setErrorMsg(null);
    try {
      const activeToken = token || (typeof window !== "undefined" ? localStorage.getItem("beacon_auth_token") : null);
      const res = await fetch(`${API_BASE_URL}/api/settings/password/change`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${activeToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          totp_code: user?.totp_enabled ? pwdTotpCode.trim() : undefined
        })
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to update password.");
      }
      
      setSuccessMsg("Your password has been updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPwdTotpCode("");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (qrCodeData?.secret) {
      navigator.clipboard.writeText(qrCodeData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/65 backdrop-blur-sm p-4 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-modal-title"
    >
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 12 }}
        transition={springs.gentle}
        className="royal-card bg-white dark:bg-[#0B0F19] border border-stone-200 dark:border-slate-800 shadow-2xl rounded-3xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] my-auto"
      >
        {/* Top Gold Ribbon */}
        <div className="h-1 gold-ribbon w-full" />
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200/80 dark:border-slate-800 bg-stone-50/60 dark:bg-slate-900/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-amber-700 dark:text-amber-400 shadow-xs">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h2 id="settings-modal-title" className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-50 font-serif">
                Trustee Account & Security
              </h2>
              <p className="text-xs text-stone-600 dark:text-slate-400">
                Potter&apos;s House Christian Mission UK (SC054652)
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 hover:bg-stone-200/60 dark:hover:bg-slate-800 rounded-xl transition-colors"
            aria-label="Close Settings"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-stone-200/80 dark:border-slate-800 px-6 bg-stone-50/30 dark:bg-slate-900/20">
          <button 
            onClick={() => { setActiveTab("profile"); setErrorMsg(null); setSuccessMsg(null); }}
            className={`px-4 py-3 text-xs sm:text-sm font-bold border-b-2 transition-all font-serif ${
              activeTab === "profile" 
                ? "border-red-600 text-red-700 dark:text-amber-400" 
                : "border-transparent text-stone-500 hover:text-stone-800 dark:hover:text-slate-300"
            }`}
          >
            Trustee Profile
          </button>
          <button 
            onClick={() => { setActiveTab("security"); setErrorMsg(null); setSuccessMsg(null); }}
            className={`px-4 py-3 text-xs sm:text-sm font-bold border-b-2 transition-all font-serif flex items-center gap-1.5 ${
              activeTab === "security" 
                ? "border-red-600 text-red-700 dark:text-amber-400" 
                : "border-transparent text-stone-500 hover:text-stone-800 dark:hover:text-slate-300"
            }`}
          >
            <Shield className="h-3.5 w-3.5" />
            <span>2-Step Verification & Password</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {errorMsg && (
            <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 text-red-700 dark:text-red-300 text-xs rounded-2xl flex items-start gap-2.5 shadow-xs">
              <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5 text-red-600 dark:text-red-400" />
              <span className="font-medium">{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300 text-xs rounded-2xl flex items-start gap-2.5 shadow-xs">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400" />
              <span className="font-medium">{successMsg}</span>
            </div>
          )}

          {activeTab === "profile" && (
            <div className="space-y-5">
              <div className="flex items-center gap-4 p-4 border border-stone-200 dark:border-slate-800 rounded-2xl bg-stone-50/60 dark:bg-slate-900/40">
                <div className="h-14 w-14 bg-gradient-to-br from-red-600 to-amber-600 text-white rounded-2xl flex items-center justify-center text-xl font-bold font-serif shadow-xs">
                  {user?.name?.charAt(0).toUpperCase() || "T"}
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base font-serif">{user?.name || "Authorized Trustee"}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-amber-300 border border-red-200 dark:border-red-500/30 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                      {user?.role || "Trustee"}
                    </span>
                    <span className="text-xs text-stone-500 dark:text-slate-400 font-mono">SC054652</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3.5">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-stone-600 dark:text-slate-400 flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                    <span>Registered Trustee Email</span>
                  </label>
                  <div className="px-3.5 py-2.5 bg-stone-100/80 dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl text-slate-800 dark:text-slate-200 text-xs font-mono">
                    {user?.email}
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-stone-600 dark:text-slate-400 flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                    <span>Trustee Full Name</span>
                  </label>
                  <div className="px-3.5 py-2.5 bg-stone-100/80 dark:bg-slate-900 border border-stone-200 dark:border-slate-800 rounded-xl text-slate-800 dark:text-slate-200 text-xs">
                    {user?.name}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              {/* 2-Step Verification Section */}
              <div className="space-y-4">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-2 font-serif">
                    <Shield className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    <span>2-Step Verification (Authenticator App)</span>
                  </h3>
                  <p className="text-xs text-stone-600 dark:text-slate-400 mt-1 leading-relaxed">
                    Protect your trustee account with a 6-digit rolling code from an authenticator app whenever you sign in or authorize compliance filings.
                  </p>
                </div>

                {user?.totp_enabled && !setup2FA ? (
                  <div className="p-4 border border-emerald-200 dark:border-emerald-500/30 bg-emerald-50/60 dark:bg-emerald-950/20 rounded-2xl flex items-center justify-between shadow-xs">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 rounded-xl">
                        <ShieldCheck className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-xs sm:text-sm font-bold text-emerald-900 dark:text-emerald-200">2-Step Verification is Active</p>
                        <p className="text-[11px] text-emerald-700 dark:text-emerald-400">Your account is secured with rolling 6-digit authenticator codes.</p>
                      </div>
                    </div>
                  </div>
                ) : setup2FA && qrCodeData ? (
                  <div className="p-5 sm:p-6 border border-stone-200 dark:border-slate-800 rounded-3xl space-y-5 bg-stone-50/70 dark:bg-slate-950/50">
                    
                    {/* Setup Instructions Steps */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-slate-100 font-serif">
                        <span className="h-5 w-5 rounded-full bg-red-600 text-white flex items-center justify-center text-[11px] font-mono">1</span>
                        <span>Open an Authenticator App on your phone</span>
                      </div>
                      <p className="text-xs text-stone-600 dark:text-slate-400 pl-7 leading-relaxed">
                        Use <strong>Google Authenticator</strong>, <strong>Microsoft Authenticator</strong>, <strong>Apple iOS Passwords</strong>, or <strong>Authy</strong>.
                      </p>

                      <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-slate-100 font-serif pt-1">
                        <span className="h-5 w-5 rounded-full bg-red-600 text-white flex items-center justify-center text-[11px] font-mono">2</span>
                        <span>Add Potter&apos;s House Account (Choose Method A or B)</span>
                      </div>

                      {/* Method Toggle Buttons */}
                      <div className="pl-7 flex items-center gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setSetupMode("qr")}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            setupMode === "qr"
                              ? "bg-red-600 text-white shadow-xs"
                              : "bg-stone-200 dark:bg-slate-800 text-stone-700 dark:text-slate-300 hover:bg-stone-300"
                          }`}
                        >
                          <QrCode className="h-3.5 w-3.5" />
                          <span>Method A: Scan QR Code</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setSetupMode("manual")}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            setupMode === "manual"
                              ? "bg-red-600 text-white shadow-xs"
                              : "bg-stone-200 dark:bg-slate-800 text-stone-700 dark:text-slate-300 hover:bg-stone-300"
                          }`}
                        >
                          <Key className="h-3.5 w-3.5" />
                          <span>Method B: Enter Key / Digits Manually</span>
                        </button>
                      </div>

                      {/* Method A: QR Display */}
                      {setupMode === "qr" && (
                        <div className="ml-7 p-4 bg-white dark:bg-slate-900 rounded-2xl border border-stone-200 dark:border-slate-800 flex flex-col sm:flex-row items-center gap-5">
                          <div className="bg-white p-3 rounded-2xl border border-stone-200 shadow-sm shrink-0">
                            <QRCode value={qrCodeData.provisioning_uri} size={135} />
                          </div>
                          <div className="space-y-1.5 text-xs text-stone-600 dark:text-slate-400">
                            <p className="font-bold text-slate-900 dark:text-slate-100">Scan with your phone camera:</p>
                            <p className="leading-relaxed">
                              In your authenticator app, tap <strong>&quot;+&quot;</strong> → select <strong>&quot;Scan a QR code&quot;</strong>, then point your camera at this code.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Method B: Manual Digits / Secret Key */}
                      {setupMode === "manual" && (
                        <div className="ml-7 p-4 bg-white dark:bg-slate-900 rounded-2xl border border-stone-200 dark:border-slate-800 space-y-3">
                          <div className="text-xs space-y-1">
                            <p className="font-bold text-slate-900 dark:text-slate-100">If you cannot scan, enter these details manually:</p>
                            <p className="text-stone-500 dark:text-slate-400">In your app, tap <strong>&quot;+&quot;</strong> → select <strong>&quot;Enter a setup key&quot;</strong>:</p>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                            <div className="p-2.5 bg-stone-50 dark:bg-slate-950 rounded-xl border border-stone-200 dark:border-slate-800">
                              <span className="text-[10px] uppercase font-bold text-stone-400 block">Account Name:</span>
                              <span className="font-semibold text-slate-800 dark:text-slate-200">Potter&apos;s House (SC054652)</span>
                            </div>
                            <div className="p-2.5 bg-stone-50 dark:bg-slate-950 rounded-xl border border-stone-200 dark:border-slate-800">
                              <span className="text-[10px] uppercase font-bold text-stone-400 block">Key Type:</span>
                              <span className="font-semibold text-slate-800 dark:text-slate-200">Time-based (Standard)</span>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <span className="text-[10px] uppercase font-bold text-stone-500 dark:text-slate-400 block">Your Secret Setup Key:</span>
                            <div className="flex items-center gap-2">
                              <code className="flex-1 bg-stone-50 dark:bg-slate-950 text-red-700 dark:text-amber-400 px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold tracking-widest break-all border border-stone-200 dark:border-slate-800 select-all">
                                {formatSecretInGroups(qrCodeData.secret)}
                              </code>
                              <button 
                                type="button"
                                onClick={copyToClipboard}
                                className="p-2.5 bg-stone-100 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl text-stone-700 dark:text-slate-200 hover:bg-amber-500/10 hover:text-amber-700 transition-colors shadow-xs"
                                title="Copy secret key to clipboard"
                              >
                                {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                              </button>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Step 3: Enter 6-Digit Code */}
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-slate-100 font-serif pt-2">
                        <span className="h-5 w-5 rounded-full bg-red-600 text-white flex items-center justify-center text-[11px] font-mono">3</span>
                        <span>Enter the 6-digit code shown on your phone</span>
                      </div>

                      <div className="pl-7 space-y-3">
                        <div className="flex flex-col sm:flex-row gap-3">
                          <input
                            type="text"
                            maxLength={6}
                            placeholder="123456"
                            value={totpCode}
                            onChange={(e) => setTotpCode(e.target.value)}
                            className="flex-1 bg-white dark:bg-slate-900 border border-amber-500/60 rounded-xl px-4 py-2.5 text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-amber-500/20 text-slate-900 dark:text-white shadow-xs"
                          />
                          <button
                            type="button"
                            onClick={handleEnable2FA}
                            disabled={loading || totpCode.trim().length < 6}
                            className="royal-btn-crimson font-bold px-5 py-2.5 rounded-xl text-xs sm:text-sm transition-all shadow-md disabled:opacity-50 flex items-center justify-center gap-2 active:scale-[0.98]"
                          >
                            <span>{loading ? "Verifying Code..." : "Activate 2-Step Verification"}</span>
                            <ArrowRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                    </div>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={handleGenerate2FA}
                    disabled={loading}
                    className="border border-stone-200 dark:border-slate-800 hover:border-amber-500 dark:hover:border-amber-500 bg-white dark:bg-slate-900/60 px-5 py-4 rounded-2xl flex items-center justify-between w-full group transition-all shadow-xs"
                  >
                    <div className="flex items-center gap-3.5 text-left">
                      <div className="p-2.5 bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 rounded-xl group-hover:bg-red-50 dark:group-hover:bg-red-950/20 transition-colors">
                        <Smartphone className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 font-serif">Set Up 2-Step Verification</p>
                        <p className="text-[11px] text-stone-500 dark:text-slate-400">Connect Google Authenticator or Microsoft Authenticator</p>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-red-600 dark:text-amber-400 group-hover:translate-x-0.5 transition-transform">Configure Setup &rarr;</span>
                  </button>
                )}
              </div>

              <div className="h-px bg-stone-200/80 dark:border-slate-800 w-full" />

              {/* Password Change Section */}
              <div className="space-y-4">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base flex items-center gap-2 font-serif">
                    <Lock className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    <span>Change Password</span>
                  </h3>
                  {user?.totp_enabled && (
                    <p className="text-[11px] text-amber-800 dark:text-amber-400 mt-1 flex items-center gap-1">
                      <ShieldCheck className="h-3.5 w-3.5" /> 2-Step verification code is required to change your password.
                    </p>
                  )}
                </div>

                <form onSubmit={handleChangePassword} className="space-y-3.5 bg-stone-50/60 dark:bg-slate-950/40 p-4 sm:p-5 rounded-2xl border border-stone-200 dark:border-slate-800 text-xs">
                  <div className="grid gap-3.5 md:grid-cols-2">
                    <div className="md:col-span-2 space-y-1">
                      <label className="text-xs font-bold text-stone-700 dark:text-slate-300 block">Current Password</label>
                      <input
                        type="password"
                        required
                        value={currentPassword}
                        onChange={e => setCurrentPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-amber-500 shadow-xs"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-stone-700 dark:text-slate-300 block">New Password</label>
                      <input
                        type="password"
                        required
                        placeholder="At least 8 characters"
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-amber-500 shadow-xs"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-stone-700 dark:text-slate-300 block">Confirm New Password</label>
                      <input
                        type="password"
                        required
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-900 border border-stone-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-amber-500 shadow-xs"
                      />
                    </div>
                    
                    {user?.totp_enabled && (
                      <div className="md:col-span-2 border-t border-stone-200 dark:border-slate-800 pt-3 mt-1 space-y-1">
                        <label className="text-xs font-bold text-stone-700 dark:text-slate-300 block">6-Digit Authenticator App Code</label>
                        <input
                          type="text"
                          required
                          maxLength={6}
                          placeholder="123456"
                          value={pwdTotpCode}
                          onChange={e => setPwdTotpCode(e.target.value)}
                          className="w-full bg-white dark:bg-slate-900 border border-amber-500/60 rounded-xl px-3.5 py-2 text-xs font-mono tracking-widest focus:outline-none focus:border-amber-600 shadow-xs"
                        />
                      </div>
                    )}
                  </div>
                  
                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="royal-btn-gold font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-xs disabled:opacity-50 flex items-center gap-2 active:scale-[0.98]"
                    >
                      <span>{loading ? "Updating..." : "Update Password"}</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};
