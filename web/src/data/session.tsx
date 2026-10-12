import { createContext, useContext, useState, type ReactNode } from "react";

/**
 * Demo sign-in. The four seeded roles (friend's Firebase Auth, Mon 12) map to these; until it is connected,
 * the role is picked on the start page and kept for this tab only.
 */
export type Role = "coordinator" | "team_leader" | "resident";

export interface Session {
  role: Role;
  actor: string; // e.g. "team:T-S", "coordinator:demo-1"
  label: string;
}

export const DEMO_SESSIONS: Session[] = [
  { role: "team_leader", actor: "team:T-S", label: "Team T-S (boat)" },
  { role: "team_leader", actor: "team:T-R", label: "Team T-R (truck)" },
  { role: "coordinator", actor: "coordinator:demo-1", label: "Coordinator desk" },
  { role: "resident", actor: "resident:demo", label: "Resident (ask for help)" },
];

const KEY = "reachpoint.session";

function load(): Session | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

const Ctx = createContext<{ session: Session | null; signIn: (s: Session) => void; signOut: () => void }>({
  session: null,
  signIn: () => {},
  signOut: () => {},
});

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(load);
  const signIn = (s: Session) => {
    setSession(s);
    try {
      sessionStorage.setItem(KEY, JSON.stringify(s));
    } catch {
      /* private mode: keep it in memory */
    }
  };
  const signOut = () => {
    setSession(null);
    try {
      sessionStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  };
  return <Ctx.Provider value={{ session, signIn, signOut }}>{children}</Ctx.Provider>;
}

export function useSession() {
  return useContext(Ctx);
}
