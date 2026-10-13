import { useLang, type Pair } from "../i18n/lang";
import { S } from "../i18n/strings";
import { Icon } from "./Icon";
import "./progress.css";

export function ProgressTracker({ steps, current, held = false, horizontal = false, label }: {
  steps: Pair[]; current: number | null; held?: boolean; horizontal?: boolean; label: Pair;
}) {
  const { t } = useLang();
  const tone = held ? "held" : current === null ? "unknown" :
    (horizontal ? ["taken", "taken", "moving", "moving", "done"] : ["waiting", "waiting", "taken", "moving", "done"])[current];
  return (
    <ol className={`progress-tracker ${horizontal ? "is-horizontal" : ""} ${held ? "is-held" : ""}`} aria-label={t(label)} data-tone={tone}>
      {steps.map((step, i) => {
        const active = i === current;
        const past = current !== null && i < current;
        return (
          <li key={i} className={active ? "is-current" : past ? "is-past" : "is-future"} aria-current={active ? "step" : undefined}>
            <span className="progress-marker"><Icon name={active && held ? "pause" : past ? "check" : active ? "hand" : "clock"} /></span>
            <span>{active && held ? t(S.progress.held) : t(step)}</span>
          </li>
        );
      })}
    </ol>
  );
}
