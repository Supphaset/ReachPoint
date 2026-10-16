import { useEffect, useState } from "react";
import { ApiError, post, submissionId } from "../../data/api";
import { fmtTime } from "../../data/format";
import { apiMode } from "../../data/mode";
import { useSession } from "../../data/session";
import { useView } from "../../data/useView";
import { useLang } from "../../i18n/lang";
import { Banner, BigButton, Skeleton } from "../../ui/components";
import { Icon } from "../../ui/Icon";

export interface ReviewLocation {
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  source: string;
  status: "resolved" | "partial" | "unresolved";
  map_url: string | null;
}
export interface CallerReview {
  transport_recommendation: "boat" | "truck" | "needs_assessment";
  transport_threshold_cm?: number;
  reported_water_depth_cm?: number | null;
  transport_basis?: string;
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
  resolved_location?: ReviewLocation;
  approved?: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
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
  ai_processing?: boolean;
}
interface DeskView { callers: CallerRow[]; ai_enabled?: boolean; counts: { total: number; ai_read: number; human_reviewed: number; needs_review: number } }
type Words = (en: string, th: string) => string;

function areaName(row: CallerRow, w: Words) {
  if (!row.review_stale && row.review?.resolved_location?.address) return row.review.resolved_location.address;
  if (mapLink(row.location)) return w("Shared map location", "ตำแหน่งจากลิงก์แผนที่");
  return row.location?.trim() || w("Area not reported", "ยังไม่ระบุพื้นที่");
}

function mapLink(value: string | null | undefined) {
  try {
    const url = new URL(value ?? "");
    return url.protocol === "https:" && ["maps.app.goo.gl", "goo.gl", "maps.google.com", "maps.google.co.th", "google.com", "www.google.com", "google.co.th", "www.google.co.th"].includes(url.hostname) ? url.href : null;
  } catch { return null; }
}

function transportLabel(value: CallerReview["transport_recommendation"] | undefined, w: Words) {
  return value === "boat" ? w("Boat candidate", "เสนอเรือ") : value === "truck" ? w("Truck candidate", "เสนอรถบรรทุก") : w("Needs assessment", "ต้องประเมินการเข้าถึง");
}

function situation(row: CallerRow, w: Words) {
  return row.situation_details?.trim() || row.emergency_detail?.trim() || (row.type === "food" ? w("Food and drinking water", "อาหารและน้ำดื่ม") : row.type === "evacuation" ? w("Evacuation requested", "ขออพยพ") : w("Details not reported", "ยังไม่ระบุรายละเอียด"));
}

function emergencyLabel(row: CallerRow, w: Words) {
  const value = row.review?.emergency_level ?? row.reported_emergency_level;
  return levelLabel(value, w);
}

function levelLabel(value: CallerReview["emergency_level"] | undefined, w: Words) {
  return value === "1a" ? w("1a · Suspected medical", "1a · สงสัยฉุกเฉินการแพทย์") : value === "1b" ? w("1b · Urgent rescue", "1b · กู้ภัยเร่งด่วน") : value === "2" ? w("2 · Priority assistance", "2 · ช่วยเหลือลำดับสำคัญ") : value === "3" ? w("3 · Routine", "3 · ทั่วไป") : w("Unresolved", "ยังไม่ทราบ");
}

function CheckedBy({ row, w }: { row: CallerRow; w: Words }) {
  const human = row.review?.checked_by === "Human";
  const approved = row.review?.approved && !row.review_stale;
  return <span className={`caller-badge ${approved ? "caller-approved" : human ? "caller-human" : row.review?.checked_by === "AI" ? "caller-ai" : ""}`}>
    <Icon name={human ? "check" : row.review?.checked_by === "AI" ? "sparkle" : "question"} size={14} />
    {approved ? w("Human approved", "คนอนุมัติแล้ว") : row.ai_processing ? w("AI reviewing…", "AI กำลังตรวจสอบ…") : human ? w("Human reviewed · Awaiting approval", "คนตรวจแล้ว · รออนุมัติ") : row.review?.checked_by === "AI" ? w("AI reviewed · Awaiting approval", "AI ตรวจแล้ว · รอคนอนุมัติ") : w("Not reviewed", "ยังไม่ได้ตรวจสอบ")}
  </span>;
}

