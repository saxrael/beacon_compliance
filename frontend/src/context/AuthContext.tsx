"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export interface UserProfile {
  user_id: string;
  email: string;
  name: string;
  role: string;
  first_login_complete: boolean;
  google_linked: boolean;
  totp_enabled?: boolean;
}

export interface LoginResult {
  user?: UserProfile;
  requires_2fa?: boolean;
  tempToken?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  token: string | null;
  error: string | null;
  loginWithEmail: (email: string, password: string) => Promise<LoginResult>;
  loginWith2FA: (tempToken: string, code: string) => Promise<UserProfile>;
  loginWithGoogle: (code: string, state?: string) => Promise<UserProfile>;
  getGoogleLoginUrl: () => Promise<string>;
  completeFirstLoginReset: (email: string, currentPassword: string, newPassword: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = "http://localhost:8000/api/auth";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {

    const storedToken = localStorage.getItem("beacon_auth_token");
    if (storedToken) {
      setToken(storedToken);
      fetchUserProfile(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async (authToken: string) => {
    try {
      const res = await fetch(`${API_BASE}/me`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (res.ok) {
        const profile = await res.json();
        setUser(profile);
      } else {
        localStorage.removeItem("beacon_auth_token");
        setToken(null);
        setUser(null);
      }
    } catch (err) {
      console.error("Failed to fetch user profile:", err);
    } finally {
      setLoading(false);
    }
  };

  const loginWithEmail = async (email: string, password: string): Promise<LoginResult> => {
    setError(null);
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "Authentication failed. Invalid email or password.";
      setError(msg);
      throw new Error(msg);
    }

    const data = await res.json();
    if (data.requires_2fa) {
      return { requires_2fa: true, tempToken: data.access_token, user: data.user };
    }
    
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("beacon_auth_token", data.access_token);
    return { user: data.user };
  };

  const loginWith2FA = async (tempToken: string, totpCode: string): Promise<UserProfile> => {
    setError(null);
    const res = await fetch(`${API_BASE}/login/2fa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ temp_token: tempToken, totp_code: totpCode }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "Invalid 2FA code.";
      setError(msg);
      throw new Error(msg);
    }

    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("beacon_auth_token", data.access_token);
    return data.user;
  };

  const getGoogleLoginUrl = async (): Promise<string> => {
    const res = await fetch(`${API_BASE}/google/login`);
    if (!res.ok) {
      throw new Error("Failed to initiate Google OAuth login.");
    }
    const data = await res.json();
    return data.auth_url;
  };

  const loginWithGoogle = async (code: string, state?: string): Promise<UserProfile> => {
    setError(null);
    const url = `${API_BASE}/google/callback?code=${encodeURIComponent(code)}${state ? `&state=${encodeURIComponent(state)}` : ""}`;
    const res = await fetch(url);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "Google OAuth sign-in failed. Email is not pre-provisioned.";
      setError(msg);
      throw new Error(msg);
    }

    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("beacon_auth_token", data.access_token);
    return data.user;
  };

  const completeFirstLoginReset = async (email: string, currentPassword: string, newPassword: string) => {
    setError(null);
    const res = await fetch(`${API_BASE}/first-login-reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, current_password: currentPassword, new_password: newPassword }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || "Password reset failed.";
      setError(msg);
      throw new Error(msg);
    }

    const updatedProfile = await res.json();
    setUser(updatedProfile);
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/logout`, { method: "POST" });
    } catch (e) {

    } finally {
      localStorage.removeItem("beacon_auth_token");
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        token,
        error,
        loginWithEmail,
        loginWith2FA,
        loginWithGoogle,
        getGoogleLoginUrl,
        completeFirstLoginReset,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
