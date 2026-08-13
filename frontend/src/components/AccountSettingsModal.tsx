"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { X, Shield, Lock, Key, Copy, Check, ShieldAlert, ShieldCheck, Mail, User, Settings } from "lucide-react";
import QRCode from "react-qr-code";

interface AccountSettingsModalProps {
  onClose: () => void;
}

export const AccountSettingsModal: React.FC<AccountSettingsModalProps> = ({ onClose }) => {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");
  

  const [setup2FA, setSetup2FA] = useState(false);
  const [qrCodeData, setQrCodeData] = useState<any>(null);
  const [totpCode, setTotpCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);


  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwdTotpCode, setPwdTotpCode] = useState("");

  const handleGenerate2FA = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch("http:
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to generate 2FA secret");
      const data = await res.json();
      setQrCodeData(data);
      setSetup2FA(true);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEnable2FA = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch("http:
        method: "POST",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ totp_code: totpCode })
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to verify 2FA code");
      }
      
      setSuccessMsg("Two-factor authentication successfully enabled.");
      setSetup2FA(false);
      setQrCodeData(null);

      setTimeout(() => window.location.reload(), 2000);
    } catch (err: any) {
      setErrorMsg(err.message);
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
    
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch("http:
        method: "POST",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          totp_code: user?.totp_enabled ? pwdTotpCode : undefined
        })
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to change password");
      }
      
      setSuccessMsg("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPwdTotpCode("");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message);
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-700 dark:text-slate-300">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">Account Settings</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">Manage your profile and security preferences</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        {}
        <div className="flex border-b border-slate-100 dark:border-slate-800 px-6">
          <button 
            onClick={() => {setActiveTab("profile"); setErrorMsg(null); setSuccessMsg(null);}}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === "profile" ? "border-red-500 text-red-600 dark:text-red-400" : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"}`}
          >
            Profile
          </button>
          <button 
            onClick={() => {setActiveTab("security"); setErrorMsg(null); setSuccessMsg(null);}}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === "security" ? "border-red-500 text-red-600 dark:text-red-400" : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"}`}
          >
            Security & Login
          </button>
        </div>

        {}
        <div className="p-6 overflow-y-auto flex-1">
          {errorMsg && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-xs rounded-lg flex items-start gap-2">
              <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}
          {successMsg && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20 text-green-600 dark:text-green-400 text-xs rounded-lg flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {activeTab === "profile" && (
            <div className="space-y-6">
              <div className="flex items-center gap-4 p-4 border border-slate-100 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-950">
                <div className="h-16 w-16 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-500 rounded-full flex items-center justify-center text-xl font-bold">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-lg">{user?.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="bg-red-500/10 text-red-600 dark:text-yellow-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full uppercase">
                      {user?.role}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid gap-1">
                  <label className="text-xs font-semibold text-slate-500 flex items-center gap-1.5"><Mail className="h-3.5 w-3.5"/> Email Address</label>
                  <div className="px-3 py-2.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-700 dark:text-slate-300 text-sm">
                    {user?.email}
                  </div>
                </div>
                <div className="grid gap-1">
                  <label className="text-xs font-semibold text-slate-500 flex items-center gap-1.5"><User className="h-3.5 w-3.5"/> Full Name</label>
                  <div className="px-3 py-2.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-700 dark:text-slate-300 text-sm">
                    {user?.name}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-8">
              {}
              <div className="space-y-4">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-slate-400" />
                    Two-Factor Authentication (2FA)
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Add an extra layer of security to your account by requiring a code from an authenticator app.
                  </p>
                </div>

                {user?.totp_enabled && !setup2FA ? (
                  <div className="p-4 border border-green-200 dark:border-green-900/50 bg-green-50 dark:bg-green-500/10 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 rounded-full">
                        <ShieldCheck className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-green-800 dark:text-green-300">2FA is Enabled</p>
                        <p className="text-xs text-green-600 dark:text-green-500">Your account is secured with TOTP.</p>
                      </div>
                    </div>
                  </div>
                ) : setup2FA && qrCodeData ? (
                  <div className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl space-y-5 bg-slate-50 dark:bg-slate-950/50">
                    <div className="flex flex-col sm:flex-row gap-6 items-center sm:items-start">
                      <div className="bg-white p-3 rounded-xl border shadow-sm">
                        <QRCode value={qrCodeData.provisioning_uri} size={140} />
                      </div>
                      <div className="space-y-3 flex-1 w-full">
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Scan this QR Code</h4>
                        <p className="text-xs text-slate-500 leading-relaxed">
                          Scan the QR code with your authenticator app (e.g., Google Authenticator, Authy, or Microsoft Authenticator).
                        </p>
                        <div className="pt-2">
                          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Or enter setup key manually</p>
                          <div className="flex items-center gap-2">
                            <code className="flex-1 bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-300 px-3 py-2 rounded-lg text-xs font-mono font-bold tracking-widest break-all border border-slate-200 dark:border-slate-800">
                              {qrCodeData.secret}
                            </code>
                            <button 
                              onClick={copyToClipboard}
                              className="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors"
                              title="Copy setup key"
                            >
                              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-slate-200 dark:border-slate-800 pt-5">
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2 block">
                        Verify Code to Enable
                      </label>
                      <div className="flex gap-3">
                        <input
                          type="text"
                          maxLength={6}
                          placeholder="123456"
                          value={totpCode}
                          onChange={(e) => setTotpCode(e.target.value)}
                          className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-4 py-2.5 text-sm font-mono tracking-widest focus:outline-none focus:border-red-500 transition-colors"
                        />
                        <button
                          onClick={handleEnable2FA}
                          disabled={loading || totpCode.length < 6}
                          className="bg-red-600 hover:bg-red-700 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50"
                        >
                          {loading ? "Verifying..." : "Enable 2FA"}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={handleGenerate2FA}
                    disabled={loading}
                    className="border border-slate-200 dark:border-slate-800 hover:border-red-500 dark:hover:border-red-500 bg-white dark:bg-slate-900 px-4 py-3 rounded-xl flex items-center justify-between w-full group transition-all"
                  >
                    <div className="flex items-center gap-3 text-left">
                      <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-full group-hover:bg-red-50 dark:group-hover:bg-red-900/20 transition-colors">
                        <Shield className="h-4 w-4 text-slate-500 group-hover:text-red-500" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">Set Up 2FA</p>
                        <p className="text-[11px] text-slate-500">Not currently enabled</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-red-600 dark:text-red-400">Configure</span>
                  </button>
                )}
              </div>

              <div className="h-px bg-slate-100 dark:bg-slate-800 w-full" />

              {}
              <div className="space-y-4">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-slate-400" />
                    Change Password
                  </h3>
                  {user?.totp_enabled && (
                    <p className="text-[11px] text-yellow-600 dark:text-yellow-500 mt-1 flex items-center gap-1">
                      <ShieldCheck className="h-3 w-3" /> 2FA is required to change your password.
                    </p>
                  )}
                </div>

                <form onSubmit={handleChangePassword} className="space-y-3 bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="md:col-span-2">
                      <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1">Current Password</label>
                      <input
                        type="password"
                        required
                        value={currentPassword}
                        onChange={e => setCurrentPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1">New Password</label>
                      <input
                        type="password"
                        required
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1">Confirm New Password</label>
                      <input
                        type="password"
                        required
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500"
                      />
                    </div>
                    
                    {user?.totp_enabled && (
                      <div className="md:col-span-2 border-t border-slate-200 dark:border-slate-800 pt-3 mt-1">
                        <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 block mb-1">2FA Authenticator Code</label>
                        <input
                          type="text"
                          required
                          maxLength={6}
                          placeholder="123456"
                          value={pwdTotpCode}
                          onChange={e => setPwdTotpCode(e.target.value)}
                          className="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm font-mono tracking-widest focus:outline-none focus:border-red-500"
                        />
                      </div>
                    )}
                  </div>
                  
                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 text-white font-semibold px-5 py-2 rounded-lg text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      <Key className="h-4 w-4" />
                      {loading ? "Updating..." : "Update Password"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