function NeedIndicators({ row, w }: { row: CallerRow; w: Words }) {
  if (row.review_stale) return null;
  const medication = row.review?.evidence.some(e => e.kind === "medication");
  const boat = row.review?.transport_recommendation === "boat";
  if (!medication && !boat) return null;
  return <span className="caller-need-tags">
    {medication && <span className="caller-need-tag caller-medication"><span aria-hidden="true">💊</span>{w("Medication reported", "แจ้งเรื่องยา")}</span>}
    {boat && <span className="caller-need-tag caller-boat"><span aria-hidden="true">🚤</span>{w("Boat suggested", "เสนอใช้เรือ")}</span>}
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
        <header className="caller-queue-head"><h2>{w("All requests", "คำขอทั้งหมด")}</h2><span className="num muted">{rows.length}</span></header>
        <p className="fine-print">{w("AI reviews automatically · Human approves", "AI ตรวจสอบอัตโนมัติ · คนอนุมัติ")}</p>
        <ol className="caller-requests">{rows.map(r => <li key={r.report_id}>
          <button type="button" className={`caller-request${r.review?.approved && !r.review_stale ? " is-approved" : ""}`} aria-pressed={r.report_id === current?.report_id} onClick={() => { setSelected(r.report_id); setMobileDetail(true); }}>
            <span className="caller-request-meta"><span>{r.report_id}</span>{r.received_at && <time dateTime={r.received_at}>{fmtTime(r.received_at)}</time>}</span>
            <strong className="caller-area">{areaName(r, w)}</strong>
            <NeedIndicators row={r} w={w} />
            <span className="caller-situation">{situation(r, w)}</span>
            <span className="caller-badges"><span className={`caller-badge ${r.immediate_danger ? "caller-danger-badge" : ""}`}>{r.immediate_danger && <Icon name="triangle" size={14} />}{emergencyLabel(r, w)}</span><CheckedBy row={r} w={w} /></span>
            {r.review_stale && <span className="fine-print">{w("Outdated review", "ผลตรวจสอบเก่า")}</span>}
          </button>
        </li>)}</ol>
      </aside>
      {current && <CallerDetail key={`${current.report_id}-${current.review?.review_revision ?? 0}-${current.input_revision}`} row={current} aiEnabled={v.data.ai_enabled !== false} offline={v.connection === "offline"} onBack={() => setMobileDetail(false)} onSaved={() => setRefresh(n => n + 1)} />}
    </div>}
  </section>;
}

