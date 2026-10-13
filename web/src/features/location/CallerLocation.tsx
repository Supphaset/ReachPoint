import { useEffect, useRef, useState } from "react";
import type { Location, LocationInput } from "../../data/contract";
import { locate } from "../../data/intake";
import { deviceLocation } from "../../data/deviceLocation";
import { apiMode } from "../../data/mode";
import { useLang, type Pair } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Icon } from "../../ui/Icon";
import { LocationChip } from "./LocationChip";
import { GoogleLocationPicker } from "./GoogleLocationPicker";

type At = [number, number];
const PRECISE_M = 50; // a GPS fix better than this is used as is; a rougher one opens the map on it to fine-tune

/**
 * "Where are you?" for the person asking for help. Inline in the one-message form, or as a sheet in the chat
 * (`variant="sheet"`): a header with back and close, one step at a time, and the primary action always on screen.
 * Step 1 chooser: GPS (primary), pick on the map, or a place name. Step 2 map: replaces the chooser and fills the
 * sheet, with a fixed centre pin you move the map under. Nothing is sent until a step succeeds (D25).
 */
export function CallerLocation({ onChange, onBusy, variant = "inline", onClose }: {
  onChange: (input?: LocationInput) => void; onBusy: (busy: boolean) => void; variant?: "inline" | "sheet"; onClose?: () => void;
}) {
  const { t } = useLang();
  const sheet = variant === "sheet";
  const [address, setAddress] = useState("");
  const [resolved, setResolved] = useState<Location>();
  const [map, setMap] = useState(false);
  const [start, setStart] = useState<At | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Pair>();
  const generation = useRef(0);
  const addressBox = useRef<HTMLInputElement>(null);
  useEffect(() => () => { generation.current++; }, []);
  const working = (value: boolean) => { setBusy(value); onBusy(value); };
  const clear = () => { generation.current++; working(false); setResolved(undefined); setMessage(undefined); onChange(undefined); };
  const openMap = (at: At | null = null, why?: Pair) => { setStart(at); setMap(true); setMessage(why); };
  const preview = async (input: LocationInput, request = ++generation.current) => {
    working(true);
    setMessage(undefined);
    const result = await locate(input);
    if (request !== generation.current) return;
    working(false);
    if (!result.ok) { setMessage(apiMode() ? S.location.failed : S.common.needsServer); return; }
    // Keep even an unresolved address: the desk can still locate it by hand (D25).
    setResolved(result.value);
    onChange(input);
    setMap(false);
    if (result.value.status === "unlocated") setMessage(S.location.notFound);
    if (result.value.status === "outside_area") { setResolved(undefined); openMap(null, S.location.outside); }
    if (result.value.status === "located" && navigator.vibrate) navigator.vibrate(30);
  };
  const gps = async () => {
    const request = ++generation.current;
    working(true);
    setMessage(undefined);
    // In fixtures, never request device permission or send a coordinate.
    if (!apiMode()) { working(false); setMessage(S.common.needsServer); return; }
    const result = await deviceLocation();
    if (request !== generation.current) return;
    if (!result.ok) { working(false); openMap(null, S.location[result.reason]); return; }
    const fix = result.input;
    if (fix.kind === "pin" && fix.accuracyM != null && fix.accuracyM > PRECISE_M) {
      working(false);
      openMap([fix.lon, fix.lat], S.location.notPrecise);
      return;
    }
    await preview(result.input, request);
  };
  const find = () => {
    if (!address.trim()) { addressBox.current?.focus(); setMessage(S.location.addressHint); return; }
    void preview({ kind: "address", text: address.trim() });
  };

  const chooser = <>
    {!sheet && <h2 id="caller-location-title">{t(S.location.where)}</h2>}
    <p className="fine-print">{t(S.location.purpose)}</p>
    <div className="location-choices">
      <button type="button" className="btn btn-primary btn-lg" disabled={busy} onClick={() => void gps()}><Icon name="pin" />{busy ? t(S.location.finding) : t(S.location.gps)}</button>
      <button type="button" className="btn btn-secondary btn-lg" disabled={busy} onClick={() => openMap()}><Icon name="map" />{t(S.location.map)}</button>
    </div>
    <p className="location-or" aria-hidden="true">{t(S.location.or)}</p>
    <label htmlFor="caller-address">{t(S.location.address)}</label>
    <div className="location-address">
      <input id="caller-address" ref={addressBox} value={address} disabled={busy} enterKeyHint="search" placeholder={t(S.location.addressExample)}
        onChange={e => setAddress(e.target.value)} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); if (!busy) find(); } }} />
      <button type="button" className="btn btn-secondary" disabled={busy} onClick={find}>{t(S.location.find)}</button>
    </div>
  </>;

  const status = <div role="status" aria-live="polite" className={message ? "location-message" : undefined}>{busy ? t(S.location.finding) : message && t(message)}</div>;
  const privacy = <p className="fine-print location-privacy"><Icon name="lock" size={16} /> {t(S.location.privacy)}</p>;
  const picker = <GoogleLocationPicker key={start ? start.join() : "city"} start={start} fill={sheet}
    onConfirm={at => void preview({ kind: "pin", lon: at[0], lat: at[1], method: "map" })} />;

  if (sheet) return <section className="location-block is-sheet" aria-labelledby="caller-location-title">
    <header className="sheet-head">
      {map
        ? <button type="button" className="icon-btn" onClick={() => { generation.current++; working(false); setMap(false); setMessage(undefined); }} aria-label={t(S.location.back)}><Icon name="back" /></button>
        : <span aria-hidden="true" />}
      <h2 id="caller-location-title">{t(map ? S.location.mapTitle : S.location.where)}</h2>
      <button type="button" className="icon-btn" onClick={onClose} aria-label={t(S.location.close)}><Icon name="close" /></button>
    </header>
    {map
      ? <div className="sheet-body is-map">{message && <p className="location-map-note" role="status">{t(message)}</p>}{!busy && picker}{busy && status}</div>
      : <div className="sheet-body">
        {resolved
          ? <div className="location-actions"><LocationChip location={resolved} /><button type="button" className="btn btn-secondary" onClick={clear}>{t(S.location.change)}</button></div>
          : chooser}
        {status}
        {resolved && resolved.status !== "located" && <button type="button" className="btn btn-secondary btn-lg" disabled={busy} onClick={() => openMap()}>{t(S.location.map)}</button>}
        {privacy}
      </div>}
    {!map && <footer className="sheet-foot">
      <button type="button" className="btn btn-quiet btn-md" onClick={onClose}>{t(S.location.skip)}</button>
    </footer>}
  </section>;

  return <section className="location-block" aria-labelledby="caller-location-title">
    {resolved
      ? <><h2 id="caller-location-title">{t(S.location.where)}</h2>
        <div className="location-actions"><LocationChip location={resolved} /><button type="button" className="btn btn-secondary" onClick={clear}>{t(S.location.change)}</button></div></>
      : !map && chooser}
    {status}
    {resolved && resolved.status !== "located" && !map && <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => openMap()}>{t(S.location.map)}</button>}
    {map && <h2 id="caller-location-title">{t(S.location.mapTitle)}</h2>}
    {map && !busy && picker}
    {(map || busy) && <button type="button" className="btn btn-secondary" onClick={() => { generation.current++; working(false); setMap(false); }}>{t(S.location.cancel)}</button>}
    {privacy}
  </section>;
}
