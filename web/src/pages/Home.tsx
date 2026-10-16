import { Link, useNavigate } from "react-router-dom";
import { DEMO_SESSIONS, useSession, type Session } from "../data/session";
import { useLang } from "../i18n/lang";
import { S } from "../i18n/strings";
import { Icon, type IconName } from "../ui/Icon";
import "./pages.css";

const HOME: Record<Session["role"], string> = {
  team_leader: "/team/list",
  coordinator: "/desk",
  resident: "/callers",
};

const STEP_ICON: IconName[] = ["water", "sparkle", "check", "hand"];
const ROLE_ICON: Record<string, IconName> = { resident: "alert", "team:T-S": "mission", "team:T-R": "map", coordinator: "list" };
const roleKey = (s: Session) => (s.role === "team_leader" ? s.actor : s.role);

/** Start page: what ReachPoint does, the live demo, and the demo roles (Firebase Auth replaces the role pick later). */
export function Home() {
  const { signIn } = useSession();
  const { t } = useLang();
  const navigate = useNavigate();
  const search = window.location.search;
  const demo = `/demo${search.includes("data=") ? search : "?data=api"}`;
  const order = ["resident", "team:T-S", "coordinator", "team:T-R"];
  const sessions = [...DEMO_SESSIONS].sort((a, b) => order.indexOf(roleKey(a)) - order.indexOf(roleKey(b)));
  return (
    <div className="page home">
      <section className="home-hero">
        <p className="home-context">{t(S.home.context)}</p>
        <h1>{t(S.home.tagline)}</h1>
        <p className="home-lead">{t(S.home.lead)}</p>
        <div className="home-cta">
          <Link className="btn btn-primary btn-md home-watch" to={demo}>
            <Icon name="people" size={20} />
            <span>{t(S.home.watch)}</span>
          </Link>
          <span className="muted">{t(S.home.watchNote)}</span>
        </div>
      </section>

      <section className="home-how" aria-labelledby="home-how">
        <h2 id="home-how">{t(S.home.howTitle)}</h2>
        <ol className="home-steps">
          {S.home.how.map((step, i) => (
            <li key={i}>
              <span className="home-step-icon" aria-hidden="true">
                <Icon name={STEP_ICON[i]} size={22} />
              </span>
              <span className="home-step-num">{i + 1}</span>
              <strong>{t(step.title)}</strong>
              <span className="muted">{t(step.body)}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="home-roles" aria-labelledby="home-roles">
        <h2 id="home-roles">{t(S.home.rolesTitle)}</h2>
        <div className="home-role-grid">
          {sessions.map((s) => {
            const r = S.home.roles[roleKey(s)];
            return (
              <button
                key={s.actor}
                type="button"
                className="home-role"
                onClick={() => {
                  signIn(s);
                  navigate(HOME[s.role] + search);
                }}
              >
                <span className="home-role-icon" aria-hidden="true">
                  <Icon name={ROLE_ICON[roleKey(s)] ?? "people"} size={24} />
                </span>
                <span className="home-role-text">
                  <strong>{r ? t(r.title) : s.label}</strong>
                  {r && <span className="muted">{t(r.body)}</span>}
                </span>
                <Icon name="chevron" size={20} />
              </button>
            );
          })}
        </div>
      </section>

      <footer className="home-foot">
        <span>{t(S.home.builtWith)}</span>
        <span>{t(S.home.cup)}</span>
      </footer>
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