function CallerDetail({ row, aiEnabled, offline, onBack, onSaved }: { row: CallerRow; aiEnabled: boolean; offline: boolean; onBack: () => void; onSaved: () => void }) {
  const { lang } = useLang();
  const { session } = useSession();
  const w: Words = (en, th) => lang === "th" ? th : en;
  const review = row.review;
  const location = review?.resolved_location;
  const [editing, setEditing] = useState(false);
  const [transport, setTransport] = useState<CallerReview["transport_recommendation"]>(review?.transport_recommendation ?? "needs_assessment");
  const [level, setLevel] = useState<NonNullable<CallerReview["emergency_level"]> | "">(review?.emergency_level ?? row.reported_emergency_level ?? "");
  const [danger, setDanger] = useState(row.immediate_danger);
  const [address, setAddress] = useState(location?.address ?? (mapLink(row.location) ? "" : row.location ?? ""));
  const [latitude, setLatitude] = useState(location?.latitude?.toString() ?? "");
  const [longitude, setLongitude] = useState(location?.longitude?.toString() ?? "");
  const [summary, setSummary] = useState(review?.volunteer_summary ?? "");
  const [reason, setReason] = useState("");
  const [reviewer, setReviewer] = useState(session?.actor ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [attempt, setAttempt] = useState<object>();
  const approved = !!review?.approved && !row.review_stale;
  const missing = [
    !row.phone_number?.trim() && w("Phone number", "เบอร์โทรศัพท์"),
    !row.type?.trim() && w("Help type", "ประเภทความช่วยเหลือ"),
    !row.location?.trim() && w("Submitted location", "ตำแหน่งที่ผู้แจ้งระบุ"),
  ].filter(Boolean);
  const canApprove = !row.review_stale && !missing.length && !!reviewer.trim();
  const source = location?.source === "google_maps_geocoding" ? "Google Maps" : location?.source === "google_maps_link" ? w("Google Maps link", "ลิงก์ Google Maps") : location?.source === "human" ? w("Human corrected", "คนแก้ไขแล้ว") : location?.source === "caller" ? w("Caller-reported", "ผู้แจ้งรายงาน") : w("Awaiting location lookup", "รอระบุตำแหน่ง");
  const maps = mapLink(location?.map_url) ?? mapLink(row.location);
  const save = async (action: "approve" | "correct" | "retry") => {
    if (offline || busy) return;
    if (action !== "retry" && danger && level && level !== "1a" && level !== "1b") {
      setError(w("Immediate danger must use level 1a or 1b.", "อันตรายทันทีต้องเป็นระดับ 1a หรือ 1b"));
      return;
    }
    setBusy(true); setError(undefined);
    const body = action === "retry" ? { submissionId: submissionId() } : attempt ?? {
      submissionId: submissionId(), input_revision: row.input_revision, expected_revision: review?.review_revision ?? 0,
      transport_recommendation: transport, emergency_level: level || null, immediate_danger: danger,
      volunteer_summary: summary.trim() || null, reviewed_by: reviewer,
      reason: action === "approve" ? w("Approved the operational review.", "อนุมัติผลตรวจสอบเพื่อปฏิบัติการ") : reason,
      approve: action === "approve",
      resolved_location: { address: address.trim() || null, latitude: latitude.trim() ? Number(latitude) : null,
        longitude: longitude.trim() ? Number(longitude) : null, source: location?.source ?? "human", status: location?.status ?? "unresolved", map_url: maps },
    };
    if (action !== "retry") setAttempt(body);
    try {
      await post(`/api/desk/${row.report_id}/${action === "retry" ? "ai-review" : "human-review"}`, body);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : w("Could not save review.", "บันทึกผลตรวจสอบไม่ได้"));
      if (e instanceof ApiError && e.status > 0) setAttempt(undefined);
    } finally { setBusy(false); }
  };
  const cancel = () => {
    setTransport(review?.transport_recommendation ?? "needs_assessment"); setLevel(review?.emergency_level ?? row.reported_emergency_level ?? "");
    setDanger(row.immediate_danger); setAddress(location?.address ?? (mapLink(row.location) ? "" : row.location ?? ""));
    setLatitude(location?.latitude?.toString() ?? ""); setLongitude(location?.longitude?.toString() ?? "");
    setSummary(review?.volunteer_summary ?? ""); setReason(""); setError(undefined); setEditing(false);
  };
  return <article className="caller-detail" aria-label={`${row.report_id} ${w("case details", "รายละเอียดคำขอ")}`}>
    <header className="caller-detail-head">
      <button type="button" className="caller-back" onClick={onBack}><Icon name="back" />{w("Back to requests", "กลับไปที่คำขอ")}</button>
      <div className="caller-request-meta"><span>{row.report_id} · {row.channel}{row.received_at && ` · ${fmtTime(row.received_at)}`}</span><CheckedBy row={row} w={w} /></div>
      <div><h2>{areaName(row, w)}</h2><p className="muted">{situation(row, w)}</p></div>
    </header>
    {row.immediate_danger && <p className="caller-danger"><Icon name="triangle" />{w("Immediate danger reported", "แจ้งอันตรายทันที")}</p>}
    <div className="caller-detail-body">
      {row.review_stale && <Banner kind="stale">{w("Caller details changed. Awaiting a new AI review; the previous approval no longer applies.", "ข้อมูลผู้แจ้งเปลี่ยนแล้ว รอ AI ตรวจสอบใหม่ ผลอนุมัติเดิมใช้ไม่ได้")}</Banner>}
      {(row.ai_processing || (!review && aiEnabled)) && <p className="caller-workflow" role="status"><Icon name="sparkle" />{w("AI is reviewing location, transport, urgency and preparation needs automatically.", "AI กำลังตรวจสอบตำแหน่ง การเดินทาง ความเร่งด่วน และสรุปเตรียมทีมอัตโนมัติ")}</p>}
      {!aiEnabled && !approved && <p className="fine-print">{w("Automatic AI review is unavailable. You can check and correct the details.", "AI ตรวจสอบอัตโนมัติยังไม่พร้อม สามารถตรวจสอบและแก้ไขข้อมูลได้")}</p>}
      {!editing ? <>
        <section className={`caller-ai-results ${approved ? "is-approved" : ""}`} aria-label={w("Review results", "ผลตรวจสอบ")}>
          <div className="caller-section-head"><h3><Icon name={review?.checked_by === "Human" ? "check" : "sparkle"} />{review?.checked_by === "Human" ? w("Review results", "ผลตรวจสอบ") : w("AI review", "AI ตรวจสอบ")}</h3><span className="fine-print">{approved ? w("Human approved", "คนอนุมัติแล้ว") : w("Awaiting human approval", "รอคนอนุมัติ")}</span></div>
          <section className="caller-location-result">
            <div className="caller-section-head"><h3>{w("Address & coordinates", "ที่อยู่และพิกัด")}</h3>{maps && <a href={maps} target="_blank" rel="noopener noreferrer">Google Maps <Icon name="map" size={14} /></a>}</div>
            <dl className="caller-key-facts">
              <div><dt>{w("Text address", "ที่อยู่ข้อความ")}</dt><dd>{location?.address || w("Needs location review", "ต้องตรวจสอบที่อยู่")}</dd></div>
              <div><dt>{w("Coordinates", "พิกัด")}</dt><dd>{location?.latitude != null && location?.longitude != null ? `${location.latitude}, ${location.longitude}` : w("Not resolved", "ยังระบุไม่ได้")}</dd></div>
            </dl>
            <p className="fine-print">{source}{location?.status !== "resolved" && ` · ${w("Incomplete", "ข้อมูลไม่ครบ")}`}</p>
          </section>
          <div className="caller-classifications">
            <div><span className="fine-print">{w("Transport", "การเดินทาง")}</span><strong>{transportLabel(review?.transport_recommendation, w)}</strong></div>
            <div><span className="fine-print">{w("Emergency level", "ระดับความเร่งด่วน")}</span><strong>{emergencyLabel(row, w)}</strong></div>
          </div>
          <p className="fine-print">{review?.reported_water_depth_cm != null
            ? w(`Reported water: ${review.reported_water_depth_cm} cm. `, `ระดับน้ำที่แจ้ง: ${review.reported_water_depth_cm} ซม. `)
            : review?.transport_basis === "qualitative_water"
            ? w("Boat suggested from reported waist/chest/head-level water; exact depth is unmeasured. ", "เสนอเรือจากรายงานน้ำถึงเอว/อก/ศีรษะ ยังไม่มีค่าความลึกที่วัดได้ ")
            : w("No measured water depth reported. ", "ยังไม่ได้แจ้งระดับน้ำเป็นตัวเลข ")}
            {w(`Boat planning preference starts at ${review?.transport_threshold_cm ?? 50} cm. Confirm field access before travel.`, `เกณฑ์เสนอเรือเริ่มที่ ${review?.transport_threshold_cm ?? 50} ซม. ต้องตรวจสอบการเข้าถึงจริงก่อนเดินทาง`)}</p>
          <details><summary>{w("Emergency evaluation guideline", "เกณฑ์ประเมินความเร่งด่วน")}</summary><ul>
            <li>{w("1a: Reported serious medical warning signs; qualified assessment required.", "1a: มีสัญญาณฉุกเฉินทางการแพทย์ ต้องให้ผู้มีคุณสมบัติประเมิน")}</li>
            <li>{w("1b: Immediate flood-rescue danger, such as rising water with no safe refuge.", "1b: อันตรายจากน้ำท่วมทันที เช่น น้ำกำลังขึ้นและไม่มีที่ปลอดภัย")}</li>
            <li>{w("2: Food, water, medication or evacuation assistance requested, pending any more urgent signs.", "2: แจ้งขออาหาร น้ำ ยาประจำ หรืออพยพ โดยยังไม่มีสัญญาณที่เร่งด่วนกว่า")}</li>
            <li>{w("3: Explicitly safe, routine and non-urgent circumstances.", "3: แจ้งชัดว่าปลอดภัย เป็นงานทั่วไป และไม่เร่งด่วน")}</li>
          </ul><p className="fine-print">{w("Missing information stays unresolved. Human approval is required.", "ข้อมูลไม่พอยังคงรอตรวจสอบ ต้องมีคนอนุมัติ")}</p></details>
          <section className="caller-prep-notes"><div className="caller-section-head"><h3>{w("Volunteer prep notes", "บันทึกเตรียมอาสาสมัคร")}</h3><span className="fine-print">{w("Optional", "ไม่บังคับ")}</span></div><p>{review?.volunteer_summary || w("No preparation notes. Approval does not require notes.", "ไม่มีบันทึกเตรียมทีม ไม่จำเป็นต่อการอนุมัติ")}</p></section>
          {!!review?.evidence.length && <details><summary>{w("Supporting caller quotes", "คำพูดผู้แจ้งที่ใช้อ้างอิง")}</summary><ul>{review.evidence.map((e, i) => <li key={i}><q>{e.quote}</q></li>)}</ul></details>}
          {!!review?.reasons.length && <details><summary>{w("Reasons & missing information", "เหตุผลและข้อมูลที่ยังขาด")}</summary><ul>{[...review.reasons, ...review.missing_information].map((text, i) => <li key={i}>{text}</li>)}</ul></details>}
        </section>
        <dl className="caller-contact-facts">{[[w("People", "ผู้ประสบภัย"), row.people_details], [w("Callback number", "เบอร์ติดต่อกลับ"), row.phone_number]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? w("Unknown", "ไม่ทราบ")}</dd></div>)}</dl>
        {review?.emergency_level === "1a" || row.reported_emergency_level === "1a" ? <p className="fine-print">{w("Suspected medical emergency; qualified assessment is not yet confirmed.", "สงสัยฉุกเฉินทางการแพทย์ ยังไม่ยืนยันการประเมินโดยผู้มีคุณสมบัติ")}</p> : null}
        <section className="caller-approval" aria-label={w("Human approval", "คนอนุมัติ")}>
          <div><h3>{approved ? w("Approved", "อนุมัติแล้ว") : w("Human approval", "คนอนุมัติ")}</h3><p className="fine-print">{approved ? `${review?.approved_by} · ${review?.approved_at ? fmtTime(review.approved_at) : ""}` : w("Check the AI results before approving.", "ตรวจสอบผลของ AI ก่อนอนุมัติ")}</p>
            <p className="fine-print">{w("Only phone, help type and submitted location are required. Other fields can be completed later.", "ต้องมีเพียงเบอร์โทรศัพท์ ประเภทความช่วยเหลือ และตำแหน่งที่ผู้แจ้งระบุ ข้อมูลอื่นเติมภายหลังได้")}</p>
            <p className="fine-print">{w("Approval advances caller tracking to Reviewing request. Team progress updates after a team accepts.", "เมื่ออนุมัติ หน้าติดตามจะแสดงขั้นตอนกำลังตรวจสอบคำขอ ความคืบหน้าของทีมจะแสดงเมื่อมีทีมรับงาน")}</p>
            {!approved && !!missing.length && <p className="fine-print">{w("Required: ", "ข้อมูลที่จำเป็น: ")}{missing.join(" · ")}</p>}
          </div>
          <div className="caller-approval-actions"><BigButton size="md" variant="secondary" disabled={busy || !!attempt || offline || !!row.ai_processing} onClick={() => setEditing(true)}>{w("Edit details", "แก้ไขข้อมูล")}</BigButton><BigButton size="md" icon="check" disabled={approved || !canApprove || busy || offline} onClick={() => save("approve")}>{busy ? w("Saving…", "กำลังบันทึก…") : attempt ? w("Retry saving approval", "ลองบันทึกอนุมัติอีกครั้ง") : approved ? w("Approved", "อนุมัติแล้ว") : w("Approve review", "อนุมัติผลตรวจสอบ")}</BigButton></div>
        </section>
      </> : <form className="caller-review-rail" onSubmit={e => { e.preventDefault(); void save("correct"); }}>
        <fieldset className="review-form desk-form" disabled={offline || busy || !!attempt}>
          <legend>{w("Correct review details", "แก้ไขผลตรวจสอบ")}</legend>
          <label>{w("Text address", "ที่อยู่ข้อความ")}<textarea value={address} maxLength={1000} onChange={e => setAddress(e.target.value)} /></label>
          <div className="caller-coordinate-inputs"><label>{w("Latitude", "ละติจูด")}<input type="number" step="any" min={-90} max={90} value={latitude} onChange={e => setLatitude(e.target.value)} /></label><label>{w("Longitude", "ลองจิจูด")}<input type="number" step="any" min={-180} max={180} value={longitude} onChange={e => setLongitude(e.target.value)} /></label></div>
          <label>{w("Transport", "การเดินทาง")}<select value={transport} onChange={e => setTransport(e.target.value as CallerReview["transport_recommendation"])}>{(["needs_assessment", "boat", "truck"] as const).map(value => <option key={value} value={value}>{transportLabel(value, w)}</option>)}</select></label>
          <label>{w("Emergency level", "ระดับความเร่งด่วน")}<select value={level} onChange={e => setLevel(e.target.value as typeof level)}><option value="">{w("Unresolved", "ยังไม่ทราบ")}</option>{(["1a", "1b", "2", "3"] as const).map(value => <option key={value} value={value}>{levelLabel(value, w)}</option>)}</select></label>
          <label className="inline"><input type="checkbox" checked={danger} onChange={e => setDanger(e.target.checked)} />{w("Immediate danger reported", "แจ้งอันตรายทันที")}</label>
          <label>{w("Volunteer prep notes (optional)", "บันทึกเตรียมอาสาสมัคร (ไม่บังคับ)")}<textarea value={summary} maxLength={2000} onChange={e => setSummary(e.target.value)} /></label>
          <label>{w("Correction reason", "เหตุผลการแก้ไข")}<textarea value={reason} required maxLength={1000} onChange={e => setReason(e.target.value)} /></label>
          {!session?.actor && <label>{w("Reviewed by", "ผู้ตรวจสอบ")}<input value={reviewer} required maxLength={100} onChange={e => setReviewer(e.target.value)} /></label>}
        </fieldset>
        <div className="caller-approval-actions"><BigButton size="md" variant="secondary" disabled={busy || !!attempt} onClick={cancel}>{w("Cancel", "ยกเลิก")}</BigButton><BigButton type="submit" size="md" disabled={offline || busy || !reason.trim() || !reviewer.trim()}>{attempt ? w("Retry saving corrections", "ลองบันทึกแก้ไขอีกครั้ง") : w("Save corrections", "บันทึกแก้ไข")}</BigButton></div>
        <p className="fine-print">{w("Corrections are saved for review. Approve after checking the updated results.", "บันทึกแก้ไขเพื่อทบทวน อนุมัติหลังตรวจสอบผลที่ปรับแล้ว")}</p>
      </form>}
      {error && <Banner kind="error">{error}</Banner>}
      {aiEnabled && !row.ai_processing && review?.checked_by == null && !!review && <BigButton size="md" variant="quiet" disabled={busy || !!attempt || offline} onClick={() => save("retry")}>{w("Retry AI review", "ลองให้ AI ตรวจสอบอีกครั้ง")}</BigButton>}
      <details className="caller-full-report"><summary>{w("Full caller report & details", "ข้อมูลผู้แจ้งและรายละเอียดทั้งหมด")}</summary><dl className="caller-facts">{([
        [w("Contact", "ติดต่อ"), row.phone_number], [w("People", "ผู้ประสบภัย"), row.people_details],
        [w("Children / older people / pets", "เด็ก / ผู้สูงอายุ / สัตว์เลี้ยง"), [row.n_children, row.n_elders, row.n_pets].map(n => n ?? "?").join(" / ")],
        [w("Reported location", "ตำแหน่งที่ผู้แจ้งส่ง"), row.location], [w("Reported coordinates", "พิกัดที่ผู้แจ้งส่ง"), row.coordinates],
        [w("Access details", "รายละเอียดตำแหน่ง"), row.location_details], [w("Water", "น้ำ"), row.water_level],
        [w("Situation", "สถานการณ์"), row.situation_details], [w("Emergency details", "เหตุฉุกเฉิน"), row.emergency_detail], [w("Other details", "ข้อมูลอื่น"), row.other_details],
      ] as [string, string | null][]).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? w("Unknown", "ไม่ทราบ")}</dd></div>)}</dl></details>
      {!!row.history.length && <details className="caller-full-report"><summary>{w("Review history", "ประวัติการตรวจสอบ")} ({row.history.length})</summary><ol>{row.history.map(r => <li key={r.review_revision}>{r.reviewed_at} · {r.approved ? w("Human approved", "คนอนุมัติแล้ว") : r.checked_by ?? r.source} · {r.emergency_level ?? "?"} · {r.transport_recommendation} · {r.reasons.join(" · ")}</li>)}</ol></details>}
    </div>
    <footer className="caller-detail-foot">{w("Operational approval · Route and medical assessment remain separate.", "อนุมัติเพื่อปฏิบัติการ · แยกจากการประเมินเส้นทางและการแพทย์")}</footer>
  </article>;
}
