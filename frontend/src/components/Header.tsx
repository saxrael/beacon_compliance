"use client";

import React, { useState } from "react";
import { UserCheck, Sun, Moon, LogOut, UserPlus, Menu, HelpCircle, Landmark } from "lucide-react";
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
    <header className="border-b border-stone-200/80 dark:border-slate-800 bg-white/95 dark:bg-[#070A11]/95 backdrop-blur-md sticky top-0 z-40 flex flex-col transition-colors duration-300 shadow-xs">
      <div className="h-1 gold-ribbon w-full" />
      
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="tour-menu-btn p-2 rounded-xl bg-stone-100 dark:bg-slate-800 text-stone-700 dark:text-slate-200 hover:bg-amber-500/10 hover:text-amber-700 dark:hover:text-amber-400 transition-all flex items-center justify-center border border-stone-300/80 dark:border-slate-700 active:scale-95 shadow-xs"
              aria-label="Open Navigation Menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            
            <div className="tour-header-logo flex items-center justify-center">
              <img
                src={theme === "dark" ? "/assets/logo_dark.png" : "/assets/logo.png"}
                alt="Potter's House Crest"
                className="h-9 w-auto max-w-[150px] sm:max-w-[200px] object-contain drop-shadow-xs"
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
                <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-500/30 text-[11px] font-mono px-2.5 py-0.5 rounded-full font-semibold">
                  <Landmark className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                  Scottish Charity SC054652
                </span>
              </div>
              <p className="text-xs font-medium text-stone-600 dark:text-slate-400">
                Potter&apos;s House Christian Mission UK <span className="hidden sm:inline">• Dunbar, Scotland</span>
              </p>
              <p className="text-[11px] italic text-stone-500 dark:text-slate-400/90 hidden lg:block font-editorial">
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
              <span>Register New Trustee</span>
            </button>
          )}

          <button
            onClick={startProductTour}
            aria-label="Start Product Tour"
            title="Interactive Compliance Guide"
            className="tour-help-btn flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 text-xs font-semibold transition-colors"
          >
            <HelpCircle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Guided Tour</span>
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
            <div 
              onClick={() => setIsSettingsOpen(true)}
              title="Account & Profile Settings"
              className="flex items-center gap-2 bg-stone-100/90 hover:bg-stone-200/90 dark:bg-slate-800/90 dark:hover:bg-slate-700/90 border border-stone-300/80 dark:border-slate-700 rounded-xl px-2.5 py-1.5 text-xs shadow-xs transition-all cursor-pointer group"
            >
              {user.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name || "Trustee"}
                  className="h-7 w-7 rounded-full object-cover border border-amber-500/50 shadow-xs ring-1 ring-amber-500/20"
                />
              ) : (
                <div className="h-7 w-7 rounded-full bg-gradient-to-br from-red-700 via-red-600 to-amber-600 text-white font-bold flex items-center justify-center text-[10px] shadow-xs border border-amber-500/40">
                  {getInitials(user.name || "")}
                </div>
              )}
              <div className="flex flex-col text-left">
                <span className="font-semibold text-stone-900 dark:text-slate-100 leading-tight group-hover:text-amber-700 dark:group-hover:text-amber-300 transition-colors">
                  {user.name}
                </span>
                <span className="text-[10px] text-red-600 dark:text-amber-400 uppercase font-bold tracking-wider">{userRole}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  logout();
                }}
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
