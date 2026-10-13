import { useEffect, useState } from "react";
import type { CallCase, CallSession } from "../../data/call";
import { useLang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { BigButton } from "../../ui/components";
import { Icon } from "../../ui/Icon";

const groups = [
  { title: "casePeople", fields: ["people_count", "people_details", "children_count", "elderly_count", "mobility_needs", "reporter_name"] },
  { title: "casePlace", fields: ["location", "landmark", "coordinates"] },
  { title: "caseSituation", fields: ["water_level", "water_trend", "current_shelter", "injuries"] },
  { title: "caseNeeds", fields: ["urgent_needs", "callback_contact"] },
] as const satisfies readonly { title: "casePeople" | "casePlace" | "caseSituation" | "caseNeeds"; fields: readonly (keyof CallCase)[] }[];

// Seven core details the assistant asks for; extra facts remain visible when supplied.
const progressFields = ["people_count", "people_details", "mobility_needs", "location", "water_level", "urgent_needs", "injuries"] as const;

export function CallCaseSidebar({ session, busy, onConfirm }: { session: CallSession; busy: boolean; onConfirm: () => void }) {
  const { t, lang } = useLang();
  const [expanded, setExpanded] = useState(false);
  useEffect(() => { if (session.canConfirm) setExpanded(true); }, [session.canConfirm]);

  const known = progressFields.filter(field => session.case[field] !== null).length;
  const missing = groups.flatMap(group => group.fields).filter(field => session.case[field] === null && !session.case.unavailable_fields.includes(field));

  return <aside className="call-case" aria-label={t(S.call.conversation.caseTitle)}>
    <div className="call-case-head">
      <div>
        <div className="call-case-title"><h2>{t(S.call.conversation.caseTitle)}</h2><span className="call-case-count" aria-label={t(S.call.conversation.caseCollected(known, progressFields.length))}>{known}/{progressFields.length}</span></div>
        <p className="fine-print">{t(S.call.conversation.caseHint)}</p>
      </div>
      <button className="call-case-toggle" type="button" aria-expanded={expanded} aria-controls="call-case-content" onClick={() => setExpanded(!expanded)}>
        <span className="visually-hidden">{t(expanded ? S.call.conversation.caseHide : S.call.conversation.caseShow)}</span>
        <Icon name="chevron" size={20} />
      </button>
    </div>
    <div id="call-case-content" className={`call-case-content ${expanded ? "is-open" : ""}`}>
      {session.case.immediate_danger && <p className="call-case-alert"><Icon name="octagon" size={18} />{t(S.call.conversation.caseDanger)}</p>}
      {session.case.contradictions.length > 0 && <div className="call-case-conflict">
        <strong>{t(S.call.conversation.caseConflict)}</strong>
        <ul>{session.case.contradictions.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>}
      {groups.map((group) => {
        const rows = group.fields.filter(field => session.case[field] !== null || session.case.unavailable_fields.includes(field));
        if (!rows.length) return null;
        return <section className="call-case-group" key={group.title}>
          <h3>{t(S.call.conversation[group.title])}</h3>
          <dl>{rows.map((field) => {
            const value = session.case[field];
            const declined = value === null;
            return <div className="call-case-row" key={field}>
              <dt>{t(S.call.conversation.caseFields[field])}</dt>
              <dd className={declined ? "is-unknown" : ""}>{declined ? t(S.call.conversation.caseSkipped) : seedText(String(value), lang)}</dd>
            </div>;
          })}</dl>
        </section>;
      })}
      {missing.length > 0 && <p className="call-case-needed">{t(S.call.conversation.caseStillNeeded(missing.map(field => t(S.call.conversation.caseFields[field])).join(", ")))}</p>}
      {session.locationLookup.status === "confirmed" && <p className="fine-print">{t(S.call.conversation.selected)}: {session.locationLookup.label || session.locationLookup.query}</p>}
      {session.summary && <section className="call-case-confirm" aria-label={t(S.call.conversation.confirmTitle)}>
        <h3>{t(S.call.conversation.confirmTitle)}</h3>
        <p>{t(S.call.conversation.correction)}</p>
        <BigButton onClick={onConfirm} disabled={!session.canConfirm || busy}>{busy ? t(S.call.sending) : t(S.call.conversation.confirm)}</BigButton>
      </section>}
    </div>
  </aside>;
}
