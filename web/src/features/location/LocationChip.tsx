import type { Location } from "../../data/contract";
import type { Pair } from "../../i18n/lang";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Icon } from "../../ui/Icon";
import "./location.css";

/** Package landmark labels are codes plus generic names; preserve codes and caller-authored names. */
export function landmarkText(label: string, t: (p: Pair) => string): string {
  let result = label;
  for (const [en, pair] of Object.entries(S.location.landmarks)) result = result.replace(en, t(pair));
  return result;
}
export function locationSource(location: Location, viewer: "caller" | "desk" = "caller"): Pair {
  if (location.kind === "pin") return viewer === "desk"
    ? S.location.sources[location.method === "gps" ? "callerGps" : "callerMap"]
    : S.location.sources[location.method === "gps" ? "gps" : "map"];
  if (location.status === "unlocated") return S.location.sources.notFound;
  return location.provider === "pinpoint" ? S.location.sources.pinpoint : location.provider === "stand-in" ? S.location.sources.standIn : S.location.sources.other;
}
export function locationText(location: Location, t: (p: Pair) => string, viewer: "caller" | "desk" = "caller"): string {
  if (location.status !== "located") return t(S.location[location.status]);
  const label = location.landmarkLabel || location.landmarkId || location.segmentId || location.zoneId;
  return [label ? t(S.location.near(landmarkText(label, t))) : t(S.location.located), t(locationSource(location, viewer)),
    location.accuracyM != null ? t(S.location.accuracy(location.accuracyM)) : ""].filter(Boolean).join(" · ");
}
export function LocationChip({ location, viewer = "caller" }: { location?: Location; viewer?: "caller" | "desk" }) {
  const { t } = useLang();
  return <span className={`location-chip ${location?.status === "located" ? "is-located" : "is-unknown"}`}>
    <Icon name={location?.status === "located" ? "pin" : "question"} />
    <span>{location ? locationText(location, t, viewer) : t(S.location.notGiven)}</span>
  </span>;
}
