import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { useEffect, useState } from "react";
import { dismissCheck, publishMission } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useView } from "../../data/useView";
import { Banner, BigButton, Skeleton } from "../../ui/components";

interface ZoneOrderView {
  suggestedChecks: { suggestionId: string; zoneId: string; areaId: string; reasons: string[] }[];
}

/** Suggested checks (D18): zones with flood evidence, no calls and no recent check. Publish or dismiss; nothing
 * is published automatically. Publishing makes a zone mission teams can take segment by segment. */
export function SuggestedChecks({ onCount }: { onCount?: (n: number) => void }) {
  const { t: tr } = useLang();
  const [n, setN] = useState(0);
  const v = useView<ZoneOrderView>(apiMode() ? `views/zoneOrder?r=${n}` : null);
  useEffect(() => { if (v.status === "ready") onCount?.(v.data.suggestedChecks.length); }, [v, onCount]);
  if (!apiMode()) return null;
  if (v.status === "loading") return <Skeleton lines={2} />;
  if (v.status !== "ready") return <Banner kind="error">{tr(S.desk.checksError)}</Banner>;
  const checks = v.data.suggestedChecks;
  return (
    <section className="review" aria-label={tr(S.desk.checksTitle)}>
      <h2>{tr(S.desk.checksTitle)} ({checks.length})</h2>
      <p className="muted">{tr(S.desk.checksBody)}</p>
      {checks.slice(0, 3).map((c) => <Check key={c.suggestionId} c={c} onDone={() => setN((x) => x + 1)} />)}
      {checks.length > 3 && <p className="fine-print">{tr(S.desk.more(checks.length - 3))}</p>}
    </section>
  );
}

function Check({ c, onDone }: { c: ZoneOrderView["suggestedChecks"][number]; onDone: () => void }) {
  const { t: tr } = useLang();
  const [dismissing, setDismissing] = useState(false);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const run = async (p: Promise<{ ok: boolean; message?: string }>) => {
    const r = await p;
    if (!r.ok) return setMsg(r.message ?? tr(S.desk.error));
    onDone();
  };
  return (
    <article className="review-row">
      <strong>{tr(S.desk.zone)} {c.zoneId}</strong>
      <ul className="review-facts">{c.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
      {msg && <Banner kind="error">{msg}</Banner>}
      {dismissing ? (
        <div className="review-form">
          <label htmlFor={`dismiss-${c.zoneId}`}>
            {tr(S.desk.whyDismiss)}
            <input id={`dismiss-${c.zoneId}`} value={reason} onChange={(e) => setReason(e.target.value)} placeholder={tr(S.desk.dismissExample)} />
          </label>
          <div className="review-actions">
            <BigButton size="md" onClick={() => run(dismissCheck(c.zoneId, reason))} disabled={!reason.trim()}>{tr(S.desk.dismissCheck)}</BigButton>
            <BigButton size="md" variant="secondary" onClick={() => setDismissing(false)}>{tr(S.desk.cancel)}</BigButton>
          </div>
        </div>
      ) : (
        <div className="review-actions">
          <BigButton size="md" onClick={() => run(publishMission(c.zoneId, c.reasons))}>{tr(S.desk.publish)}</BigButton>
          <BigButton size="md" variant="secondary" onClick={() => setDismissing(true)}>{tr(S.desk.dismiss)}</BigButton>
        </div>
      )}
    </article>
  );
}
