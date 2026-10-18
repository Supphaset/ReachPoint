import { Tr, useT } from "./ui/lang";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { v2, vol, type CopilotResult, type Overview, type ZonePage as ZoneData, type Trip, type CopilotPlan, type Plan } from "./api";
import { useGeo, useTeam, VNavLinks } from "./volunteer/shared";
import { CopilotAnswer } from "./ui/Answer";
import { DepthRange, HonestyLabel, Panel, questions, StepHeader } from "./ui/Shared";
import { displayText, readerLabel } from "./ui/trace";
import { TripMap } from "./ui/TripMap";
export function PlanPage() {
  const t = useT();
  const [params] = useSearchParams();
  const geo = useGeo();
  const [team, setTeam] = useTeam();
  const initialQuestion = params.get('question') ?? ((params.get('zones') || params.get('zone')) ? `I have one boat with 6 seats. Plan for zone ${params.get('zones') ?? params.get('zone')}.` : questions[0]);
  const [question, setQuestion] = useState(initialQuestion);
  const [asked, setAsked] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CopilotResult | null>(null);
  const [error, setError] = useState('');
  const [overview, setOverview] = useState<Overview | null>(null);
  const [zone, setZone] = useState<ZoneData | null>(null);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [extra, setExtra] = useState('');
  const [eta, setEta] = useState('06:30');
  const [posted, setPosted] = useState<number | null>(null);
  const [posting, setPosting] = useState(false);
  const plan = result?.plan;
  const request = useRef(0);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      request.current++;
    };
  }, []);
  async function ask(prompt: string) {
    if (!prompt.trim() || busy)
      return;
    const id = ++request.current;
    setBusy(true);
    setError('');
    setAsked(prompt);
    setResult(null);
    setZone(null);
    setTrip(null);
    setPosted(null);
    setExtra('');
    try {
      const response = await vol.copilot(prompt);
      if (id === request.current)
        setResult(response);
    }
    catch (failure) {
      if (id === request.current)
        setError(String(failure));
    }
    finally {
      if (id === request.current)
        setBusy(false);
    }
  }
  const auto = useRef(false);
  useEffect(() => {
    if (auto.current || !(params.get('question') || params.get('zones') || params.get('zone')))
      return;
    const timer = window.setTimeout(() => {
      auto.current = true;
      void ask(initialQuestion);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);
  useEffect(() => {
    let active = true;
    const load = () => vol.overview().then(overall => {
      if (active)
        setOverview(overall);
    }, failure => {
      if (active)
        setError(String(failure));
    });
    void load();
    const timer = window.setInterval(load, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (!plan)
      return;
    setTrip(null);
    let active = true;
    const zones = [plan.zone, ...(extra.trim() ? [extra.trim()] : [])];
    const load = () => Promise.all([vol.zone(plan.zone, team), vol.trip(zones, team)]).then(([zoneData, tripData]) => {
      if (active) {
        setZone(zoneData);
        setTrip(tripData);
      }
    }, failure => {
      if (active)
        setError(String(failure));
    });
    void load();
    const timer = window.setInterval(load, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [plan, team, extra, posted]);
  const own = team.trim();
  const other = trip?.zones.flatMap(zone => zone.otherTeams).filter(postedPlan => !own || postedPlan.team !== own) ?? [];
  const unique = other.filter((postedPlan, index, plans) => plans.findIndex(candidate => candidate.id === postedPlan.id) === index);
  const overlap = unique.filter(postedPlan => (postedPlan.zones ?? []).some(zone => zone === plan?.zone || zone === extra.trim()));
  async function post() {
    if (!plan || !own || posting || posted !== null)
      return;
    setPosting(true);
    setError('');
    try {
      const response = await v2.plan(t(`${own} ${plan.vehicle === 'boat' ? 'เรือ' : plan.vehicle} ${plan.seats} ที่นั่ง จะเข้าโซน ${plan.zone}${extra.trim() ? ` และ ${extra.trim()}` : ''} ประมาณ ${eta} (อพยพ)`, `${own}: ${plan.vehicle}, ${plan.seats} seats, zone ${plan.zone}${extra.trim() ? ` then ${extra.trim()}` : ""}, around ${eta} (evacuation)`), own);
      if (mounted.current)
        setPosted(response.plan.told ?? 0);
    }
    catch (failure) {
      if (mounted.current)
        setError(String(failure));
    }
    finally {
      if (mounted.current)
        setPosting(false);
    }
  }
  return <div className="rp-app">
    <StepHeader at={overview?.at} onAction={async (action) => {
      await v2.clock(action);
      request.current++;
      setBusy(false);
      setResult(null);
      setZone(null);
      setTrip(null);
      setPosted(null);
      setOverview(await vol.overview());
    }} />
    <nav className="rp-subnav" aria-label={t("หน้าอาสา", "Volunteer pages")}>
      <span className="rp-subnav-label"><Tr th="อาสา" en="Volunteers" /></span>
      <VNavLinks />
    </nav>
    <main className="rp-main">
      <div className="rp-section-head">
        <h1><Tr th="เรือหนึ่งลำ เริ่มที่ไหน" en="One boat. Where first?" /></h1>
        <HonestyLabel />
      </div>
      {error && <p className="rp-warning" role="alert">{error}</p>}
      <div className="rp-plan-layout">
        <CopilotPanel question={question} setQuestion={setQuestion} busy={busy} ask={ask} asked={asked} result={result} />
        {plan ? <>
          <TripMap plan={plan} households={zone?.households ?? []} shelters={overview?.shelters ?? []} geo={geo} atH={overview?.atH ?? 96} />
          <aside className="rp-stack">
            <OrderPanel plan={plan} />
            <OtherTeams plan={plan} extra={extra} setExtra={setExtra} trip={trip} overlap={overlap} unique={unique} />
            {plan.after && <section className="rp-pad">
              <h3>After this trip · {plan.after.zone}</h3>
              <p>{plan.after.urgent} urgent · {plan.after.cannotWalk} can't walk</p>
              <Link to={`/v/zone/${plan.after.zone}`}>Check next uncovered zone →</Link>
            </section>}
            <PlanDraft plan={plan} team={team} setTeam={setTeam} eta={eta} setEta={setEta} post={post} posting={posting} posted={posted} disabled={posting || busy || !own || !trip || (!!extra.trim() && !overview?.zones.some(zone => zone.id === extra.trim())) || plan.runs.some(run => run.people > plan.seats)} />
          </aside>
        </> : <div className="rp-plan-empty">
          <h2>Your trip will appear here.</h2>
          <p>Ask a question, review the tool evidence, then post a plan.</p>
          {result && !plan && <p>This answer did not include a trip plan. Try describing your vehicle and capacity.</p>}
        </div>}
      </div>
    </main>
  </div>;
}

interface CopilotPanelProps {
  question: string;
  setQuestion: (value: string) => void;
  busy: boolean;
  ask: (question: string) => Promise<void>;
  asked: string;
  result: CopilotResult | null;
}

function CopilotPanel({ question, setQuestion, busy, ask, asked, result }: CopilotPanelProps) {
  const plan = result?.plan;
  const isGemini = readerLabel(result?.reader) === "Gemini";
  return <Panel title="Copilot" className="rp-copilot">
    <div className="rp-pad rp-stack">
      <p>Ask Gemini to turn your capacity into a trip with evidence.</p>
      {questions.map(prompt => <button className="rp-chip" key={prompt} disabled={busy} onClick={() => {
        setQuestion(prompt);
        void ask(prompt);
      }}>{prompt}</button>)}
      <form onSubmit={event => {
        event.preventDefault();
        void ask(question);
      }} className="rp-stack">
        <label htmlFor="copilot-question">Your question</label>
        <textarea id="copilot-question" value={question} onChange={event => setQuestion(event.target.value)} rows={3} />
        <button className="rp-primary" disabled={busy || !question.trim()}>Ask copilot →</button>
      </form>
      {asked && <div className="rp-question">{asked}</div>}
      <div role="status" aria-live="polite">
        {busy && <p className="rp-thinking">✦ Gemini is thinking
          <span aria-hidden="true"> ···</span>
        </p>}
      </div>
      {result && <>
        <span className={`rp-reader ${isGemini ? '' : 'rp-warning'}`}>{isGemini ? '✦ Gemini' : 'Rules (Gemini unavailable)'}</span>
        <div className="rp-tools">
          {result.toolCalls.map((toolCall, index) => <div key={index}>
            {displayText(toolCall.name)}(
            {displayText(JSON.stringify(toolCall.args))}) →
            {displayText(toolCall.summary)}
            <small>{toolCall.ms} ms</small>
          </div>)}
        </div>
        {result.checkFailed && <small className="rp-warning">Gemini's answer failed the number check, so this one is written from the tools</small>}
        <CopilotAnswer text={result.answer} />
        {plan && <a className="rp-button" href="#plan-draft">Use this plan →</a>}
        <small className="rp-honesty">Answer from the API · {result.ms} ms · review before posting</small>
      </>}
    </div>
  </Panel>;
}

function OrderPanel({ plan }: {
  plan: CopilotPlan;
}) {
  const t = useT();
  return <Panel title={t("ใครก่อน · Why this order", "Why this order")}>
    {plan.families.map((family, index) => <article className="rp-stop-detail" key={family.id}>
      <div>
        <b className="rp-stop-number">{index + 1}</b>
        <b>{family.people} <Tr th="คน" en="people" /></b>
      </div>
      <Link to={`/v/case/${family.id}`}>{family.id} · evidence →</Link>
      <div className="rp-chips">
        {[family.urgent ? '● Urgent' : '', family.children ? `${family.children} children` : '', family.elderly ? `${family.elderly} elderly` : '', family.cannotWalk ? `${family.cannotWalk} can't walk` : '', `Silent ${family.hoursSilent} h`, family.firstHand ? 'First-hand' : 'Reported by others', `Priority ${family.priority}`].filter(Boolean).map(reason => <span className={`rp-pill ${reason.includes('Urgent') ? 'rp-urgent' : ''}`} key={reason}>{reason}</span>)}
        <DepthRange value={family.depthM} source="at house" />
      </div>
    </article>)}
    <div className="rp-pad">
      <h3><Tr th="เตรียมอะไร" en="What to bring" /></h3>
      <ul>
        {plan.bring.map((item, index) => <li key={index}>{displayText(item)}</li>)}
      </ul>
    </div>
  </Panel>;
}

interface OtherTeamsProps {
  plan: CopilotPlan;
  extra: string;
  setExtra: (value: string) => void;
  trip: Trip | null;
  overlap: Plan[];
  unique: Plan[];
}

function OtherTeams({ plan, extra, setExtra, trip, overlap, unique }: OtherTeamsProps) {
  const t = useT();
  return <Panel title={t("ทีมใกล้เคียง · Other teams near you", "Other teams near you")}>
    <div className="rp-pad rp-stack">
      <label>Add another zone · check overlap
        <input value={extra} onChange={event => setExtra(event.target.value.toUpperCase())} placeholder="Zone ID, e.g. D11" />
      </label>
      {trip ? <p className={overlap.length ? 'rp-warning' : 'rp-success'} role="status">{overlap.length ? `Overlap: ${overlap.length} posted plans. Coordinate before you go.` : 'No overlap in the selected zones'}</p> : <p>Checking posted plans…</p>}
      {plan.otherTeams.map((postedTeam, index) => <div key={index}>
        <b>{displayText(postedTeam.team)}</b>
        <p>{postedTeam.vehicle} · {postedTeam.seats ?? 'unknown'} seats · ETA {postedTeam.eta ?? 'unknown'}</p>
        <p>{postedTeam.offers && displayText(postedTeam.offers)}</p>
      </div>)}
      {unique.map(postedTeam => <div key={postedTeam.id}>
        <b>{displayText(postedTeam.team ?? 'Team')}</b>
        <p>{(postedTeam.zones ?? []).join(' → ')} · {postedTeam.vehicle} · {postedTeam.seats ?? 'unknown'} seats · ETA {postedTeam.eta ?? 'unknown'}</p>
      </div>)}
      <small>Posted plans; ETAs are not fresh confirmations.</small>
    </div>
  </Panel>;
}

interface PlanDraftProps {
  plan: CopilotPlan;
  team: string;
  setTeam: (value: string) => void;
  eta: string;
  setEta: (value: string) => void;
  post: () => Promise<void>;
  posting: boolean;
  posted: number | null;
  disabled: boolean;
}

function PlanDraft({ plan, team, setTeam, eta, setEta, post, posting, posted, disabled }: PlanDraftProps) {
  return <section className="rp-card rp-pad" id="plan-draft">
    <form className="rp-stack" onSubmit={event => {
      event.preventDefault();
      void post();
    }}>
      <h2>Your plan · {plan.zone}</h2>
      <p>{plan.families.length} families · {plan.runs.length} runs</p>
      <label>Team
        <input required value={team} onChange={event => setTeam(event.target.value)} disabled={posting || posted !== null} />
      </label>
      <label>Bringing
        <input readOnly value={`${plan.vehicle} · ${plan.seats} seats · ${plan.bring.map(displayText).join(', ')}`} />
      </label>
      <label>Arriving around
        <input type="time" required value={eta} onChange={event => setEta(event.target.value)} disabled={posting || posted !== null} />
      </label>
      <p>Estimated arrival · evacuation plan</p>
      {posted === null ? <button className="rp-primary" disabled={disabled}>{posting ? 'Posting…' : 'Post plan →'}</button> : <div role="status" className="rp-success">✓ {posted} families told · planned, not rescued yet</div>}
      <Link to="/">Back to overview →</Link>
    </form>
  </section>;
}
