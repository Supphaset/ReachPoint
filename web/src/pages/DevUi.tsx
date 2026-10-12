import { useState } from "react";
import { Banner, BigButton, CountBadge, EstimateRange, LastUpdated, PriorityBadge, ProposalCard, Skeleton, StatusChip } from "../ui/components";
import { JOB, REVIEW, SEGMENT } from "../ui/states";
import "./pages.css";

const SWATCHES = [
  "brand", "red", "yellow", "green", "waiting", "taken", "moving", "held", "done", "unknown", "ai", "offline",
];

/** Every shared component in every state (C10 test plan). Your friend builds call, desk and resident screens from these. */
export function DevUi() {
  const [busy, setBusy] = useState(false);
  return (
    <div className="page dev-ui">
      <h1>Shared components</h1>
      <p className="muted">
        Import from <code>src/ui/components</code>. Colours, fonts and spacing come only from <code>src/ui/tokens.css</code>;
        <code> npm run check:tokens</code> fails on raw colours.
      </p>

      <section>
        <h2>Priority badge</h2>
        <div className="dev-row">
          <PriorityBadge priority="red" />
          <PriorityBadge priority="yellow" />
          <PriorityBadge priority="green" />
        </div>
        <div className="dev-row">
          <PriorityBadge priority="red" lang="en" size="sm" />
          <PriorityBadge priority="yellow" lang="en" size="sm" />
          <PriorityBadge priority="green" lang="en" size="sm" />
        </div>
      </section>

      <section>
        <h2>Status chip</h2>
        <p className="muted">Job states</p>
        <div className="dev-row">
          {Object.keys(JOB).map((s) => (
            <StatusChip key={s} kind="job" state={s} />
          ))}
        </div>
        <p className="muted">Segment checks</p>
        <div className="dev-row">
          {Object.keys(SEGMENT).map((s) => (
            <StatusChip key={s} kind="segment" state={s} />
          ))}
        </div>
        <p className="muted">Review</p>
        <div className="dev-row">
          {Object.keys(REVIEW).map((s) => (
            <StatusChip key={s} kind="review" state={s} />
          ))}
        </div>
        <p className="muted">Count badge</p>
        <div className="dev-row">
          <CountBadge urgent={2} unreviewed={1} />
          <CountBadge urgent={0} unreviewed={3} />
          <CountBadge urgent={0} unreviewed={0} empty />
        </div>
      </section>

      <section>
        <h2>AI proposal card</h2>
        <ProposalCard
          title="Assistance request: evacuation, 3 people"
          quote="ตอนนี้ครอบครัวเราอยู่ที่อาคารชุมชน มีสามคน"
          onApprove={() => setBusy(true)}
          onReject={() => setBusy(false)}
          busy={busy}
        >
          <p className="muted">Machine translation, unreviewed: “Our household is at the community building now. There are three of us.”</p>
        </ProposalCard>
        <ProposalCard title="Read-only draft (no actions)" />
      </section>

      <section>
        <h2>Banners</h2>
        <Banner kind="offline">ข้อมูลล่าสุดเมื่อ 10:32 · Last updated 10:32, reconnecting</Banner>
        <Banner kind="stale">This briefing is old. Check with the desk before you go.</Banner>
        <Banner kind="overdue">ยังพักไว้ · การอัปเดตล่าช้า / Still on hold, update overdue. The coordinator desk has been alerted.</Banner>
        <Banner kind="error" action={{ label: "Try again", onClick: () => {} }}>
          Already taken by T-S.
        </Banner>
        <Banner kind="info">Map unavailable. List and briefing still work.</Banner>
      </section>

      <section>
        <h2>Last updated, estimate, loading</h2>
        <LastUpdated at="2026-10-11T03:15:00Z" />
        <LastUpdated at="2026-10-11T00:35:00Z" offline />
        <EstimateRange range="7,900–13,000">live here</EstimateRange>
        <Skeleton lines={3} />
      </section>

      <section>
        <h2>Big buttons</h2>
        <div className="dev-grid">
          <BigButton icon="hand">Take this family</BigButton>
          <BigButton variant="secondary">Hand back</BigButton>
          <BigButton variant="quiet">Ask desk to re-confirm</BigButton>
          <BigButton disabled>Needs 5 seats, you have 4</BigButton>
        </div>
      </section>

      <section>
        <h2>Colour tokens</h2>
        <div className="dev-grid">
          {SWATCHES.map((n) => (
            <div key={n} className="swatch">
              <i style={{ background: `var(--color-${n})` }} />
              <code>--color-{n}</code>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Screen states to check</h2>
        <div className="dev-links">
          <a href="/team/map/P-B">P-B normal</a>
          <a href="/team/map/P-B/B-3">B-3 zone briefing</a>
          <a href="/team/map/P-B/B-4">B-4 quiet zone (no reports)</a>
          <a href="/team/map/P-B?variant=empty">Empty: no reports yet</a>
          <a href="/team/map/P-B?variant=stale">Stale briefing</a>
          <a href="/team/map/P-B?offline=1">Offline</a>
          <a href="/team/map/P-B?variant=layer-missing">Flood layer missing</a>
          <a href="/team/map/P-B?fail=tiles">Map failed</a>
          <a href="/team/map/P-B?fail=view">View failed</a>
          <a href="/team/map/P-C">P-C no recent assessment</a>
        </div>
      </section>
    </div>
  );
}
