"use client";

import React from "react";
import { User, Settings, ShieldCheck, LogOut, X, HelpCircle, ShieldAlert, Landmark, FileText, UploadCloud, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";

interface SidebarMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
  onStartTour: () => void;
}

export const SidebarMenu: React.FC<SidebarMenuProps> = ({ 
  isOpen, 
  onClose, 
  onOpenSettings,
  onStartTour
}) => {
  const { user, logout } = useAuth();
  const userRole = user?.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1).toLowerCase()) : "Trustee";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          
          {/* Sliding Panel */}
          <motion.div 
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={springs.gentle}
            className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-white dark:bg-[#0B0F19] border-r border-stone-200 dark:border-slate-800 z-50 shadow-2xl flex flex-col justify-between overflow-hidden"
          >
            {/* Top Gold Ribbon Accent */}
            <div className="h-1.5 gold-ribbon w-full" />
            
            {/* Header with Crest Branding */}
            <div className="p-5 border-b border-stone-200/80 dark:border-slate-800 flex items-center justify-between bg-stone-50/60 dark:bg-slate-900/40">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-stone-100 dark:bg-slate-900 border border-stone-200 dark:border-slate-800 flex items-center justify-center p-1 shadow-xs overflow-hidden">
                  <img
                    src="/assets/logo_mark.png"
                    alt="Potter's House Emblem"
                    className="h-full w-full object-contain"
                  />
                </div>
                <div>
                  <h2 className="font-serif font-bold text-slate-900 dark:text-slate-50 text-base leading-tight">
                    Trustee Navigation
                  </h2>
                  <p className="text-[11px] font-mono text-amber-700 dark:text-amber-400 font-semibold">
                    Scottish Charity SC054652
                  </p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-1.5 text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 rounded-xl hover:bg-stone-200/60 dark:hover:bg-slate-800 transition-colors"
                aria-label="Close Menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Trustee Profile Card */}
            <div className="p-5 border-b border-stone-200/80 dark:border-slate-800 bg-stone-100/50 dark:bg-slate-900/30">
              <div className="flex items-center gap-3.5">
                <div className="h-11 w-11 rounded-2xl bg-gradient-to-br from-red-600 to-amber-600 text-white flex items-center justify-center font-serif font-bold text-lg shadow-sm">
                  {user?.name?.charAt(0).toUpperCase() || "T"}
                </div>
                <div className="overflow-hidden flex-1">
                  <p className="font-bold text-slate-900 dark:text-slate-100 text-sm truncate">{user?.name || "Authorized Trustee"}</p>
                  <p className="text-xs text-stone-500 dark:text-slate-400 truncate">{user?.email || "trustee@pottershouse.org.uk"}</p>
                </div>
              </div>
              <div className="mt-3.5 flex items-center gap-2">
                <span className="bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-500/30 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  {userRole}
                </span>
                {user?.totp_enabled ? (
                  <span className="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 text-emerald-600 dark:text-emerald-400" /> 2-Step Active
                  </span>
                ) : (
                  <span className="bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <ShieldAlert className="h-3 w-3 text-amber-600" /> 2-Step Recommended
                  </span>
                )}
              </div>
            </div>

            {/* Menu Items */}
            <div className="p-3.5 flex-1 overflow-y-auto space-y-1.5">
              <div className="px-3 py-1.5">
                <p className="text-[10px] font-bold text-stone-400 dark:text-slate-500 uppercase tracking-widest">
                  Compliance & Account
                </p>
              </div>

              <button 
                onClick={() => {
                  onClose();
                  onOpenSettings();
                }}
                className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-stone-100 dark:hover:bg-slate-800/80 transition-all hover:translate-x-1"
              >
                <Settings className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                <span>Account & Security Settings</span>
              </button>
              
              <button 
                onClick={() => {
                  onClose();
                  onStartTour();
                }}
                className="tour-start-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-stone-100 dark:hover:bg-slate-800/80 transition-all hover:translate-x-1"
              >
                <HelpCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0" />
                <span>Interactive Guided Tour</span>
              </button>

              <div className="h-px bg-stone-200/80 dark:bg-slate-800 my-3 mx-2" />
              
              <div className="px-3 py-1.5">
                <p className="text-[10px] font-bold text-stone-400 dark:text-slate-500 uppercase tracking-widest">
                  Trustee Support
                </p>
              </div>

              <a 
                href="mailto:system.admin@pottershouse.org.uk"
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-stone-100 dark:hover:bg-slate-800/80 transition-all hover:translate-x-1"
              >
                <User className="h-4 w-4 text-stone-400 shrink-0" />
                <span>Contact Charity Support</span>
              </a>

              <div className="mt-4 p-3.5 rounded-2xl bg-amber-500/5 border border-amber-500/20 text-[11px] text-stone-600 dark:text-slate-400 leading-relaxed">
                <p className="font-semibold text-amber-800 dark:text-amber-300 mb-0.5">Scottish Charity Governance Notice</p>
                All account updates and official trustee approvals are securely and permanently recorded in the charity audit log.
              </div>
            </div>

            {/* Footer Sign Out */}
            <div className="p-4 border-t border-stone-200/80 dark:border-slate-800 bg-stone-50/40 dark:bg-slate-900/40">
              <button 
                onClick={logout}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-50 dark:bg-red-950/30 hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/30 rounded-xl text-xs font-bold transition-all active:scale-[0.98]"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out of Portal</span>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
