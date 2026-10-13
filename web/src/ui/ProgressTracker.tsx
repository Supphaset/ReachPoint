import { useLang, type Pair } from "../i18n/lang";
import { S } from "../i18n/strings";
import { Icon } from "./Icon";
import "./progress.css";

export function ProgressTracker({ steps, current, held = false, horizontal = false, label, tone: toneOverride, completedAt }: {
  steps: Pair[]; current: number | null; held?: boolean; horizontal?: boolean; label: Pair; tone?: "waiting" | "moving" | "done"; completedAt?: (string | null)[];
}) {
  const { t, lang } = useLang();
  const tone = held ? "held" : current === null ? "unknown" : toneOverride ??
    (horizontal ? ["taken", "taken", "moving", "moving", "done"] : ["waiting", "waiting", "taken", "moving", "done"])[current];
  return (
    <ol className={`progress-tracker ${horizontal ? "is-horizontal" : ""} ${held ? "is-held" : ""}`} aria-label={t(label)} data-tone={tone}>
      {steps.map((step, i) => {
        const active = i === current;
        const past = current !== null && i < current;
        const at = completedAt?.[i];
        return (
          <li key={i} className={active ? "is-current" : past ? "is-past" : "is-future"} aria-current={active ? "step" : undefined}>
            <span className="progress-marker"><Icon name={active && held ? "pause" : past || at ? "check" : active ? "hand" : "clock"} /></span>
            <span className="progress-step-label">{active && held ? t(S.progress.held) : t(step)}
              {completedAt && <small>{at ? <time dateTime={at}>{new Intl.DateTimeFormat(lang === "th" ? "th-TH" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" }).format(new Date(at))}</time> : past ? (lang === "th" ? "ไม่ทราบเวลาที่เสร็จสิ้น" : "Completion time unknown") : (lang === "th" ? "ยังไม่เสร็จสิ้น" : "Not completed")}</small>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
