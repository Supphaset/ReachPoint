import { NavLink, Outlet, Link } from "react-router-dom";
import { useSession, type Role } from "../data/session";
import { Icon, type IconName } from "../ui/Icon";
import "./shell.css";

interface Tab {
  to: string;
  label: string;
  th: string;
  icon: IconName;
}

const TABS: Record<Role, Tab[]> = {
  team_leader: [
    { to: "/team/list", label: "Waiting", th: "รอทีม", icon: "list" },
    { to: "/team/mission", label: "My jobs", th: "งานของฉัน", icon: "mission" },
    { to: "/team/map", label: "Area map", th: "แผนที่", icon: "map" },
  ],
  coordinator: [
    { to: "/desk", label: "Desk", th: "โต๊ะประสานงาน", icon: "list" },
    { to: "/desk/split", label: "Split", th: "แบ่งงาน", icon: "people" },
    { to: "/desk/map", label: "Flood map", th: "แผนที่", icon: "map" },
  ],
  resident: [],
};

export function Wordmark() {
  return (
    <Link to="/" className="wordmark" aria-label="ReachPoint home">
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="12" cy="12" r="3.5" fill="currentColor" />
      </svg>
      <span>ReachPoint</span>
    </Link>
  );
}

export function AppShell() {
  const { session, signOut } = useSession();
  const tabs = session ? TABS[session.role] : [];
  return (
    <div className={`shell ${tabs.length ? "has-tabs" : ""}`}>
      <header className="topbar">
        <Wordmark />
        {tabs.length > 0 && (
          <nav className="topnav" aria-label="Main">
            {tabs.map((t) => (
              <NavLink key={t.to} to={t.to} end={t.to === "/desk"} className="topnav-link">
                <Icon name={t.icon} size={18} />
                {t.label}
              </NavLink>
            ))}
          </nav>
        )}
        <div className="topbar-end">
          <span className="demo-tag">Synthetic demo</span>
          {session && (
            <button className="who" onClick={signOut} title="Switch role">
              {session.label}
            </button>
          )}
        </div>
      </header>
      <main className="shell-main">
        <Outlet />
      </main>
      {tabs.length > 0 && (
        <nav className="tabbar" aria-label="Main">
          {tabs.map((t) => (
            <NavLink key={t.to} to={t.to} end={t.to === "/desk"} className="tab">
              <Icon name={t.icon} size={22} />
              <span>{t.th}</span>
              <span className="tab-en">{t.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}
