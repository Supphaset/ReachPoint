import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { useEffect, useState } from "react";
import type { ReconfirmRow, RisingWaterView } from "../../data/contract";
import { flagUrgent, loadTeam, useTeam } from "../../data/teamStore";
import { useView } from "../../data/useView";
import { Banner, BigButton, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { pickSnapshot, useMinute } from "../briefing/Rain";
import { ReviewQueue } from "./ReviewQueue";
import { SuggestedChecks } from "./SuggestedChecks";
import { ResourceFailure } from "./ResourceFailure";
import "../intake/intake.css";
import "./desk.css";

type Decision = { kind: "called" } | { kind: "flagged"; reason: string } | { kind: "dismissed" };

/**
 * D42 desk prompt: when the gauge or the rain says the water is rising, the waiting families to re-confirm first.
 * Call back, flag urgent (with a reason, tier 1b → RED on every team list) or dismiss. Nothing changes by itself.
 * The friend's desk can drop this panel in; decisions here are local until the API stores them.
 */
export function RisingWaterPanel({ areaId = "P-B", onCount }: { areaId?: string; onCount?: (n: number) => void }) {
  const { t: tr } = useLang();
  const v = useView<RisingWaterView[]>(`views/risingWater/${areaId}`);
  const t = useMinute();
  const team = useTeam();
  const [done, setDone] = useState<Record<string, Decision>>({});
  useEffect(() => void loadTeam("T-S"), []);

  useEffect(() => { if (v.status === "ready") onCount?.(pickSnapshot(v.data, t)?.prompt?.reconfirm.length ?? 0); }, [v, t, onCount]);
  if (v.status === "loading") return <Skeleton lines={4} />;
  if (v.status !== "ready") return <Banner kind="error">{tr(S.desk.waterError)}</Banner>;
  const s = pickSnapshot(v.data, t);
  if (!s) return null;
  const p = s.prompt;
  const red = new Set(team.status === "ready" ? team.view.open.filter((l) => l.colour === "red").map((l) => l.listingId) : []);

  return (
    <section className="rising" aria-label={tr(S.desk.waterTab)}>
      <header className="rising-head">
        <Icon name="water" size={20} />
        <div>
          <h2>{p ? p.title : `${tr(S.desk.river)}, ${areaId}`}</h2>
          {s.gaugeLine && <p className="fine-print">{s.gaugeLine}</p>}
          {p?.signals
            .filter((x) => x.kind !== "gauge_reading")
            .map((x) => (
              <p key={x.kind + x.since} className="rising-signal">
                {x.text}
              </p>
            ))}
          {p?.rise && <p className="rising-signal num">{p.rise.text}</p>}
        </div>
      </header>
      {!p ? (
        <p className="muted">{tr(S.desk.waterQuiet)}</p>
      ) : (
        <>
          <ol className="rising-list">
            {p.reconfirm.map((r) => (
              <Row key={r.listingId} r={r} decision={done[r.listingId]} isRed={red.has(r.listingId)}
                   onDecide={(d) => setDone((x) => ({ ...x, [r.listingId]: d }))} />
            ))}
          </ol>
          {p.more > 0 && <p className="fine-print">{tr(S.desk.more(p.more))}</p>}
          <p className="fine-print">{p.note}</p>
        </>
      )}
    </section>
  );
}

function Row({ r, decision, isRed, onDecide }: { r: ReconfirmRow; decision?: Decision; isRed: boolean; onDecide: (d: Decision) => void }) {
  const { t: tr } = useLang();
  const [flagging, setFlagging] = useState(false);
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const submit = async () => {
    const res = await flagUrgent(r.listingId, reason, confirmed);
    if (!res.ok) return setError(res.message);
    setFlagging(false);
    onDecide({ kind: "flagged", reason: reason.trim() });
  };
  return (
    <li className={`rising-row ${decision?.kind === "dismissed" ? "is-dismissed" : ""}`}>
      <div className="rising-row-top">
        <strong className="num">{r.caseId}</strong>
        <span>{r.label}</span>
        <span className="muted">{r.people}</span>
      </div>
      <p className="rising-reasons">{r.reasons.join(" · ")}</p>
      {r.ifItRises && (
        <p className={`rising-estimate ${r.ifItRises.mayBeOverHead ? "is-high" : ""}`}>
          {r.ifItRises.text}
        </p>
      )}
      {isRed || decision?.kind === "flagged" ? (
        <p className="rising-done">{tr(S.desk.flagged)}{decision?.kind === "flagged" ? `: ${decision.reason}` : ""}</p>
      ) : decision?.kind === "dismissed" ? (
        <p className="rising-done muted">{tr(S.desk.dismissed)}</p>
      ) : flagging ? (
        <div className="rising-flag">
          <label>
            {tr(S.desk.flagReason)}
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder={tr(S.desk.flagExample)} autoFocus />
          </label>
          <label className="rising-check">
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            {tr(S.desk.confirmed)}
          </label>
          {error && <p className="field-error">{error}</p>}
          <div className="rising-actions">
            <BigButton size="md" onClick={submit} disabled={!reason.trim()}>{tr(S.desk.flagUrgent)}</BigButton>
            <BigButton size="md" variant="secondary" onClick={() => setFlagging(false)}>{tr(S.desk.cancel)}</BigButton>
          </div>
        </div>
      ) : (
        <div className="rising-actions">
          <BigButton size="md" variant={decision?.kind === "called" ? "secondary" : "primary"} onClick={() => onDecide({ kind: "called" })}>
            {decision?.kind === "called" ? tr(S.desk.callbackAsked) : tr(S.desk.callback)}
          </BigButton>
          <BigButton size="md" variant="secondary" onClick={() => setFlagging(true)}>{tr(S.desk.flagUrgent)}</BigButton>
          <BigButton size="md" variant="secondary" onClick={() => onDecide({ kind: "dismissed" })}>{tr(S.desk.dismiss)}</BigButton>
        </div>
      )}
    </li>
  );
}

/** Coordinator desk, until the friend's desk lands: the water-rising panel first. */
export function DeskPage() {
  const { t } = useLang();
  // ?tab=boat or ?tab=quiet opens that tab (the /demo "moments" link straight to them)
  const [tab, setTab] = useState(() => {
    const wanted = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("tab");
    return wanted && ["review", "water", "boat", "quiet"].includes(wanted) ? wanted : "review";
  });
  const [reviewCount, setReviewCount] = useState<number>();
  const [waterCount, setWaterCount] = useState<number>();
  const [quietCount, setQuietCount] = useState<number>();
  const counts: Record<string, number | undefined> = { review: reviewCount, water: waterCount, quiet: quietCount };
  const tabs = [ ["review", S.desk.review, "list"], ["water", S.desk.waterTab, "water"], ["boat", S.desk.boatTab, "pause"], ["quiet", S.desk.quietTab, "map"] ] as const;
  return <div className="page desk-page">
    <header className="page-head"><h1>{t(S.desk.title)}</h1><p className="muted">{t(S.desk.intro)}</p></header>
    <div className="desk-tabs" role="group" aria-label={t(S.desk.title)}>
      {tabs.map(([id, label, icon]) => <button key={id} aria-pressed={tab === id} onClick={() => setTab(id)}><Icon name={icon} />{t(label)}{counts[id] !== undefined && <span className="num">({counts[id]})</span>}</button>)}
    </div>
    <div hidden={tab !== "review"}><ReviewQueue onCount={setReviewCount} /></div>
    <div hidden={tab !== "water"}><RisingWaterPanel onCount={setWaterCount} /></div>
    <div hidden={tab !== "boat"}><ResourceFailure /></div>
    <div hidden={tab !== "quiet"}><SuggestedChecks onCount={setQuietCount} /></div>
  </div>;
}
