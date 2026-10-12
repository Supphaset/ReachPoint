import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Group, Job, OpenListing, Outcome, Party, TeamMissionsView, TeamStatus, Urgency } from "../../data/contract";
import { now } from "../../data/clock";
import { ASSISTANCE_LABEL, fmtAgo, fmtTime } from "../../data/format";
import { useSession } from "../../data/session";
import { SegmentJobs, ZoneMissions } from "./Segments";
import {
  claimListing,
  closeAllocation,
  handBack,
  loadTeam,
  reportProgress,
  requestReconfirm,
  setTeamStatus,
  setWindow,
  useTeam,
} from "../../data/teamStore";
import { Banner, BigButton, LastUpdated, PriorityBadge, Skeleton, StatusChip } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { OUTCOME, TEAM_STATUS } from "../../ui/states";
import "./team.css";

const STALE_CONFIRM_MIN = 60;

export function fmtDistance(m: number | null) {
  if (m === null) return "distance unknown";
  return m < 1000 ? `about ${m} m` : `about ${(m / 1000).toFixed(1)} km`;
}

export function fmtSeats(n: number) {
  return `${Number.isInteger(n) ? n : n.toFixed(1)} seat${n === 1 ? "" : "s"}`;
}

const ONE: Record<keyof Party, string> = { adults: "adult", children: "child", infants: "baby", stretcher: "stretcher" };
const MANY: Record<keyof Party, string> = { adults: "adults", children: "children", infants: "babies", stretcher: "stretchers" };

export function fmtParty(p: Party) {
  return (Object.keys(ONE) as (keyof Party)[])
    .filter((k) => p[k])
    .map((k) => `${p[k]} ${p[k] === 1 ? ONE[k] : MANY[k]}`)
    .join(", ");
}

function useTeamView() {
  const { session } = useSession();
  const teamId = session?.actor.startsWith("team:") ? session.actor.slice(5) : "T-S";
  useEffect(() => {
    loadTeam(teamId);
  }, [teamId]);
  return useTeam();
}

function Frame({ children }: { children: ReactNode }) {
  return <div className="page team-page">{children}</div>;
}

function Gate({ render }: { render: (v: TeamMissionsView, offline: boolean) => ReactNode }) {
  const s = useTeamView();
  if (s.status === "loading")
    return (
      <Frame>
        <Skeleton lines={6} />
      </Frame>
    );
  if (s.status === "missing")
    return (
      <Frame>
        <Banner kind="info">No demo records for team {s.teamId} yet. Sign in as Team T-S or T-R.</Banner>
      </Frame>
    );
  if (s.status === "error")
    return (
      <Frame>
        <Banner kind="error" action={{ label: "Try again", onClick: () => window.location.reload() }}>
          Your team's list is unavailable. {s.message}
        </Banner>
      </Frame>
    );
  return <Frame>{render(s.view, s.offline)}</Frame>;
}

/* ---------------- Team status (D4/D13, T17) ---------------- */

function StatusCard({ v }: { v: TeamMissionsView }) {
  const [open, setOpen] = useState(false);
  const t = v.team;
  const s = TEAM_STATUS[t.status];
  return (
    <section className="status-card" aria-label="Team status">
      <div className="status-top">
        <div>
          <p className="muted status-who">
            {v.label} · {t.resource.kind} {t.resource.resourceId} · at {t.location.label}
          </p>
          <p className="status-line">
            <StatusChip kind="team" state={t.status} />
            <span className="muted">
              since {fmtTime(t.statusSetAt)}
              {t.reason && ` · ${t.reason}`}
              {t.backAbout && ` · back about ${fmtTime(t.backAbout)}`}
            </span>
          </p>
        </div>
        <BigButton variant="secondary" size="md" onClick={() => setOpen(true)}>
          Change
        </BigButton>
      </div>
      <p className="seats-line num">
        <Icon name="people" size={16} /> {fmtSeats(t.resource.seatUnitsLeft)} free of {t.resource.seatUnits} today
        <span className="muted"> · {t.resource.basis}</span>
      </p>
      {open && <StatusSheet v={v} onClose={() => setOpen(false)} />}
      <span className="visually-hidden">{s.en}</span>
    </section>
  );
}

