"use client";

import React from "react";
import { ShieldCheck, UserCheck, Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

interface HeaderProps {
  currentRole: string;
  onRoleChange: (role: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentRole, onRoleChange }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 flex flex-col transition-colors duration-300">
      <div className="h-1 bg-gradient-to-r from-red-600 via-yellow-400 to-red-600 w-full"></div>
      <div className="px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="h-12 w-auto min-w-[3rem] px-2 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-center shadow-md">
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
              Potter's House Christian Mission UK (SCIO, Dunbar, Scotland)
            </p>
            <p className="text-[11px] italic text-slate-500 dark:text-slate-400/90 mt-0.5">
              "Building Lives, Strengthening Homes, Shaping Nations for Christ"
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 hover:border-red-500 transition-all active:scale-95"
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

          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300">
            <UserCheck className="h-4 w-4 text-red-600 dark:text-yellow-400" />
            <label htmlFor="trustee-role-select" className="text-slate-500 dark:text-slate-400 font-medium">Active Trustee Role:</label>
            <select
              id="trustee-role-select"
              aria-label="Active Trustee Role"
              value={currentRole}
              onChange={(e) => onRoleChange(e.target.value)}
              className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-yellow-400 text-xs font-semibold rounded px-2 py-1 focus:outline-none focus:border-red-500"
            >
              <option value="chair">Chair</option>
              <option value="treasurer">Treasurer</option>
              <option value="secretary">Secretary</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
