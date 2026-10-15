import { useEffect, useState } from "react";
import { ApiError, post, submissionId } from "../../data/api";
import { fmtTime } from "../../data/format";
import { apiMode } from "../../data/mode";
import { useSession } from "../../data/session";
import { useView } from "../../data/useView";
import { useLang } from "../../i18n/lang";
import { Banner, BigButton, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";

export interface CallerReview {
  transport_recommendation: "boat" | "truck" | "needs_assessment";
  emergency_level: "1a" | "1b" | "2" | "3" | null;
  checked_by: "AI" | "Human" | null;
  immediate_danger: boolean;
  review_status: "ai_read" | "human_review_required" | "human_reviewed";
  source: string;
  reviewed_by: string | null;
  reviewed_at: string;
  review_revision: number;
  volunteer_summary: string | null;
  reasons: string[];
  missing_information: string[];
  evidence: { field: string; quote: string; kind: string }[];
}
export interface CallerRow {
  report_id: string;
  type: "food" | "evacuation" | null;
  channel: string;
  phone_number: string | null;
  people_details: string | null;
  n_children: number | null;
  n_elders: number | null;
  n_pets: number | null;
  location: string | null;
  coordinates: string | null;
  location_details: string | null;
  water_level: string | null;
  situation_details: string | null;
  emergency_detail: string | null;
  other_details: string | null;
  input_revision: string;
  received_at: string | null;
  report_status: string;
  review_stale: boolean;
  immediate_danger: boolean;
  reported_emergency_level: "1a" | "1b" | null;
  review: CallerReview | null;
  history: CallerReview[];
}
interface DeskView { callers: CallerRow[]; counts: { total: number; ai_read: number; human_reviewed: number; needs_review: number } }
type Words = (en: string, th: string) => string;

function areaName(row: CallerRow, w: Words) {
  return row.location?.trim() || w("Area not reported", "ยังไม่ระบุพื้นที่");
}

function situation(row: CallerRow, w: Words) {
  return row.situation_details?.trim() || row.emergency_detail?.trim() || (row.type === "food" ? w("Food and drinking water", "อาหารและน้ำดื่ม") : row.type === "evacuation" ? w("Evacuation requested", "ขออพยพ") : w("Details not reported", "ยังไม่ระบุรายละเอียด"));
}

function emergencyLabel(row: CallerRow, w: Words) {
  const value = row.review?.emergency_level ?? row.reported_emergency_level;
  return value === "1a" ? w("1a · Suspected medical", "1a · สงสัยฉุกเฉินการแพทย์") : value === "1b" ? w("1b · Urgent rescue", "1b · กู้ภัยเร่งด่วน") : value === "2" ? w("2 · Priority assistance", "2 · ช่วยเหลือลำดับสำคัญ") : value === "3" ? w("3 · Routine", "3 · ทั่วไป") : w("Unresolved", "ยังไม่ทราบ");
}

function CheckedBy({ row, w }: { row: CallerRow; w: Words }) {
  const human = row.review?.checked_by === "Human";
  return <span className={`caller-badge ${human ? "caller-human" : row.review?.checked_by === "AI" ? "caller-ai" : ""}`}>
    <Icon name={human ? "check" : row.review?.checked_by === "AI" ? "sparkle" : "question"} size={14} />
    {human ? w("Human reviewed", "คนตรวจแล้ว") : row.review?.checked_by === "AI" ? w("AI reviewed", "AI ตรวจแล้ว") : w("Not reviewed", "ยังไม่ได้ตรวจสอบ")}
  </span>;
}

export function CallerDesk({ onCount }: { onCount?: (n: number) => void }) {
  const { lang } = useLang();
  const w = (en: string, th: string) => lang === "th" ? th : en;
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<string>();
  const [mobileDetail, setMobileDetail] = useState(false);
  const v = useView<DeskView>(apiMode() ? `desk?r=${refresh}` : null);
  useEffect(() => { if (v.status === "ready") onCount?.(v.data.callers.length); }, [v, onCount]);
  if (!apiMode()) return <Banner kind="info">{w("Open with ?data=api to review callers.", "เปิดด้วย ?data=api เพื่อตรวจสอบผู้แจ้ง")}</Banner>;
  if (v.status === "loading") return <Skeleton lines={3} />;
  if (v.status !== "ready") return <Banner kind="error">{w("Caller reviews unavailable.", "โหลดผลตรวจสอบผู้แจ้งไม่ได้")}</Banner>;
  const rows = v.data.callers;
  const current = rows.find(r => r.report_id === selected) ?? rows[0];
  return <section className="caller-desk" data-mobile-detail={mobileDetail} aria-label={w("Caller review workspace", "พื้นที่ตรวจสอบผู้แจ้ง")}>
    {v.connection === "offline" && <Banner kind="error">{w("Offline: showing the last loaded caller records.", "ออฟไลน์: แสดงข้อมูลผู้แจ้งที่โหลดไว้ล่าสุด")}</Banner>}
    {!rows.length && <p>{w("New confirmed caller requests will appear here.", "คำขอที่ผู้แจ้งยืนยันแล้วจะแสดงที่นี่")}</p>}
    {!!rows.length && <div className="caller-workspace">
      <aside className="caller-queue" aria-label={w("Caller request queue", "รายการคำขอผู้แจ้ง")}>
        <header className="caller-queue-head"><h2>{w("Requests", "คำขอช่วยเหลือ")}</h2><span className="num muted">{rows.length}</span></header>
        <p className="fine-print">{w("Immediate danger first", "อันตรายทันทีมาก่อน")} · {v.data.counts.ai_read} AI · {v.data.counts.human_reviewed} {w("Human", "คนตรวจแล้ว")}</p>
        <ol className="caller-requests">{rows.map(r => <li key={r.report_id}>
          <button type="button" className="caller-request" aria-pressed={r.report_id === current?.report_id} onClick={() => { setSelected(r.report_id); setMobileDetail(true); }}>
            <span className="caller-request-meta"><span>{r.report_id}</span>{r.received_at && <time dateTime={r.received_at}>{fmtTime(r.received_at)}</time>}</span>
            <strong className="caller-area">{areaName(r, w)}</strong>
            <span className="caller-situation">{situation(r, w)}</span>
            <span className="caller-badges"><span className={`caller-badge ${r.immediate_danger ? "caller-danger-badge" : ""}`}>{r.immediate_danger && <Icon name="triangle" size={14} />}{emergencyLabel(r, w)}</span><CheckedBy row={r} w={w} /></span>
            {r.review_stale && <span className="fine-print">{w("Outdated review", "ผลตรวจสอบเก่า")}</span>}
          </button>
        </li>)}</ol>
      </aside>
      {current && <CallerDetail key={`${current.report_id}-${current.review?.review_revision ?? 0}-${current.input_revision}`} row={current} offline={v.connection === "offline"} onBack={() => setMobileDetail(false)} onSaved={() => setRefresh(n => n + 1)} />}
    </div>}
  </section>;
}

function CallerDetail({ row, offline, onBack, onSaved }: { row: CallerRow; offline: boolean; onBack: () => void; onSaved: () => void }) {
  const { lang } = useLang();
  const { session } = useSession();
  const w = (en: string, th: string) => lang === "th" ? th : en;
  const review = row.review;
  const [transport, setTransport] = useState<CallerReview["transport_recommendation"]>(review?.transport_recommendation ?? "needs_assessment");
  const [level, setLevel] = useState<NonNullable<CallerReview["emergency_level"]> | "">(review?.emergency_level ?? row.reported_emergency_level ?? "");
  const [danger, setDanger] = useState(row.immediate_danger);
  const [summary, setSummary] = useState(review?.volunteer_summary ?? "");
  const [reason, setReason] = useState("");
  const [reviewer, setReviewer] = useState(session?.actor ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [id] = useState(submissionId);
  const [attempt, setAttempt] = useState<object>();
  const save = async (ai = false) => {
    if (offline || busy) return;
    if (!ai && danger && level !== "1a" && level !== "1b") {
      setError(w("Immediate danger must use level 1a or 1b.", "อันตรายทันทีต้องเป็นระดับ 1a หรือ 1b"));
      return;
    }
    setBusy(true); setError(undefined);
    const body = ai ? { submissionId: submissionId() } : attempt ?? { submissionId: id, input_revision: row.input_revision,
      expected_revision: review?.review_revision ?? 0, transport_recommendation: transport, emergency_level: level || null,
      immediate_danger: danger, volunteer_summary: summary.trim() || null, reason, reviewed_by: reviewer };
    if (!ai) setAttempt(body);
    try {
      await post(`/api/desk/${row.report_id}/${ai ? "ai-review" : "human-review"}`, body);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : w("Could not save review.", "บันทึกผลตรวจสอบไม่ได้"));
      if (e instanceof ApiError && e.status > 0) setAttempt(undefined);
    } finally { setBusy(false); }
  };
  return <article className="caller-detail" aria-label={`${row.report_id} ${w("case details", "รายละเอียดคำขอ")}`}>
    <header className="caller-detail-head">
      <button type="button" className="caller-back" onClick={onBack}><Icon name="back" />{w("Back to requests", "กลับไปที่คำขอ")}</button>
      <div className="caller-request-meta"><span>{row.report_id} · {row.channel}{row.received_at && ` · ${fmtTime(row.received_at)}`}</span><CheckedBy row={row} w={w} /></div>
      <div><h2>{areaName(row, w)}</h2><p className="muted">{situation(row, w)}</p></div>
    </header>
    {row.immediate_danger && <p className="caller-danger"><Icon name="triangle" />{w("Immediate danger reported", "แจ้งอันตรายทันที")}</p>}
    <div className="caller-detail-body">
      {row.review_stale && <Banner kind="stale">{w("Outdated review: caller details changed. Review the current report before confirming.", "ผลตรวจสอบเก่า: ข้อมูลผู้แจ้งเปลี่ยนแล้ว โปรดตรวจสอบข้อมูลปัจจุบันก่อนยืนยัน")}</Banner>}
      <div className="caller-preparation-layout">
        <div className="caller-preparation">
          <section className={`caller-summary ${review?.checked_by === "Human" ? "is-reviewed" : ""}`} aria-label={w("Volunteer preparation brief", "สรุปเพื่อเตรียมอาสาสมัคร")}>
            <h3><Icon name="sparkle" />{w("Volunteer preparation brief", "สรุปเพื่อเตรียมอาสาสมัคร")}</h3>
            <p className="fine-print">{review?.checked_by === "Human" ? w("Human reviewed", "คนตรวจแล้ว") : w("AI summary · optional", "AI สรุป · ไม่บังคับ")}</p>
            {review?.volunteer_summary ? <p>{review.volunteer_summary}</p> : <p className="muted">{w("No preparation summary available. Review can continue.", "ยังไม่มีสรุปเตรียมทีม สามารถตรวจสอบต่อได้")}</p>}
            {!!review?.evidence.length && <details><summary>{w("Supporting caller quotes", "คำพูดผู้แจ้งที่ใช้อ้างอิง")}</summary><ul>{review.evidence.map((e, i) => <li key={i}><q>{e.quote}</q></li>)}</ul></details>}
          </section>
          <dl className="caller-key-facts">{[[w("People", "ผู้ประสบภัย"), row.people_details], [w("Reported water", "ระดับน้ำที่แจ้ง"), row.water_level], [w("Callback number", "เบอร์ติดต่อกลับ"), row.phone_number]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? w("Unknown", "ไม่ทราบ")}</dd></div>)}</dl>
          {row.reported_emergency_level === "1a" || review?.emergency_level === "1a" ? <p className="fine-print">{w("Suspected medical emergency; qualified assessment is not yet confirmed.", "สงสัยฉุกเฉินทางการแพทย์ ยังไม่ยืนยันการประเมินโดยผู้มีคุณสมบัติ")}</p> : null}
          {review?.review_status === "human_review_required" && <p className="fine-print">{w("Human review required", "ต้องให้คนตรวจสอบ")}</p>}
          <BigButton size="md" variant="quiet" icon="sparkle" disabled={offline || busy || !!attempt || (review?.checked_by === "Human" && !row.review_stale)} onClick={() => save(true)}>{w("Run AI review", "ให้ AI ตรวจสอบ")}</BigButton>
        </div>
        <form className="caller-review-rail" onSubmit={e => { e.preventDefault(); void save(); }}>
          <fieldset className="review-form desk-form" disabled={offline || busy || !!attempt}>
            <legend>{w("Review recommendation", "ตรวจสอบข้อเสนอ")}</legend>
            <label>{w("Transport recommendation", "เสนอการเดินทาง")}<select value={transport} onChange={e => setTransport(e.target.value as CallerReview["transport_recommendation"])}><option value="needs_assessment">{w("Needs assessment", "ต้องประเมินการเข้าถึง")}</option><option value="boat">{w("Boat candidate", "เสนอเรือ")}</option><option value="truck">{w("Truck candidate", "เสนอรถบรรทุก")}</option></select></label>
            <label>{w("Emergency level", "ระดับความเร่งด่วน")}<select value={level} onChange={e => setLevel(e.target.value as typeof level)}><option value="">{w("Unresolved", "ยังไม่ทราบ")}</option><option value="1a">{w("1a · Suspected medical", "1a · สงสัยฉุกเฉินการแพทย์")}</option><option value="1b">{w("1b · Urgent rescue", "1b · กู้ภัยเร่งด่วน")}</option><option value="2">{w("2 · Priority assistance", "2 · ช่วยเหลือลำดับสำคัญ")}</option><option value="3">{w("3 · Routine", "3 · ทั่วไป")}</option></select></label>
            <label className="inline"><input type="checkbox" checked={danger} onChange={e => setDanger(e.target.checked)} />{w("Immediate danger reported", "แจ้งอันตรายทันที")}</label>
            <label>{w("Review / correction reason", "เหตุผลการตรวจสอบ / แก้ไข")}<textarea value={reason} required maxLength={1000} onChange={e => setReason(e.target.value)} /></label>
            <label>{w("Reviewed by", "ผู้ตรวจสอบ")}<input value={reviewer} required maxLength={100} onChange={e => setReviewer(e.target.value)} /></label>
            <details><summary>{w("Edit preparation summary (optional)", "แก้ไขสรุปเตรียมทีม (ไม่บังคับ)")}</summary><label>{w("Volunteer summary (optional)", "สรุปเตรียมทีม (ไม่บังคับ)")}<textarea value={summary} maxLength={2000} onChange={e => setSummary(e.target.value)} /></label></details>
          </fieldset>
          {error && <Banner kind="error">{error}</Banner>}
          <BigButton type="submit" size="md" icon="check" disabled={offline || busy || !reason.trim() || !reviewer.trim()}>{busy ? w("Saving…", "กำลังบันทึก…") : attempt ? w("Retry saving review", "ลองบันทึกอีกครั้ง") : w("Save human review", "บันทึกคนตรวจแล้ว")}</BigButton>
          <p className="fine-print">{w("Operational review; route and medical assessment remain separate.", "ตรวจสอบเพื่อปฏิบัติการ แยกจากการประเมินเส้นทางและการแพทย์")}</p>
        </form>
      </div>
      <details className="caller-full-report"><summary>{w("Full caller report & details", "ข้อมูลผู้แจ้งและรายละเอียดทั้งหมด")}</summary>
        <dl className="caller-facts">{([
      [w("Contact", "ติดต่อ"), row.phone_number], [w("People", "ผู้ประสบภัย"), row.people_details],
      [w("Children / older people / pets", "เด็ก / ผู้สูงอายุ / สัตว์เลี้ยง"), [row.n_children, row.n_elders, row.n_pets].map(n => n ?? "?").join(" / ")],
      [w("Location", "ตำแหน่ง"), row.location], [w("Coordinates", "พิกัด"), row.coordinates],
      [w("Access details", "รายละเอียดตำแหน่ง"), row.location_details], [w("Water", "น้ำ"), row.water_level],
      [w("Situation", "สถานการณ์"), row.situation_details], [w("Emergency details", "เหตุฉุกเฉิน"), row.emergency_detail],
      [w("Other details", "ข้อมูลอื่น"), row.other_details],
        ] as [string, string | null][]).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? w("Unknown", "ไม่ทราบ")}</dd></div>)}</dl>
        {review && <section className="caller-reasons"><h3>{w("Why this recommendation", "เหตุผลของข้อเสนอ")}</h3><p className="fine-print">{review.source} · {review.reviewed_at}{review.reviewed_by && ` · ${review.reviewed_by}`}</p><ul>{review.reasons.map(r => <li key={r}>{r}</li>)}</ul>{!!review.missing_information.length && <><h3>{w("Information to confirm", "ข้อมูลที่ต้องยืนยัน")}</h3><ul>{review.missing_information.map(r => <li key={r}>{r}</li>)}</ul></>}</section>}
      </details>
      {!!row.history.length && <details className="caller-full-report"><summary>{w("Review history", "ประวัติการตรวจสอบ")} ({row.history.length})</summary><ol>{row.history.map(r => <li key={r.review_revision}>{r.reviewed_at} · {r.checked_by ?? r.source} · {r.emergency_level ?? "?"} · {r.transport_recommendation} · {r.reasons.join(" · ")}</li>)}</ol></details>}
    </div>
    <footer className="caller-detail-foot">{w("Caller-reported · unverified", "ผู้แจ้งรายงาน · ยังไม่ยืนยัน")}</footer>
  </article>;
}
