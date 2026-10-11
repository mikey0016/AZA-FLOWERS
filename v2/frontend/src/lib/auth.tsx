"use client";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export interface AuthUser {
  name: string;
  phone: string;
}

interface AuthCtx {
  user: AuthUser | null;
  token: string | null;
  login: (phone: string, password: string) => Promise<string | null>;
  register: (name: string, phone: string, password: string) => Promise<string | null>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx>({
  user: null, token: null,
  login: async () => "xatolik", register: async () => "xatolik", logout: () => {},
});

async function post(path: string, body: unknown, token?: string | null) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Token ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  return r.json();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    try {
      const t = localStorage.getItem("aza2_token");
      const u = localStorage.getItem("aza2_user");
      if (t && u) {
        setToken(t);
        setUser(JSON.parse(u));
        fetch("/api/v2/auth/me/", { headers: { Authorization: `Token ${t}` } })
          .then((r) => (r.ok ? r.json() : null))
          .then((j) => {
            if (!j) { localStorage.removeItem("aza2_token"); localStorage.removeItem("aza2_user"); setToken(null); setUser(null); }
            else if (j.name) { const nu = { name: j.name, phone: j.phone }; setUser(nu); localStorage.setItem("aza2_user", JSON.stringify(nu)); }
          })
          .catch(() => {});
      }
    } catch { /* ignore */ }
  }, []);

  const save = (t: string, u: AuthUser) => {
    setToken(t); setUser(u);
    try {
      localStorage.setItem("aza2_token", t);
      localStorage.setItem("aza2_user", JSON.stringify(u));
    } catch { /* ignore */ }
  };

  const value = useMemo<AuthCtx>(() => ({
    user, token,
    login: async (phone, password) => {
      const j = await post("/api/v2/auth/login/", { phone, password });
      if (!j.ok && !j.token) return j.error || "Xatolik";
      save(j.token, j.user);
      return null;
    },
    register: async (name, phone, password) => {
      const j = await post("/api/v2/auth/register/", { name, phone, password });
      if (!j.token) return j.error || "Xatolik";
      save(j.token, j.user);
      return null;
    },
    logout: () => {
      setToken(null); setUser(null);
      try { localStorage.removeItem("aza2_token"); localStorage.removeItem("aza2_user"); } catch { /* ignore */ }
    },
  }), [user, token]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  return useContext(Ctx);
}

export function authHeaders(): Record<string, string> {
  try {
    const t = localStorage.getItem("aza2_token");
    return t ? { Authorization: `Token ${t}` } : {};
  } catch {
    return {};
  }
}
