import { NavLink, Outlet, Link } from "react-router-dom";
import { useSession, type Role } from "../data/session";
import { Icon, type IconName } from "../ui/Icon";
import { LangSwitch, useLang, type Pair } from "../i18n/lang";
import { S } from "../i18n/strings";
import "./shell.css";

interface Tab {
  to: string;
  name: Pair;
  icon: IconName;
}

const TABS: Record<Role, Tab[]> = {
  team_leader: [
    { to: "/team/list", name: S.shell.tabs.waiting, icon: "list" },
    { to: "/team/mission", name: S.shell.tabs.jobs, icon: "mission" },
    { to: "/team/map", name: S.shell.tabs.map, icon: "map" },
  ],
  coordinator: [
    { to: "/desk", name: S.shell.tabs.desk, icon: "list" },
    { to: "/desk/split", name: S.shell.tabs.split, icon: "people" },
    { to: "/desk/map", name: S.shell.tabs.floodMap, icon: "map" },
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
  const { t, lang } = useLang();
  const tabs = session ? TABS[session.role] : [];
  return (
    <div className={`shell ${tabs.length ? "has-tabs" : ""}`}>
      <header className="topbar">
        <Wordmark />
        {tabs.length > 0 && (
          <nav className="topnav" aria-label="Main">
            {tabs.map((tab) => (
              <NavLink key={tab.to} to={tab.to + window.location.search} end={tab.to === "/desk"} className="topnav-link">
                <Icon name={tab.icon} size={18} />
                {t(tab.name)}
              </NavLink>
            ))}
          </nav>
        )}
        <div className="topbar-end">
          <LangSwitch />
          <span className="demo-tag">{t(S.shell.demoTag)}</span>
          {session && (
            <button className="who" onClick={signOut} title={t(S.shell.switchRole)}>
              {lang === "th" ? session.labelTh ?? session.label : session.label}
            </button>
          )}
        </div>
      </header>
      <main className="shell-main">
        <Outlet />
      </main>
      {tabs.length > 0 && (
        <nav className="tabbar" aria-label="Main">
          {tabs.map((tab) => (
            <NavLink key={tab.to} to={tab.to + window.location.search} end={tab.to === "/desk"} className="tab">
              <Icon name={tab.icon} size={22} />
              <span>{t(tab.name)}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}