const BUSY_REASONS = ["Refuelling", "Boat repair", "Rest", "On another job", "Carrying people to the shelter"];

function backAboutOptions() {
  const start = Math.ceil(now() / (30 * 60000)) * 30 * 60000;
  return Array.from({ length: 16 }, (_, i) => new Date(start + i * 30 * 60000).toISOString());
}

function StatusSheet({ v, onClose }: { v: TeamMissionsView; onClose: () => void }) {
  const [status, setStatus] = useState<TeamStatus>(v.team.status);
  const [reason, setReason] = useState(v.team.reason ?? BUSY_REASONS[0]);
  const [back, setBack] = useState(v.team.backAbout ?? backAboutOptions()[2]);
  return (
    <Sheet title="Team status" onClose={onClose}>
      <div className="choice-list" role="radiogroup" aria-label="Status">
        {(["available", "busy", "off_duty"] as TeamStatus[]).map((s) => (
          <label key={s} className={`choice ${status === s ? "is-on" : ""}`}>
            <input type="radio" name="status" checked={status === s} onChange={() => setStatus(s)} />
            <StatusChip kind="team" state={s} />
          </label>
        ))}
      </div>
      {status !== "available" && (
        <>
          <label className="field">
            <span>Reason (optional)</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              {BUSY_REASONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Back about</span>
            <select value={back} onChange={(e) => setBack(e.target.value)}>
              {backAboutOptions().map((t) => (
                <option key={t} value={t}>
                  {fmtTime(t)}
                </option>
              ))}
            </select>
          </label>
        </>
      )}
      <p className="fine-print">Your status never changes by itself. The desk sees it with the time you set it.</p>
      <BigButton
        onClick={async () => {
          await setTeamStatus(status, status === "available" ? null : reason, status === "available" ? null : back);
          onClose();
        }}
      >
        Save status
      </BigButton>
    </Sheet>
  );
}

/* ---------------- Why it's urgent ---------------- */

const BASIS: Record<string, string> = {
  "qualified review": "qualified review",
  coordinator: "coordinator",
  "reviewed call": "reviewed call",
  callers: "callers",
  none: "no report",
};

export function UrgencyBox({ u, colour, open = false, inJob = false }: { u: Urgency; colour: string; open?: boolean; inJob?: boolean }) {
  return (
    <details className={`urgency tone-${colour}`} open={open}>
      <summary>
        <span className="urgency-title">{u.title}</span>
        <span className="urgency-summary">{u.summary}</span>
      </summary>
      <ul className="urgency-facts">
        {u.facts.map((f) => (
          <li key={f.kind + f.text}>
            <span>
              {f.text}
              {f.at && (
                <span className={f.stale ? "is-stale" : ""}>
                  {" "}
                  · reported {fmtTime(f.at)} by {f.callers} caller{f.callers === 1 ? "" : "s"}
                  {f.stale && " · older than 6 h, may have changed"}
                </span>
              )}
            </span>
            <span className="basis-tag">{BASIS[f.basis] ?? f.basis}</span>
          </li>
        ))}
      </ul>
      {u.kit.length > 0 && (
        <div className="urgency-kit">
          <strong>Bring</strong>
          <ul>
            {u.kit.map((k) => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </div>
      )}
      {u.withheld && !inJob && (
        <p className="fine-print">
          <Icon name="lock" size={12} /> {u.withheld}.
        </p>
      )}
    </details>
  );
}

/* ---------------- Waiting list (C5) ---------------- */

export function WaitingPage() {
  return (
    <Gate
      render={(v, offline) => {
        const open = v.open.filter((l) => l.groups.some((g) => g.state === "open"));
        return (
          <>
            <header className="page-head">
              <h1>Waiting for a team</h1>
              <p className="muted">
                {ASSISTANCE_LABEL[v.team.capabilities[0]]} · red first, then nearest, then longest waiting
              </p>
              <LastUpdated at={v.generatedAt} offline={offline} />
            </header>
            {offline && <Banner kind="offline">Offline. You can look, but taking a case needs a connection.</Banner>}
            <StatusCard v={v} />
            {v.team.status !== "available" && (
              <Banner kind="stale">You're {TEAM_STATUS[v.team.status].en.toLowerCase()}. Set yourself Available to take cases.</Banner>
            )}
            {open.length === 0 ? (
              <p className="empty">No waiting cases for your team.</p>
            ) : (
              <ul className="listing-list">
                {open.map((l) => (
                  <ListingRow key={l.listingId} l={l} v={v} offline={offline} />
                ))}
              </ul>
            )}
            <ZoneMissions v={v} offline={offline} />
            <p className="fine-print">{v.dataLabel}. Places are shown at landmark level; you get the exact point after you take a case.</p>
          </>
        );
      }}
    />
  );
}

function ListingRow({ l, v, offline }: { l: OpenListing; v: TeamMissionsView; offline: boolean }) {
  const [taking, setTaking] = useState(false);
  const confirmedMin = (now() - Date.parse(l.lastConfirmedAt)) / 60000;
  const old = confirmedMin > STALE_CONFIRM_MIN;
  const openGroups = l.groups.filter((g) => g.state === "open");
  const canTake = v.team.status === "available" && !offline;
  return (
    <li className={`listing-row tone-${l.colour}`}>
      <div className="listing-top">
        <PriorityBadge priority={l.colour} lang="en" size="sm" />
        <strong>{l.caseId}</strong>
        <span className="muted">{l.landmarkLabel}</span>
        <span className="listing-dist num">{fmtDistance(l.distanceM)}</span>
      </div>
      <UrgencyBox u={l.urgency} colour={l.colour} />
      {l.destination.id !== "D1" && (
        <p className="dest-line">
          <Icon name="chevron" size={14} /> Goes to {l.destination.label}
        </p>
      )}
      {l.reasons
        .filter((r) => !r.startsWith("Urgent:"))
        .map((r) => (
          <p key={r} className="listing-reason">
            {r}
          </p>
        ))}
      <ul className="group-list">
        {l.groups.map((g) => (
          <li key={g.groupId} className={g.state === "taken" ? "is-taken" : ""}>
            <span className="group-label">{g.label}</span>
            <span className="num">
              {g.people} {g.people === 1 ? "person" : "people"} · {fmtParty(g.party)} · {fmtSeats(g.seatUnits)}
            </span>
            {g.state === "taken" && <StatusChip kind="job" state="taken" lang="en" size="sm" />}
            {g.takenBy && <span className="muted">{g.takenBy === v.teamId ? "by you" : `by ${g.takenBy}`}</span>}
          </li>
        ))}
      </ul>
      <p className={`confirm-line ${old ? "is-old" : ""}`}>
        <Icon name="clock" size={14} />
        <span>
          Last confirmed {fmtTime(l.lastConfirmedAt)} · {fmtAgo(l.lastConfirmedAt, now())} · waiting since {fmtTime(l.waitingSince)}
        </span>
      </p>
      <div className="listing-actions">
        <BigButton size="md" icon="hand" disabled={!canTake || openGroups.length === 0} onClick={() => setTaking(true)}>
          {openGroups.length === l.groups.length && l.groups.length === 1 ? "Take" : "Take families…"}
        </BigButton>
        {l.reconfirmRequestedAt ? (
          <span className="muted reconfirm-sent">
            <Icon name="check" size={14} /> Asked the desk at {fmtTime(l.reconfirmRequestedAt)}
          </span>
        ) : (
          <BigButton size="md" variant={old ? "secondary" : "quiet"} onClick={() => requestReconfirm(l.listingId)}>
            Ask desk to re-confirm
          </BigButton>
        )}
      </div>
      {taking && <TakeSheet l={l} v={v} onClose={() => setTaking(false)} />}
    </li>
  );
}

function TakeSheet({ l, v, onClose }: { l: OpenListing; v: TeamMissionsView; onClose: () => void }) {
  const navigate = useNavigate();
  const open = l.groups.filter((g) => g.state === "open");
  const [picked, setPicked] = useState<string[]>(open.map((g) => g.groupId));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const seen = l.needRevision;
  const need = open.filter((g) => picked.includes(g.groupId)).reduce((s, g) => s + g.seatUnits, 0);
  const left = v.team.resource.seatUnitsLeft;
  const mustLookAgain = error?.code === "NEED_CHANGED" || error?.code === "VERSION_CONFLICT";

  const take = async () => {
    setBusy(true);
    setError(null);
    const r = await claimListing(l.listingId, picked, seen);
    setBusy(false);
    if (r.ok) navigate(`/team/mission${window.location.search}#${r.value.allocationId}`);
    else setError({ code: r.code, message: r.message });
  };

  return (
    <Sheet title={`Take ${l.caseId} · ${l.landmarkLabel}`} onClose={onClose}>
      <p className="muted">Take whole families. You can take some now and leave the others for another team.</p>
      <div className="choice-list">
        {l.groups.map((g: Group) => (
          <label key={g.groupId} className={`choice ${picked.includes(g.groupId) ? "is-on" : ""} ${g.state !== "open" ? "is-disabled" : ""}`}>
            <input
              type="checkbox"
              disabled={g.state !== "open"}
              checked={picked.includes(g.groupId)}
              onChange={(e) => setPicked((p) => (e.target.checked ? [...p, g.groupId] : p.filter((x) => x !== g.groupId)))}
            />
            <span>
              <strong>{g.label}</strong> · {g.people} {g.people === 1 ? "person" : "people"} ({fmtParty(g.party)}) · {fmtSeats(g.seatUnits)}
              {g.state !== "open" && ` · taken by ${g.takenBy}`}
            </span>
          </label>
        ))}
      </div>
      <p className={`seats-check num ${need > left ? "is-short" : ""}`}>
        Needs {fmtSeats(need)} · you have {fmtSeats(left)} free
      </p>
      {error && (
        <Banner
          kind="error"
          action={
            error.code === "NEED_CHANGED" || error.code === "VERSION_CONFLICT"
              ? { label: "Look again", onClick: onClose }
              : undefined
          }
        >
          {error.message}
        </Banner>
      )}
      <BigButton onClick={take} disabled={busy || picked.length === 0 || mustLookAgain} icon="hand">
        {busy ? "Taking…" : picked.length === open.length && open.length === 1 ? "Take this family" : `Take ${picked.length} ${picked.length === 1 ? "family" : "families"}`}
      </BigButton>
      <p className="fine-print">Nothing is promised to the family until you set an arrival window.</p>
    </Sheet>
  );
}

/* ---------------- My jobs ---------------- */

export function JobsPage() {
  return (
    <Gate
      render={(v, offline) => {
        const active = v.jobs.filter((j) => j.state !== "closed");
        const closed = v.jobs.filter((j) => j.state === "closed");
        return (
          <>
            <header className="page-head">
              <h1>My jobs</h1>
              <LastUpdated at={v.generatedAt} offline={offline} />
            </header>
            <SegmentJobs v={v} />
            {active.length === 0 && (
              <p className="empty">
                {closed.length ? "No open jobs." : "No jobs yet."} <Link to={`/team/list${window.location.search}`}>See who is waiting</Link>.
              </p>
            )}
            {active.map((j) => (
              <JobCard key={j.allocationId} j={j} />
            ))}
            {closed.length > 0 && (
              <section className="closed-jobs">
                <h2>Finished today</h2>
                {closed.map((j) => (
                  <JobCard key={j.allocationId} j={j} />
                ))}
              </section>
            )}
          </>
        );
      }}
    />
  );
}

function windowStarts() {
  const start = Math.ceil(now() / (30 * 60000)) * 30 * 60000;
  return Array.from({ length: 20 }, (_, i) => new Date(start + i * 30 * 60000).toISOString());
}

const DURATIONS = [30, 60, 90, 120];

function JobCard({ j }: { j: Job }) {
  const [error, setError] = useState<string | null>(null);
  const [start, setStart] = useState(windowStarts()[1]);
  const [mins, setMins] = useState(60);
  const [handing, setHanding] = useState(false);
  const [ending, setEnding] = useState(false);
  const closed = j.state === "closed";

  const run = async (p: Promise<{ ok: boolean; message?: string }>) => {
    const r = await p;
    setError(r.ok ? null : (r.message ?? "Something went wrong"));
  };
  const [lon, lat] = j.pickup.at;
  const nav = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;

  return (
    <article className={`job-card tone-${j.colour}`} id={j.allocationId}>
      <header className="job-head">
        <PriorityBadge priority={j.colour} lang="en" size="sm" />
        <strong>{j.caseId}</strong>
        <span className="muted">{j.landmarkLabel}</span>
        <span className="job-state">
          {closed && j.outcome ? <OutcomeChip o={j.outcome} /> : <StatusChip kind="job" state={j.state} lang="en" size="sm" />}
        </span>
      </header>
      {j.urgency && <UrgencyBox u={j.urgency} colour={j.colour} open={!closed} inJob />}
      <ul className="group-list">
        {j.groups.map((g) => (
          <li key={g.groupId}>
            <span className="group-label">{g.label}</span>
            <span className="num">
              {g.people} {g.people === 1 ? "person" : "people"} · {fmtParty(g.party)}
            </span>
          </li>
        ))}
      </ul>

      {j.medical && (
        <section className="medical" aria-label="Medical, for your team only">
          <h3>
            <Icon name="lock" size={16} /> Medical · for your team only
          </h3>
          <ul>
            {j.medical.functional.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <p>
            <span className="muted">Condition (from the desk):</span> {j.medical.condition}
          </p>
          <p className="fine-print">
            {j.medical.basis}. Removed from this phone when the job closes. Don't share or photograph it.
          </p>
        </section>
      )}
      {!j.medical && j.medicalRemovedAt && (
        <p className="fine-print">
          <Icon name="lock" size={12} /> Medical notes removed at {fmtTime(j.medicalRemovedAt)}, when the job closed.
        </p>
      )}

      <section className="pickup">
        <h3>
          <Icon name="map" size={16} /> Pickup point
        </h3>
        <p className="num">
          {lat.toFixed(5)}, {lon.toFixed(5)} · <span className="muted">{j.pickup.precision}: {j.pickup.source}</span>
        </p>
        {!closed && (
          <a className="btn btn-secondary btn-md nav-link" href={nav} target="_blank" rel="noreferrer">
            <Icon name="chevron" size={18} /> Navigate (Google Maps)
          </a>
        )}
        <p className="fine-print">Only you and the desk see this point. Roads may be flooded: the route is your call.</p>
        <p className="dest-line">
          <Icon name="chevron" size={14} /> Take them to <strong>{j.destination.label}</strong>
          <span className="muted"> · {j.destination.reason}</span>
        </p>
      </section>

      <section className="window">
        <h3>
          <Icon name="clock" size={16} /> Arrival window
        </h3>
        {j.window ? (
          <p>
            <strong className="num">
              {fmtTime(j.window.start)}–{fmtTime(j.window.end)}
            </strong>{" "}
            <span className="muted">
              (your estimate, set {fmtTime(j.window.setAt)}
              {closed ? ")" : "; the family sees it now)"}
            </span>
          </p>
        ) : closed ? (
          <p className="muted">No window was set.</p>
        ) : (
          <>
            <p className="muted">The family sees "seeking team" until you set this.</p>
            <div className="window-pick">
              <label className="field">
                <span>From</span>
                <select value={start} onChange={(e) => setStart(e.target.value)}>
                  {windowStarts().map((t) => (
                    <option key={t} value={t}>
                      {fmtTime(t)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>For</span>
                <select value={mins} onChange={(e) => setMins(Number(e.target.value))}>
                  {DURATIONS.map((d) => (
                    <option key={d} value={d}>
                      {d < 60 ? `${d} min` : `${d / 60} h`}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <BigButton size="md" onClick={() => run(setWindow(j.allocationId, start, new Date(Date.parse(start) + mins * 60000).toISOString()))}>
              Set window {fmtTime(start)}–{fmtTime(new Date(Date.parse(start) + mins * 60000).toISOString())}
            </BigButton>
          </>
        )}
      </section>

      {error && <Banner kind="error">{error}</Banner>}

      {!closed && (
        <div className="job-actions">
          {j.state === "taken" && (
            <BigButton size="md" disabled={!j.window} onClick={() => run(reportProgress(j.allocationId, "on_the_way"))}>
              On the way
            </BigButton>
          )}
          {j.state === "on_the_way" && (
            <BigButton size="md" onClick={() => run(reportProgress(j.allocationId, "on_scene"))}>
              On scene
            </BigButton>
          )}
          {j.state !== "taken" && (
            <BigButton size="md" onClick={() => setEnding(true)}>
              Finish…
            </BigButton>
          )}
          <BigButton size="md" variant="secondary" onClick={() => setHanding(true)}>
            Hand back
          </BigButton>
        </div>
      )}
      {closed && j.closedAt && <p className="fine-print">Closed {fmtTime(j.closedAt)}. Late updates are refused: "This job is closed".</p>}

      {ending && (
        <Sheet title={`Finish ${j.caseId}`} onClose={() => setEnding(false)}>
          <p className="muted">What happened? This goes to the desk and the family's status page.</p>
          <div className="outcome-grid">
            {(Object.keys(OUTCOME) as Outcome[]).map((o) => (
              <BigButton
                key={o}
                size="md"
                variant="secondary"
                onClick={async () => {
                  await run(closeAllocation(j.allocationId, o));
                  setEnding(false);
                }}
              >
                {OUTCOME[o].en}
              </BigButton>
            ))}
          </div>
        </Sheet>
      )}
      {handing && <HandBackSheet j={j} onClose={() => setHanding(false)} onError={setError} />}
    </article>
  );
}

function OutcomeChip({ o }: { o: Outcome }) {
  return <StatusChip kind="outcome" state={o} lang="en" size="sm" />;
}

const HAND_BACK_REASONS = ["Can't reach the place", "Boat problem", "Not enough seats after all", "Called to an emergency"];

function HandBackSheet({ j, onClose, onError }: { j: Job; onClose: () => void; onError: (m: string | null) => void }) {
  const [reason, setReason] = useState(HAND_BACK_REASONS[0]);
  return (
    <Sheet title={`Hand back ${j.caseId}`} onClose={onClose}>
      <p className="muted">The families go back on the list for other teams, and your seats come back. The desk is told why.</p>
      <label className="field">
        <span>Why</span>
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          {HAND_BACK_REASONS.map((r) => (
            <option key={r}>{r}</option>
          ))}
        </select>
      </label>
      <BigButton
        variant="secondary"
        onClick={async () => {
          const r = await handBack(j.allocationId, reason);
          onError(r.ok ? null : r.message);
          onClose();
        }}
      >
        Hand back
      </BigButton>
    </Sheet>
  );
}

/* ---------------- Sheet ---------------- */

function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="ui-sheet-backdrop" onClick={onClose}>
      <div className="ui-sheet" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <header className="ui-sheet-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="close" size={22} />
          </button>
        </header>
        <div className="ui-sheet-body">{children}</div>
      </div>
    </div>
  );
}
