import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Group, Job, OpenListing, Outcome, Party, TeamMissionsView, TeamStatus, Urgency } from "../../data/contract";
import { now } from "../../data/clock";
import { ASSISTANCE_LABEL, fmtAgo, fmtTime } from "../../data/format";
import { useSession } from "../../data/session";
import { apiMode, refreshMs } from "../../data/mode";
import { SegmentJobs, ZoneMissions } from "./Segments";
import {
  claimListing,
  closeAllocation,
  handBack,
  loadTeam,
  refreshTeam,
  reportProgress,
  requestReconfirm,
  setTeamStatus,
  setWindow,
  useTeam,
} from "../../data/teamStore";
import { Banner, BigButton, LastUpdated, PriorityBadge, Skeleton, StatusChip } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { useLang, type Lang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { OUTCOME, TEAM_STATUS } from "../../ui/states";
import { ProgressTracker } from "../../ui/ProgressTracker";
import { jobStep } from "../../ui/progress";
import "./team.css";

const STALE_CONFIRM_MIN = 60;

export function fmtDistance(m: number | null, lang: Lang = "en") {
  return S.units.distance(m)[lang];
}

export function fmtSeats(n: number, lang: Lang = "en") {
  return S.units.seats(Number.isInteger(n) ? `${n}` : n.toFixed(1), n === 1)[lang];
}

export function fmtParty(p: Party, lang: Lang = "en") {
  return (Object.keys(S.party) as (keyof Party)[])
    .filter((k) => p[k])
    .map((k) => {
      if (lang === "th") return `${S.party[k].th} ${p[k]} คน`;
      const [one, many] = S.party[k].en.split("|");
      return `${p[k]} ${p[k] === 1 ? one : many}`;
    })
    .join(lang === "th" ? " " : ", ");
}

const fmtPeople = (n: number, lang: Lang) => S.units.person(n)[lang];

function useTeamView() {
  const { session } = useSession();
  const teamId = session?.actor.startsWith("team:") ? session.actor.slice(5) : "T-S";
  useEffect(() => {
    loadTeam(teamId);
    if (!apiMode()) return;
    // A new case from the desk shows up without reloading: every 15 s, or ?refresh=2 on the /demo phones.
    const id = window.setInterval(refreshTeam, refreshMs());
    return () => window.clearInterval(id);
  }, [teamId]);
  return useTeam();
}

function Frame({ children }: { children: ReactNode }) {
  return <div className="page team-page">{children}</div>;
}

function Gate({ render }: { render: (v: TeamMissionsView, offline: boolean) => ReactNode }) {
  const s = useTeamView();
  const { t } = useLang();
  if (s.status === "loading")
    return (
      <Frame>
        <Skeleton lines={6} />
      </Frame>
    );
  if (s.status === "missing")
    return (
      <Frame>
        <Banner kind="info">{t(S.team.noRecords(s.teamId))}</Banner>
      </Frame>
    );
  if (s.status === "error")
    return (
      <Frame>
        <Banner kind="error" action={{ label: t(S.common.tryAgain), onClick: () => window.location.reload() }}>
          {t(S.team.listUnavailable)} {s.message}
        </Banner>
      </Frame>
    );
  return <Frame>{render(s.view, s.offline)}</Frame>;
}

/* ---------------- Team status (D4/D13, T17) ---------------- */

function StatusCard({ v }: { v: TeamMissionsView }) {
  const [open, setOpen] = useState(false);
  const { t: tr, lang } = useLang();
  const t = v.team;
  return (
    <section className="status-card" aria-label={tr(S.team.statusLabel)}>
      <div className="status-bar">
        <StatusChip kind="team" state={t.status} lang={lang} size="sm" />
        <span className="seats-line num"><Icon name="people" /> {tr(S.team.freeSeats(fmtSeats(t.resource.seatUnitsLeft, lang)))}</span>
        <BigButton variant="secondary" size="md" onClick={() => setOpen(true)}>{tr(S.team.change)}</BigButton>
      </div>
      {open && <StatusSheet v={v} onClose={() => setOpen(false)} />}
    </section>
  );
}

const BUSY_REASONS = S.team.busyReasons.map((r) => r.en);

/** Status and hand-back reasons are stored in English; show the Thai twin when we have one. */
function reasonText(r: string, lang: Lang) {
  const hit = [...S.team.busyReasons, ...S.team.handBackReasons].find((x) => x.en === r);
  return hit ? hit[lang] : r;
}

function backAboutOptions() {
  const start = Math.ceil(now() / (30 * 60000)) * 30 * 60000;
  return Array.from({ length: 16 }, (_, i) => new Date(start + i * 30 * 60000).toISOString());
}

function StatusSheet({ v, onClose }: { v: TeamMissionsView; onClose: () => void }) {
  const [status, setStatus] = useState<TeamStatus>(v.team.status);
  const [reason, setReason] = useState(v.team.reason ?? BUSY_REASONS[0]);
  const [back, setBack] = useState(v.team.backAbout ?? backAboutOptions()[2]);
  const { t, lang } = useLang();
  return (
    <Sheet title={t(S.team.statusLabel)} onClose={onClose}>
      <p className="muted">{seedText(v.label, lang)} · {seedText(v.team.resource.kind, lang)} {v.team.resource.resourceId} · {t(S.team.at(seedText(v.team.location.label, lang)))}</p>
      <p className="fine-print">{t(S.team.since(fmtTime(v.team.statusSetAt)))}{v.team.reason && ` · ${reasonText(v.team.reason, lang)}`}{v.team.backAbout && ` · ${t(S.team.backAbout(fmtTime(v.team.backAbout)))}`}</p>
      <p className="num">{t(S.team.seatsFree(fmtSeats(v.team.resource.seatUnitsLeft, lang), v.team.resource.seatUnits))}</p>
      <p className="fine-print">{seedText(v.team.resource.basis, lang)}</p>
      <div className="choice-list" role="radiogroup" aria-label={t(S.team.statusLabel)}>
        {(["available", "busy", "off_duty"] as TeamStatus[]).map((s) => (
          <label key={s} className={`choice ${status === s ? "is-on" : ""}`}>
            <input type="radio" name="status" checked={status === s} onChange={() => setStatus(s)} />
            <StatusChip kind="team" state={s} lang={lang} />
          </label>
        ))}
      </div>
      {status !== "available" && (
        <>
          <label className="field">
            <span>{t(S.team.reasonOptional)}</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              {BUSY_REASONS.map((r) => (
                <option key={r} value={r}>
                  {reasonText(r, lang)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>{t(S.team.backAboutField)}</span>
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
      <p className="fine-print">{t(S.team.statusNever)}</p>
      <BigButton
        onClick={async () => {
          await setTeamStatus(status, status === "available" ? null : reason, status === "available" ? null : back);
          onClose();
        }}
      >
        {t(S.team.saveStatus)}
      </BigButton>
    </Sheet>
  );
}

/* ---------------- Why it's urgent ---------------- */

export function UrgencyBox({ u, colour, open = false, inJob = false, children }: { u: Urgency; colour: string; open?: boolean; inJob?: boolean; children?: ReactNode }) {
  const { t, lang, pick } = useLang();
  const th = lang === "th" ? u.th : undefined;
  const kit = th?.kit.length === u.kit.length ? th.kit : u.kit;
  const withheld = th?.withheld ?? u.withheld;
  return (
    <details className={`urgency tone-${colour}`} open={open}>
      <summary>
        <span className="urgency-title">{th?.title ?? u.title}</span>
        <span className="urgency-summary">{th?.summary || u.summary}</span>
      </summary>
      {children}
      <ul className="urgency-facts">
        {u.facts.map((f) => (
          <li key={f.kind + f.text}>
            <span>
              {pick(f.text, f.th)}
              {f.at && (
                <span className={f.stale ? "is-stale" : ""}>
                  {t(S.team.reported(fmtTime(f.at), f.callers ?? 0))}
                  {f.stale && t(S.team.stale)}
                </span>
              )}
            </span>
            <span className="basis-tag">{S.team.basis[f.basis] ? t(S.team.basis[f.basis]) : f.basis}</span>
          </li>
        ))}
      </ul>
      {kit.length > 0 && (
        <div className="urgency-kit">
          <strong>{t(S.team.bring)}</strong>
          <ul>
            {kit.map((k) => (
              <li key={k}>{k}</li>
            ))}
          </ul>
        </div>
      )}
      {withheld && !inJob && (
        <p className="fine-print">
          <Icon name="lock" size={12} /> {withheld}{lang === "en" ? "." : ""}
        </p>
      )}
    </details>
  );
}

/* ---------------- Waiting list (C5) ---------------- */

export function WaitingPage() {
  return (
    <Gate
      render={(v, offline) => <WaitingBody v={v} offline={offline} />}
    />
  );
}

function WaitingBody({ v, offline }: { v: TeamMissionsView; offline: boolean }) {
  const { t, lang } = useLang();
  const open = v.open.filter((l) => l.groups.some((g) => g.state === "open"));
  const cap = v.team.capabilities[0];
  return (
          <>
            <header className="page-head">
              <h1>{t(S.team.waitingTitle)}</h1>
              <p className="muted">
                {S.assistance[cap] ? t(S.assistance[cap]) : ASSISTANCE_LABEL[cap]} · {t(S.team.order)}
              </p>
              <LastUpdated at={v.generatedAt} offline={offline} />
            </header>
            {offline && <Banner kind="offline">{t(S.team.offline)}</Banner>}
            <StatusCard v={v} />
            {!!v.asks?.length && <section aria-label="Coordinator asks"><h2>Coordinator asks</h2>
              <ul>{v.asks.slice(-10).reverse().map((a) => <li key={a.askId}>Asked at {fmtTime(a.askedAt)}: {a.groups.filter((g) => open.some((l) => l.listingId === g.listingId && l.groups.some((x) => x.groupId === g.groupId && x.state === "open"))).map((g) => {
                const listing = open.find((l) => l.listingId === g.listingId)!;
                return `${listing.landmarkLabel} · ${listing.groups.find((x) => x.groupId === g.groupId)!.label}`;
              }).join(", ") || "These groups are no longer open"}.</li>)}</ul>
              <p>Check current needs and take a whole group below. An ask reserves no capacity and makes no arrival promise.</p>
            </section>}
            {v.team.status !== "available" && (
              <Banner kind="stale">
                {lang === "th" ? `สถานะของคุณคือ ${TEAM_STATUS[v.team.status].th} ` : `You're ${TEAM_STATUS[v.team.status].en.toLowerCase()}. `}
                {t(S.team.notAvailable)}
              </Banner>
            )}
            {open.length === 0 ? (
              <p className="empty">{t(S.team.noWaiting)}</p>
            ) : (
              <ul className="listing-list">
                {open.map((l) => (
                  <ListingRow key={l.listingId} l={l} v={v} offline={offline} />
                ))}
              </ul>
            )}
            <ZoneMissions v={v} offline={offline} />
            <p className="fine-print">{lang === "en" ? `${v.dataLabel}. ` : ""}{t(S.team.landmarkNote)}</p>
          </>
  );
}

function ListingRow({ l, v, offline }: { l: OpenListing; v: TeamMissionsView; offline: boolean }) {
  const [taking, setTaking] = useState(false);
  const { t, lang, pick } = useLang();
  const confirmedMin = (now() - Date.parse(l.lastConfirmedAt)) / 60000;
  const old = confirmedMin > STALE_CONFIRM_MIN;
  const openGroups = l.groups.filter((g) => g.state === "open");
  const canTake = v.team.status === "available" && !offline;
  return (
    <li className={`listing-row tone-${l.colour}`}>
      <div className="listing-top">
        <PriorityBadge priority={l.colour} lang={lang} size="sm" />
        <strong>{l.caseId}</strong>
        <span className="listing-dist num">{fmtDistance(l.distanceM, lang)}</span>
      </div>
      <p className="listing-place">{seedText(l.landmarkLabel, lang)}</p>
      <p className="listing-summary">{pick(l.urgency.summary, l.urgency.th?.summary)}</p>
      <ul className="group-list">
        {l.groups.map((g) => (
          <li key={g.groupId} className={g.state === "taken" ? "is-taken" : ""}>
            <span className="group-label">{groupLabel(g, lang)}</span>
            <span className="num">
              <Icon name="people" /> {fmtPeople(g.people, lang)} · {fmtParty(g.party, lang)}
            </span>
            {g.state === "taken" && <StatusChip kind="job" state="taken" lang={lang} size="sm" />}
            {g.takenBy && <span className="muted">{g.takenBy === v.teamId ? t(S.team.byYou) : t(S.team.by(g.takenBy))}</span>}
          </li>
        ))}
      </ul>
      <div className="listing-actions">
        <BigButton size="md" icon="hand" disabled={!canTake || openGroups.length === 0} onClick={() => setTaking(true)}>
          {openGroups.length === l.groups.length && l.groups.length === 1 ? t(S.team.take) : t(S.team.takeFamilies)}
        </BigButton>
        {l.reconfirmRequestedAt ? (
          <span className="muted reconfirm-sent">
            <Icon name="check" size={14} /> {t(S.team.askedDesk(fmtTime(l.reconfirmRequestedAt)))}
          </span>
        ) : (
          <BigButton size="md" variant="quiet" onClick={() => requestReconfirm(l.listingId)}>
            {t(S.team.askReconfirm)}
          </BigButton>
        )}
      </div>
      <p className={`confirm-line ${old ? "is-old" : ""}`}>
        <Icon name="clock" size={14} />
        <span>
          {t(S.team.lastConfirmed(fmtTime(l.lastConfirmedAt), lang === "en" ? fmtAgo(l.lastConfirmedAt, now()) : t(S.units.ago(Math.floor(confirmedMin))), fmtTime(l.waitingSince)))}
        </span>
      </p>
      <UrgencyBox u={l.urgency} colour={l.colour}>
        {l.destination.id !== "D1" && (
          <p className="dest-line">
            <Icon name="chevron" size={14} /> {t(S.team.goesTo(lang === "th" ? l.destination.th?.label ?? l.destination.label : l.destination.label))}
          </p>
        )}
        {l.reasons
          .filter((r) => !r.startsWith("Urgent:"))
          .map((r) => <p key={r} className="listing-reason">{r}</p>)}
        <p className="fine-print">{seedText(l.distanceBasis, lang)}</p>
        {l.groups.map((g) => <p className="fine-print" key={g.groupId}>{groupLabel(g, lang)} · {fmtSeats(g.seatUnits, lang)}</p>)}
      </UrgencyBox>
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
  const { t, lang } = useLang();
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
    <Sheet title={t(S.team.takeTitle(l.caseId, seedText(l.landmarkLabel, lang)))} onClose={onClose}>
      <p className="muted">{t(S.team.wholeFamilies)}</p>
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
              <strong>{groupLabel(g, lang)}</strong> · {fmtPeople(g.people, lang)} ({fmtParty(g.party, lang)}) · {fmtSeats(g.seatUnits, lang)}
              {g.state !== "open" && ` · ${t(S.team.takenByShort(g.takenBy ?? ""))}`}
            </span>
          </label>
        ))}
      </div>
      <p className={`seats-check num ${need > left ? "is-short" : ""}`}>
        {t(S.team.needsSeats(fmtSeats(need, lang), fmtSeats(left, lang)))}
      </p>
      {error && (
        <Banner
          kind="error"
          action={
            error.code === "NEED_CHANGED" || error.code === "VERSION_CONFLICT"
              ? { label: t(S.team.lookAgain), onClick: onClose }
              : undefined
          }
        >
          {error.message}
        </Banner>
      )}
      <BigButton onClick={take} disabled={busy || picked.length === 0 || mustLookAgain} icon="hand">
        {busy ? t(S.team.taking) : picked.length === open.length && open.length === 1 ? t(S.team.takeThisFamily) : t(S.team.takeN(picked.length))}
      </BigButton>
      <p className="fine-print">{t(S.team.nothingPromised)}</p>
    </Sheet>
  );
}

/* ---------------- My jobs ---------------- */

export function JobsPage() {
  return (
    <Gate
      render={(v, offline) => <JobsBody v={v} offline={offline} />}
    />
  );
}

function JobsBody({ v, offline }: { v: TeamMissionsView; offline: boolean }) {
  const { t } = useLang();
  const active = v.jobs.filter((j) => j.state !== "closed");
  const closed = v.jobs.filter((j) => j.state === "closed");
  return (
          <>
            <header className="page-head">
              <h1>{t(S.team.jobsTitle)}</h1>
              <LastUpdated at={v.generatedAt} offline={offline} />
            </header>
            <SegmentJobs v={v} />
            {active.length === 0 && (
              <p className="empty">
                {closed.length ? t(S.team.noOpenJobs) : t(S.team.noJobs)} <Link to={`/team/list${window.location.search}`}>{t(S.team.seeWaiting)}</Link>
              </p>
            )}
            {active.map((j) => (
              <JobCard key={j.allocationId} j={j} />
            ))}
            {closed.length > 0 && (
              <section className="closed-jobs">
                <h2>{t(S.team.finishedToday)}</h2>
                {closed.map((j) => (
                  <JobCard key={j.allocationId} j={j} />
                ))}
              </section>
            )}
          </>
  );
}

function groupLabel(g: { label: string; labelTh?: string }, lang: Lang) {
  return lang === "th" ? g.labelTh ?? seedText(g.label, lang) : g.label;
}

function windowStarts() {
  const start = Math.ceil(now() / (30 * 60000)) * 30 * 60000;
  return Array.from({ length: 20 }, (_, i) => new Date(start + i * 30 * 60000).toISOString());
}

const DURATIONS = [30, 60, 90, 120];

export function JobCard({ j }: { j: Job }) {
  const [error, setError] = useState<string | null>(null);
  const [start, setStart] = useState(windowStarts()[1]);
  const [mins, setMins] = useState(60);
  const [handing, setHanding] = useState(false);
  const [ending, setEnding] = useState(false);
  const closed = j.state === "closed";
  const held = j.state === "held";
  const { t, lang } = useLang();
  const destLabel = lang === "th" ? j.destination.th?.label ?? j.destination.label : j.destination.label;
  const destReason = lang === "th" ? j.destination.th?.reason ?? j.destination.reason : j.destination.reason;

  const run = async (p: Promise<{ ok: boolean; message?: string }>) => {
    const r = await p;
    setError(r.ok ? null : (r.message ?? t(S.team.wrong)));
  };
  const [lon, lat] = j.pickup.at;
  const nav = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;

  return (
    <article className={`job-card tone-${j.colour}`} id={j.allocationId}>
      <ProgressTracker steps={S.progress.job} current={jobStep(j)} held={held} horizontal label={S.progress.jobLabel} />
      <header className="job-head">
        <PriorityBadge priority={j.colour} lang={lang} size="sm" />
        <strong>{j.caseId}</strong>
        <span className="muted">{seedText(j.landmarkLabel, lang)}</span>
        <span className="job-state">
          {closed && j.outcome ? <OutcomeChip o={j.outcome} /> : <StatusChip kind="job" state={j.state} lang={lang} size="sm" />}
        </span>
      </header>
      <section className="window">
        <h3>
          <Icon name="clock" size={16} /> {t(S.team.window)}
        </h3>
        {held ? (
          <p>
            {t(S.team.onHold(j.holdReason ?? ""))}
            {j.withdrawnWindow && <> {t(S.team.earlier)} <s className="num">{fmtTime(j.withdrawnWindow.start)}–{fmtTime(j.withdrawnWindow.end)}</s> {t(S.team.earlierWithdrawn)}</>}
            {j.nextStatusUpdate && <> {t(S.team.nextUpdate(fmtTime(j.nextStatusUpdate.at)))}</>}
          </p>
        ) : j.window ? (
          <p>
            <strong className="num">
              {fmtTime(j.window.start)}–{fmtTime(j.window.end)}
            </strong>{" "}
            <span className="muted">{t(S.team.yourEstimate(fmtTime(j.window.setAt), closed))}</span>
          </p>
        ) : closed ? (
          <p className="muted">{t(S.team.noWindow)}</p>
        ) : j.state !== "taken" ? (
          <p className="muted">{t(S.team.noWindow)}</p>
        ) : (
          <>
            <p className="muted">{t(S.team.seeking)}</p>
            <div className="window-pick">
              <label className="field">
                <span>{t(S.team.from)}</span>
                <select value={start} onChange={(e) => setStart(e.target.value)}>
                  {windowStarts().map((t) => (
                    <option key={t} value={t}>
                      {fmtTime(t)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>{t(S.team.for)}</span>
                <select value={mins} onChange={(e) => setMins(Number(e.target.value))}>
                  {DURATIONS.map((d) => (
                    <option key={d} value={d}>
                      {t(S.team.duration(d))}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <BigButton size="md" onClick={() => run(setWindow(j.allocationId, start, new Date(Date.parse(start) + mins * 60000).toISOString()))}>
              {t(S.team.setWindowAction)}
            </BigButton>
          </>
        )}
      </section>

      {error && <Banner kind="error">{error}</Banner>}

      {!closed && !held && (
        <div className="job-actions">
          {j.state === "taken" && j.window && (
            <BigButton size="md" disabled={!j.window} onClick={() => run(reportProgress(j.allocationId, "on_the_way"))}>
              {t(S.team.onTheWay)}
            </BigButton>
          )}
          {j.state === "on_the_way" && (
            <BigButton size="md" onClick={() => run(reportProgress(j.allocationId, "on_scene"))}>
              {t(S.team.onScene)}
            </BigButton>
          )}
          {j.state === "on_scene" && (
            <BigButton size="md" onClick={() => setEnding(true)}>
              {t(S.team.finish)}
            </BigButton>
          )}
          <BigButton size="md" variant="secondary" onClick={() => setHanding(true)}>
            {t(S.team.handBack)}
          </BigButton>
        </div>
      )}
      {j.urgency && <UrgencyBox u={j.urgency} colour={j.colour} open={!closed} inJob />}
      <ul className="group-list">
        {j.groups.map((g) => (
          <li key={g.groupId}>
            <span className="group-label">{groupLabel(g, lang)}</span>
            <span className="num">
              {fmtPeople(g.people, lang)} · {fmtParty(g.party, lang)}
            </span>
          </li>
        ))}
      </ul>

      {!closed && j.preparationSummary && <section className="medical">
        <h3>{lang === "th" ? "สรุปเพื่อเตรียมทีม" : "Volunteer preparation summary"} · {j.preparationSummary.checkedBy ?? "AI"}</h3>
        <p style={{ whiteSpace: "pre-wrap" }}>{j.preparationSummary.text}</p>
        <p className="fine-print">{fmtTime(j.preparationSummary.at)} · {lang === "th" ? "ข้อมูลจากผู้แจ้ง ต้องยืนยันสภาพปัจจุบัน" : "Caller-reported information; confirm current conditions."}</p>
      </section>}
      {j.medical && (
        <section className="medical" aria-label={t(S.team.medical)}>
          <h3>
            <Icon name="lock" size={16} /> {t(S.team.medical)}
          </h3>
          <ul>
            {j.medical.functional.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <p>
            <span className="muted">{t(S.team.condition)}</span> {j.medical.condition}
          </p>
          <p className="fine-print">
            {j.medical.basis}. {t(S.team.medicalNote)}
          </p>
        </section>
      )}
      {!j.medical && j.medicalRemovedAt && (
        <p className="fine-print">
          <Icon name="lock" size={12} /> {t(S.team.medicalRemoved(fmtTime(j.medicalRemovedAt)))}
        </p>
      )}

      <section className="pickup">
        <div className="pickup-row">
        <h3><Icon name="map" /> {t(S.team.pickup)}</h3>
        <p className="num">
          {lat.toFixed(5)}, {lon.toFixed(5)} · <span className="muted">{seedText(j.pickup.precision, lang)}: {seedText(j.pickup.source, lang)}</span>
        </p>
        </div>
        <div className="pickup-row">
          <h3>{t(S.team.takeThemTo)}</h3>
          <p><strong>{destLabel}</strong> <span className="muted">· {destReason}</span></p>
        </div>
        {!closed && !held && (
          <a className="btn btn-secondary btn-md nav-link" href={nav} target="_blank" rel="noreferrer">
            <Icon name="chevron" size={18} /> {t(S.team.navigate)}
          </a>
        )}
        <p className="fine-print">{t(S.team.pointPrivate)}</p>
      </section>

      {closed && j.closedAt && <p className="fine-print">{t(S.team.closedLate(fmtTime(j.closedAt)))}</p>}

      {ending && (
        <Sheet title={t(S.team.finishTitle(j.caseId))} onClose={() => setEnding(false)}>
          <p className="muted">{t(S.team.whatHappened)}</p>
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
                {OUTCOME[o][lang]}
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
  const { lang } = useLang();
  return <StatusChip kind="outcome" state={o} lang={lang} size="sm" />;
}

const HAND_BACK_REASONS = S.team.handBackReasons.map((r) => r.en);

function HandBackSheet({ j, onClose, onError }: { j: Job; onClose: () => void; onError: (m: string | null) => void }) {
  const [reason, setReason] = useState(HAND_BACK_REASONS[0]);
  const { t, lang } = useLang();
  return (
    <Sheet title={t(S.team.handBackTitle(j.caseId))} onClose={onClose}>
      <p className="muted">{t(S.team.handBackBody)}</p>
      <label className="field">
        <span>{t(S.team.why)}</span>
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          {HAND_BACK_REASONS.map((r) => (
            <option key={r} value={r}>
              {reasonText(r, lang)}
            </option>
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
        {t(S.team.handBack)}
      </BigButton>
    </Sheet>
  );
}

/* ---------------- Sheet ---------------- */

function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const { t } = useLang();
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
          <button className="icon-btn" onClick={onClose} aria-label={t(S.common.close)}>
            <Icon name="close" size={22} />
          </button>
        </header>
        <div className="ui-sheet-body">{children}</div>
      </div>
    </div>
  );
}
