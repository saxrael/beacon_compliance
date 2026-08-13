"use client";

import React, { useState } from "react";
import { ShieldCheck, UserCheck, Sun, Moon, LogOut, UserPlus, Menu, HelpCircle } from "lucide-react";
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
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 flex flex-col transition-colors duration-300">
      <div className="h-1 bg-gradient-to-r from-red-600 via-yellow-400 to-red-600 w-full"></div>
      <div className="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="tour-menu-btn p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center"
            aria-label="Open Menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          
          <div className="tour-header-logo h-12 w-auto min-w-[3rem] px-2 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-center shadow-md">
            <img
              src={theme === "dark" ? "/assets/logo_dark.png" : "/assets/logo.png"}
              alt="Potter's House Logo"
              className="h-9 w-auto object-contain"
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
            <ShieldCheck className="h-7 w-7 text-red-500 hidden" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-50">Beacon Compliance OS</h1>
              <span className="bg-red-500/10 text-red-700 dark:text-yellow-400 border border-red-500/30 dark:border-yellow-500/30 text-xs font-mono px-2 py-0.5 rounded-full font-semibold">
                SC054652
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Potter&apos;s House Christian Mission UK (SCIO, Dunbar, Scotland)
            </p>
            <p className="text-[11px] italic text-slate-500 dark:text-slate-400/90 mt-0.5">
              &quot;Building Lives, Strengthening Homes, Shaping Nations for Christ&quot;
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {isAdminOrDev && onOpenAdminModal && (
            <button
              onClick={onOpenAdminModal}
              className="flex items-center gap-1.5 bg-slate-800 dark:bg-slate-800 text-yellow-400 border border-slate-700 font-bold px-3 py-1.5 rounded-lg text-xs hover:bg-slate-700 transition-colors shadow-md"
            >
              <UserPlus className="h-4 w-4" />
              <span>Provision Trustees</span>
            </button>
          )}

          <button
            onClick={startProductTour}
            aria-label="Start Product Tour"
            title="Help & Tour"
            className="tour-help-btn flex items-center justify-center h-8 w-8 rounded-full bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors"
          >
            <HelpCircle className="h-4 w-4" />
          </button>

          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="tour-theme-btn flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:border-red-500 transition-all active:scale-95"
          >
            {theme === "dark" ? (
              <>
                <Sun className="h-4 w-4 text-yellow-400" />
                <span className="font-medium">Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="h-4 w-4 text-slate-700" />
                <span className="font-medium">Dark Mode</span>
              </>
            )}
          </button>

          {user && (
            <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300">
              <UserCheck className="h-4 w-4 text-red-600 dark:text-yellow-400" />
              <div className="flex flex-col">
                <span className="font-semibold text-slate-900 dark:text-slate-100">{user.name}</span>
                <span className="text-[10px] text-red-600 dark:text-yellow-400 font-mono uppercase font-bold">{userRole}</span>
              </div>
              <button
                onClick={logout}
                title="Log Out"
                className="ml-2 text-slate-400 hover:text-red-500 transition-colors p-1"
              >
                <LogOut className="h-4 w-4" />
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
