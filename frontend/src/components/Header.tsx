"use client";

import React, { useState } from "react";
import { Sun, Moon, LogOut, UserPlus, Menu, HelpCircle, Landmark, ShieldCheck } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";
import { SidebarMenu } from "./SidebarMenu";
import { AccountSettingsModal, getInitials } from "./AccountSettingsModal";
import { startProductTour } from "@/utils/ProductTour";
import { motion } from "framer-motion";

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
    <header className="border-b border-stone-200/80 dark:border-slate-800/80 bg-white/95 dark:bg-[#080C14]/95 backdrop-blur-xl sticky top-0 z-40 flex flex-col transition-colors duration-300 shadow-xs w-full max-w-[100vw]">
      <div className="h-1 gold-ribbon w-full" />
      
      <div className="max-w-7xl w-full mx-auto px-3 sm:px-6 py-2 sm:py-3 flex items-center justify-between gap-2 sm:gap-4">
        {/* Left: Brand Identity & Masthead */}
        <div className="flex items-center gap-2 sm:gap-3.5 min-w-0">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="tour-menu-btn p-2 rounded-xl text-stone-600 hover:text-stone-900 dark:text-slate-300 dark:hover:text-amber-300 hover:bg-stone-100 dark:hover:bg-slate-800/60 transition-all flex items-center justify-center shrink-0 active:scale-95"
            aria-label="Open Navigation Menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <div className="tour-header-logo flex items-center justify-center shrink-0">
              <img
                src={theme === "dark" ? "/assets/logo_dark.png" : "/assets/logo.png"}
                alt="Potter's House Crest"
                className="h-7 sm:h-9 w-auto max-w-[95px] sm:max-w-[180px] object-contain drop-shadow-xs"
                onError={(e) => { 
                  (e.target as HTMLElement).style.display = 'none'; 
                }}
              />
            </div>

            <div className="hidden sm:block h-6 w-px bg-stone-200 dark:bg-slate-800/80 shrink-0" />

            <div className="min-w-0">
              <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                <h1 className="text-sm sm:text-base md:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100 font-serif truncate">
                  Beacon Compliance
                </h1>
                <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-900 dark:text-amber-300 border border-amber-500/25 text-[9.5px] sm:text-[10px] font-mono px-1.5 sm:px-2 py-0.5 rounded-md font-semibold shrink-0">
                  <Landmark className="h-2.5 w-2.5 sm:h-3 sm:w-3 text-amber-700 dark:text-amber-400" />
                  SC054652
                </span>
              </div>
              <p className="text-[10px] sm:text-[11px] font-medium text-stone-500 dark:text-slate-400 leading-tight truncate hidden xs:block">
                Potter&apos;s House Christian Mission UK <span className="hidden md:inline">• Dunbar, Scotland</span>
              </p>
            </div>
          </div>
        </div>

        {/* Right: Integrated Control Toolbar */}
        <div className="flex items-center gap-1 sm:gap-2 shrink-0">
          {isAdminOrDev && onOpenAdminModal && (
            <button
              onClick={onOpenAdminModal}
              className="hidden md:flex items-center gap-1.5 royal-btn-crimson font-semibold px-3 py-1.5 rounded-xl text-xs transition-all shadow-xs mr-0.5"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span>Register Trustee</span>
            </button>
          )}

          <button
            onClick={startProductTour}
            aria-label="Start Product Tour"
            title="Interactive Compliance Guide"
            className="tour-help-btn flex items-center gap-1.5 p-2 sm:px-2.5 sm:py-1.5 rounded-xl text-stone-600 dark:text-slate-300 hover:text-amber-700 dark:hover:text-amber-400 hover:bg-stone-100 dark:hover:bg-slate-800/60 text-xs font-semibold transition-all active:scale-95"
          >
            <HelpCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0" />
            <span className="hidden md:inline">Guided Tour</span>
          </button>

          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="tour-theme-btn p-2 rounded-xl text-stone-600 dark:text-slate-300 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-stone-100 dark:hover:bg-slate-800/60 transition-all active:scale-95 shrink-0"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-amber-400" />
            ) : (
              <Moon className="h-4 w-4 text-stone-700" />
            )}
          </button>

          <div className="h-5 w-px bg-stone-200 dark:bg-slate-800 mx-0.5 sm:mx-1 shrink-0" />

          {user && (
            <div 
              onClick={() => setIsSettingsOpen(true)}
              title="Account & Profile Settings"
              className="flex items-center gap-1.5 sm:gap-2 p-1 sm:px-2.5 sm:py-1.5 rounded-xl hover:bg-stone-100 dark:hover:bg-slate-800/70 transition-all cursor-pointer group shrink-0"
            >
              {user.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name || "Trustee"}
                  className="h-7 w-7 rounded-full object-cover border border-amber-500/50 shadow-xs ring-1 ring-amber-500/20 shrink-0"
                />
              ) : (
                <div className="h-7 w-7 rounded-full bg-gradient-to-br from-red-700 via-red-600 to-amber-600 text-white font-bold flex items-center justify-center text-[10px] shadow-xs border border-amber-500/40 shrink-0">
                  {getInitials(user.name || "")}
                </div>
              )}
              <div className="hidden sm:flex flex-col text-left">
                <span className="font-semibold text-stone-900 dark:text-slate-100 text-xs leading-tight group-hover:text-amber-700 dark:group-hover:text-amber-300 transition-colors">
                  {user.name}
                </span>
                <span className="text-[9.5px] text-red-700 dark:text-amber-400 uppercase font-bold tracking-wider">{userRole}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  logout();
                }}
                title="Log Out"
                className="text-stone-400 hover:text-red-600 dark:hover:text-red-400 transition-colors p-1 rounded-md ml-0.5 hidden xs:block"
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

