import { useState } from "react";
import { dismissCheck, publishMission } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { Banner, BigButton, Skeleton } from "../../ui/components";

interface ZoneOrderView {
  suggestedChecks: { suggestionId: string; zoneId: string; areaId: string; reasons: string[] }[];
}

/** Suggested checks (D18): zones with flood evidence, no calls and no recent check. Publish or dismiss; nothing
 * is published automatically. Publishing makes a zone mission teams can take segment by segment. */
export function SuggestedChecks() {
  const [n, setN] = useState(0);
  const v = useView<ZoneOrderView>(apiMode() ? `views/zoneOrder?r=${n}` : null);
  if (!apiMode()) return null;
  if (v.status === "loading") return <Skeleton lines={2} />;
  if (v.status !== "ready") return <Banner kind="error">Suggested checks unavailable.</Banner>;
  const checks = v.data.suggestedChecks;
  return (
    <section className="review" aria-label="Suggested checks">
      <h2>Suggested checks ({checks.length})</h2>
      <p className="muted">Zones where people may need help but nobody has called. Publish one as a zone mission for teams.</p>
      {checks.slice(0, 3).map((c) => <Check key={c.suggestionId} c={c} onDone={() => setN((x) => x + 1)} />)}
      {checks.length > 3 && <p className="fine-print">{checks.length - 3} more lower on the list.</p>}
    </section>
  );
}

function Check({ c, onDone }: { c: ZoneOrderView["suggestedChecks"][number]; onDone: () => void }) {
  const [dismissing, setDismissing] = useState(false);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const run = async (p: Promise<{ ok: boolean; message?: string }>) => {
    const r = await p;
    if (!r.ok) return setMsg(r.message ?? "Something went wrong");
    onDone();
  };
  return (
    <article className="review-row">
      <strong>Zone {c.zoneId}</strong>
      <ul className="review-facts">{c.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
      {msg && <Banner kind="error">{msg}</Banner>}
      {dismissing ? (
        <div className="review-form">
          <label htmlFor={`dismiss-${c.zoneId}`}>
            Why dismiss?
            <input id={`dismiss-${c.zoneId}`} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Checked by the army this morning" />
          </label>
          <div className="review-actions">
            <BigButton size="md" onClick={() => run(dismissCheck(c.zoneId, reason))} disabled={!reason.trim()}>Dismiss check</BigButton>
            <BigButton size="md" variant="secondary" onClick={() => setDismissing(false)}>Cancel</BigButton>
          </div>
        </div>
      ) : (
        <div className="review-actions">
          <BigButton size="md" onClick={() => run(publishMission(c.zoneId, c.reasons))}>Publish zone mission</BigButton>
          <BigButton size="md" variant="secondary" onClick={() => setDismissing(true)}>Dismiss</BigButton>
        </div>
      )}
    </article>
  );
}
