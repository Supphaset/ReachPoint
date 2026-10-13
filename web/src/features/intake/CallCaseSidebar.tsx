import { useEffect, useState } from "react";
import type { CallCase, CallSession } from "../../data/call";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { BigButton } from "../../ui/components";
import { Icon } from "../../ui/Icon";

const groups = [
  { title: "casePeople", fields: ["people_count", "people_details", "children_count", "elderly_count", "mobility_needs", "reporter_name"] },
  { title: "casePlace", fields: ["location", "landmark", "coordinates"] },
  { title: "caseSituation", fields: ["water_level", "water_trend", "current_shelter", "injuries"] },
  { title: "caseNeeds", fields: ["urgent_needs", "callback_contact"] },
] as const satisfies readonly { title: "casePeople" | "casePlace" | "caseSituation" | "caseNeeds"; fields: readonly (keyof CallCase)[] }[];

export function CallCaseSidebar({ session, busy, onConfirm }: { session: CallSession; busy: boolean; onConfirm: () => void }) {
  const { t } = useLang();
  const [expanded, setExpanded] = useState(false);
  useEffect(() => { if (session.canConfirm) setExpanded(true); }, [session.canConfirm]);

  return <aside className="call-case" aria-label={t(S.call.conversation.caseTitle)}>
    <div className="call-case-head">
      <div>
        <h2>{t(S.call.conversation.caseTitle)}</h2>
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
      {groups.map((group) => <section className="call-case-group" key={group.title}>
        <h3>{t(S.call.conversation[group.title])}</h3>
        <dl>{group.fields.map((field) => {
          const value = session.case[field];
          const unknown = value === null;
          const declined = unknown && session.case.unavailable_fields.includes(field);
          return <div className="call-case-row" key={field}>
            <dt>{t(S.call.conversation.caseFields[field])}</dt>
            <dd className={unknown ? "is-unknown" : ""}>{declined ? t(S.call.conversation.caseDeclined) : unknown ? t(S.call.conversation.caseUnknown) : String(value)}</dd>
          </div>;
        })}</dl>
      </section>)}
      {session.locationLookup.status === "confirmed" && <p className="fine-print">{t(S.call.conversation.selected)}: {session.locationLookup.label || session.locationLookup.query}</p>}
      {session.summary && <section className="call-case-confirm" aria-label={t(S.call.conversation.confirmTitle)}>
        <h3>{t(S.call.conversation.confirmTitle)}</h3>
        <p>{t(S.call.conversation.correction)}</p>
        <BigButton onClick={onConfirm} disabled={!session.canConfirm || busy}>{busy ? t(S.call.sending) : t(S.call.conversation.confirm)}</BigButton>
      </section>}
    </div>
  </aside>;
}
