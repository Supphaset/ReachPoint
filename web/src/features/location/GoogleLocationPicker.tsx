import { useEffect, useRef, useState } from "react";
import type { Location } from "../../data/contract";
import { loadGoogleMaps, type Maps } from "../../data/googleMaps";
import { locate } from "../../data/intake";
import { demoBounds } from "../../data/locationMap";
import { useLang } from "../../i18n/lang";
import { S, seedText } from "../../i18n/strings";
import { Icon } from "../../ui/Icon";
import { callerPlace } from "./LocationChip";
import { LocationMap } from "./LocationMap";
import "./location.css";

type At = [number, number];
const HAT_YAI = { lat: 7.0086, lng: 100.4747 };

/**
 * Pick your spot on a Google Map, the way ride and delivery apps do: a pin fixed in the centre, you move the map
 * under it (a tap moves the map there too), and "Use this spot" is always ready. No zones to choose; the server
 * snaps the point to segment and landmark. `fill` makes it fill its container (the chat's location sheet). Without
 * a Maps key, or if the map can't load, the drawn map is shown instead.
 */
export function GoogleLocationPicker({ start, onConfirm, fill = false }: { start?: At | null; onConfirm: (at: At) => void; fill?: boolean }) {
  const { t, lang } = useLang();
  const box = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<"loading" | "ready" | "fallback">("loading");
  const [pin, setPin] = useState<At>(start ?? [HAT_YAI.lng, HAT_YAI.lat]);
  // What is under the pin, from the server's read-only snap (no AI): "Near Kim Yong market", or outside the area.
  const [under, setUnder] = useState<Location | null>(null);
  const asked = useRef(0);
  useEffect(() => {
    if (state !== "ready") return;
    const n = ++asked.current;
    const timer = window.setTimeout(() => {
      void locate({ kind: "pin", lon: pin[0], lat: pin[1], method: "map" }).then((r) => {
        if (n === asked.current) setUnder(r.ok ? r.value : null);
      });
    }, 400);
    return () => window.clearTimeout(timer);
  }, [pin, state]);
  const outside = under?.status === "outside_area";
  useEffect(() => {
    let alive = true;
    Promise.all([loadGoogleMaps(lang), demoBounds()])
      .then(([maps, [west, south, east, north]]) => {
        if (!alive || !box.current) return;
        const map = new maps.Map(box.current, {
          center: start ? { lat: start[1], lng: start[0] } : HAT_YAI, zoom: start ? 17 : 16, clickableIcons: false,
          // "cooperative" in the inline form, so one finger still scrolls the page; the sheet scrolls nothing else.
          gestureHandling: fill ? "greedy" : "cooperative",
          streetViewControl: false, mapTypeControl: false, fullscreenControl: false,
          restriction: { latLngBounds: { west, south, east, north }, strictBounds: false },
        });
        const sync = () => { const c = map.getCenter(); if (c) setPin([c.lng(), c.lat()]); };
        map.addListener("idle", sync);
        map.addListener("click", (e: Maps) => map.panTo(e.latLng));
        setState("ready");
      })
      .catch(() => alive && setState("fallback"));
    return () => { alive = false; };
    // The map is built once per open; language changes reopen the picker.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  if (state === "fallback") return <LocationMap at={start ?? null} onConfirm={onConfirm} />;
  return (
    <div className={`location-map is-picker is-google ${fill ? "is-fill" : ""}`}>
      <div className="location-gmap-frame">
        {/* Google Maps owns this div's children; React must never render inside it. */}
        <div ref={box} className="location-gmap" role="application" aria-label={t(S.location.mapLabel)} aria-describedby="gmap-help" />
        <span className="location-gmap-pin" aria-hidden="true"><Icon name="pin" size={40} /></span>
        <p className="location-gmap-help" id="gmap-help">{t(S.location.googleHelp)}</p>
        {state === "loading" && <p role="status" className="location-gmap-loading">{t(S.briefing.mapLoading)}</p>}
      </div>
      <div className="location-gmap-foot">
        <p className="location-gmap-where" aria-live="polite">
          {under && <><Icon name="pin" size={16} />{outside ? t(S.location.outside_area)
            : under.landmarkLabel ? t(S.location.near(callerPlace(seedText(under.landmarkLabel, lang)))) : ""}</>}
        </p>
        <button type="button" className="btn btn-primary btn-lg" disabled={state !== "ready" || outside} onClick={() => onConfirm(pin)}>
          <Icon name="check" />{t(S.location.useSpot)}
        </button>
      </div>
    </div>
  );
}
