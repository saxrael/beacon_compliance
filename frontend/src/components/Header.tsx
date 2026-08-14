"use client";

import React, { useState } from "react";
import { ShieldCheck, UserCheck, Sun, Moon, LogOut, UserPlus, Menu, HelpCircle, Sparkles } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";
import { SidebarMenu } from "./SidebarMenu";
import { AccountSettingsModal } from "./AccountSettingsModal";
import { startProductTour } from "@/utils/ProductTour";

interface HeaderProps {
  onOpenAdminModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenAdminModal }) => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const userRole = user?.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1).toLowerCase()) : "Trustee";
  const isAdminOrDev = userRole === "Developer" || userRole === "Admin";

  return (
    <header className="border-b border-stone-200 dark:border-slate-800/80 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md sticky top-0 z-40 flex flex-col transition-colors duration-300 shadow-sm">
      <div className="h-1 bg-gradient-to-r from-red-600 via-amber-500 to-red-600 w-full" />
      
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="tour-menu-btn p-2 rounded-xl bg-stone-100 dark:bg-slate-800 text-stone-700 dark:text-slate-300 hover:bg-stone-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center border border-stone-200 dark:border-slate-700/60"
              aria-label="Open Navigation Menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            
            <div className="tour-header-logo h-11 px-2.5 rounded-xl bg-stone-50 dark:bg-slate-950 border border-stone-200 dark:border-slate-800 flex items-center justify-center shadow-xs">
              <img
                src={theme === "dark" ? "/assets/logo_dark.png" : "/assets/logo.png"}
                alt="Potter's House Crest"
                className="h-8 max-h-8 w-auto object-contain"
                onError={(e) => { 
                  (e.target as HTMLElement).style.display = 'none'; 
                }}
              />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-50 font-serif">
                  Beacon Compliance
                </h1>
                <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-500/30 text-[11px] font-mono px-2 py-0.5 rounded-full font-semibold">
                  <Sparkles className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                  SC054652
                </span>
              </div>
              <p className="text-xs font-medium text-stone-600 dark:text-slate-400">
                Potter&apos;s House Christian Mission UK <span className="hidden sm:inline">• Dunbar, Scotland</span>
              </p>
              <p className="text-[11px] italic text-stone-500 dark:text-slate-400/90 hidden lg:block">
                &quot;Building Lives, Strengthening Homes, Shaping Nations for Christ&quot;
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap justify-end w-full md:w-auto">
          {isAdminOrDev && onOpenAdminModal && (
            <button
              onClick={onOpenAdminModal}
              className="flex items-center gap-1.5 bg-stone-100 hover:bg-stone-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-stone-800 dark:text-amber-300 border border-stone-300 dark:border-slate-700 font-semibold px-3 py-1.5 rounded-xl text-xs transition-colors shadow-xs"
            >
              <UserPlus className="h-3.5 w-3.5 text-red-600 dark:text-amber-400" />
              <span>Provision Trustees</span>
            </button>
          )}

          <button
            onClick={startProductTour}
            aria-label="Start Product Tour"
            title="Interactive Compliance Guide"
            className="tour-help-btn flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 text-xs font-semibold transition-colors"
          >
            <HelpCircle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Guide Tour</span>
          </button>

          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="tour-theme-btn flex items-center gap-1.5 bg-stone-100 dark:bg-slate-800 border border-stone-300 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs font-medium text-stone-700 dark:text-slate-300 hover:border-amber-500 transition-all active:scale-95 shadow-xs"
          >
            {theme === "dark" ? (
              <>
                <Sun className="h-3.5 w-3.5 text-amber-400" />
                <span>Light</span>
              </>
            ) : (
              <>
                <Moon className="h-3.5 w-3.5 text-stone-700" />
                <span>Dark</span>
              </>
            )}
          </button>

          {user && (
            <div className="flex items-center gap-2 bg-stone-100/80 dark:bg-slate-800/80 border border-stone-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs shadow-xs">
              <div className="h-7 w-7 rounded-lg bg-red-600/10 text-red-700 dark:text-amber-400 font-bold flex items-center justify-center text-xs border border-red-600/20">
                {user.name ? user.name.charAt(0).toUpperCase() : "T"}
              </div>
              <div className="flex flex-col text-left">
                <span className="font-semibold text-stone-900 dark:text-slate-100 leading-tight">{user.name}</span>
                <span className="text-[10px] text-red-600 dark:text-amber-400 font-mono uppercase font-bold tracking-wider">{userRole}</span>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="ml-1 text-stone-400 hover:text-red-600 dark:hover:text-red-400 transition-colors p-1 rounded-md"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      <SidebarMenu 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)} 
        onOpenSettings={() => setIsSettingsOpen(true)}
        onStartTour={startProductTour}
      />

      {isSettingsOpen && (
        <AccountSettingsModal onClose={() => setIsSettingsOpen(false)} />
      )}
    </header>
  );
};
