import { useEffect, useState } from "react";
import type { ReconfirmRow, RisingWaterView } from "../../data/contract";
import { flagUrgent, loadTeam, useTeam } from "../../data/teamStore";
import { useView } from "../../data/useView";
import { Banner, BigButton, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";
import { pickSnapshot, useMinute } from "../briefing/Rain";
import { ReviewQueue } from "./ReviewQueue";
import "./desk.css";

type Decision = { kind: "called" } | { kind: "flagged"; reason: string } | { kind: "dismissed" };

/**
 * D42 desk prompt: when the gauge or the rain says the water is rising, the waiting families to re-confirm first.
 * Call back, flag urgent (with a reason, tier 1b → RED on every team list) or dismiss. Nothing changes by itself.
 * The friend's desk can drop this panel in; decisions here are local until the API stores them.
 */
export function RisingWaterPanel({ areaId = "P-B" }: { areaId?: string }) {
  const v = useView<RisingWaterView[]>(`views/risingWater/${areaId}`);
  const t = useMinute();
  const team = useTeam();
  const [done, setDone] = useState<Record<string, Decision>>({});
  useEffect(() => void loadTeam("T-S"), []);

  if (v.status === "loading") return <Skeleton lines={4} />;
  if (v.status !== "ready") return <Banner kind="error">Water-rising view unavailable.</Banner>;
  const s = pickSnapshot(v.data, t);
  if (!s) return null;
  const p = s.prompt;
  const red = new Set(team.status === "ready" ? team.view.open.filter((l) => l.colour === "red").map((l) => l.listingId) : []);

  return (
    <section className="rising" aria-label="Water rising">
      <header className="rising-head">
        <Icon name="water" size={20} />
        <div>
          <h2>{p ? p.title : `River and rain, ${areaId}`}</h2>
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
        <p className="muted">Nothing says the water is rising right now.</p>
      ) : (
        <>
          <ol className="rising-list">
            {p.reconfirm.map((r) => (
              <Row key={r.listingId} r={r} decision={done[r.listingId]} isRed={red.has(r.listingId)}
                   onDecide={(d) => setDone((x) => ({ ...x, [r.listingId]: d }))} />
            ))}
          </ol>
          {p.more > 0 && <p className="fine-print">{p.more} more waiting families are lower on this list.</p>}
          <p className="fine-print">{p.note}</p>
        </>
      )}
    </section>
  );
}

function Row({ r, decision, isRed, onDecide }: { r: ReconfirmRow; decision?: Decision; isRed: boolean; onDecide: (d: Decision) => void }) {
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
        <p className="rising-done">Flagged urgent{decision?.kind === "flagged" ? `: ${decision.reason}` : ""}. RED on the team lists now.</p>
      ) : decision?.kind === "dismissed" ? (
        <p className="rising-done muted">Dismissed</p>
      ) : flagging ? (
        <div className="rising-flag">
          <label>
            Reason (what the family said, or why)
            <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Callback: water at the 2nd floor, 2 children" autoFocus />
          </label>
          <label className="rising-check">
            <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />
            Confirmed with the family just now
          </label>
          {error && <p className="field-error">{error}</p>}
          <div className="rising-actions">
            <BigButton size="md" onClick={submit} disabled={!reason.trim()}>Flag urgent</BigButton>
            <BigButton size="md" variant="secondary" onClick={() => setFlagging(false)}>Cancel</BigButton>
          </div>
        </div>
      ) : (
        <div className="rising-actions">
          <BigButton size="md" variant={decision?.kind === "called" ? "secondary" : "primary"} onClick={() => onDecide({ kind: "called" })}>
            {decision?.kind === "called" ? "Callback asked" : "Call back"}
          </BigButton>
          <BigButton size="md" variant="secondary" onClick={() => setFlagging(true)}>Flag urgent</BigButton>
          <BigButton size="md" variant="secondary" onClick={() => onDecide({ kind: "dismissed" })}>Dismiss</BigButton>
        </div>
      )}
    </li>
  );
}

/** Coordinator desk, until the friend's desk lands: the water-rising panel first. */
export function DeskPage() {
  return (
    <div className="page narrow desk-page">
      <header className="page-head">
        <h1>Coordinator desk</h1>
        <p className="muted">Requests to review, then water rising (D42). Suggested checks and zone missions come next.</p>
      </header>
      <ReviewQueue />
      <RisingWaterPanel />
    </div>
  );
}
