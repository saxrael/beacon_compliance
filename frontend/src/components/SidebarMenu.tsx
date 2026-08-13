"use client";

import React from "react";
import { User, Settings, ShieldCheck, LogOut, X, HelpCircle, ShieldAlert } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

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

  if (!isOpen) return null;

  return (
    <>
      {}
      <div 
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm z-50 transition-opacity"
        onClick={onClose}
      />
      
      {}
      <div className="fixed inset-y-0 left-0 w-72 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 z-50 shadow-2xl flex flex-col transform transition-transform duration-300">
        <div className="h-1 bg-gradient-to-r from-red-600 via-yellow-400 to-red-600 w-full" />
        
        {}
        <div className="p-4 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/50">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-red-600 dark:text-red-500" />
            <h2 className="font-bold text-slate-900 dark:text-slate-50">Menu</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/30">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-500 flex items-center justify-center font-bold text-lg border border-red-200 dark:border-red-500/20">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <p className="font-bold text-slate-900 dark:text-slate-100 truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span className="bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase">
              {user?.role}
            </span>
            {user?.totp_enabled ? (
              <span className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> 2FA ON
              </span>
            ) : (
              <span className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded flex items-center gap-1">
                <ShieldAlert className="h-3 w-3" /> 2FA OFF
              </span>
            )}
          </div>
        </div>

        {}
        <div className="p-3 flex-1 overflow-y-auto space-y-1">
          <button 
            onClick={() => {
              onClose();
              onOpenSettings();
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Settings className="h-4 w-4 text-slate-400" />
            Account Settings
          </button>
          
          <button 
            onClick={() => {
              onClose();
              onStartTour();
            }}
            className="tour-start-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <HelpCircle className="h-4 w-4 text-slate-400" />
            Interactive Tour
          </button>
          
          <div className="h-px bg-slate-100 dark:bg-slate-800/50 my-2 mx-2" />
          
          <div className="px-3 py-2">
            <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">Support</p>
            <a 
              href="mailto:system.admin@pottershouse.org.uk"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <User className="h-4 w-4 text-slate-400" />
              Contact Administrator
            </a>
          </div>
        </div>

        {}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800/50">
          <button 
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-lg text-sm font-bold transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </>
  );
};
