import { useNavigate } from "react-router-dom";
import { DEMO_SESSIONS, useSession, type Session } from "../data/session";
import { BigButton } from "../ui/components";
import "./pages.css";

const HOME: Record<Session["role"], string> = {
  team_leader: "/team/list",
  coordinator: "/desk",
  resident: "/status/demo",
};

/** Demo sign-in: pick one of the seeded roles. Firebase Auth replaces this when the friend's project is up. */
export function Home() {
  const { signIn } = useSession();
  const navigate = useNavigate();
  return (
    <div className="page narrow">
      <h1>Sign in to the demo</h1>
      <p className="muted">All people, cases and calls here are synthetic. The flood data is real (Hat Yai, Nov 2025).</p>
      <div className="role-list">
        {DEMO_SESSIONS.map((s) => (
          <BigButton
            key={s.actor}
            variant="secondary"
            onClick={() => {
              signIn(s);
              navigate(HOME[s.role]);
            }}
          >
            {s.label}
          </BigButton>
        ))}
      </div>
    </div>
  );
}

/** Placeholder for a screen another person builds on this shell. */
export function Placeholder({ title, owner, day }: { title: string; owner: string; day: string }) {
  return (
    <div className="page narrow">
      <h1>{title}</h1>
      <p className="muted">
        Built by {owner} on this shell ({day}). Use the shared components on <a href="/dev/ui">/dev/ui</a>.
      </p>
    </div>
  );
}
