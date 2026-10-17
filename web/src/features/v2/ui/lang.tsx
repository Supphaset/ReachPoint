import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

export type UiLang = "th" | "en";
export const UI_LANG_KEY = "rp.v2.lang";
type LanguageContext = { lang: UiLang; setLang: (lang: UiLang) => void };
const UiLangContext = createContext<LanguageContext>({ lang: "th", setLang: () => undefined });

/** Reads each preference lazily, so a blocked storage API cannot hide a URL choice. */
export function resolveUiLang(search: string, saved: () => string | null, language: string): UiLang {
  const query = new URLSearchParams(search).get("lang");
  if (query === "en" || query === "th") return query;
  try {
    const choice = saved();
    if (choice === "en" || choice === "th") return choice;
  } catch { /* Private browsing can deny storage. */ }
  return language.toLowerCase().startsWith("th") ? "th" : "en";
}

export function saveUiLang(choice: UiLang) {
  try { window.localStorage.setItem(UI_LANG_KEY, choice); } catch { /* Keep the choice for this visit. */ }
  const url = new URL(window.location.href);
  url.searchParams.set("lang", choice);
  window.history.replaceState(window.history.state, "", url);
}

export function UiLangProvider({ children, initialLang }: { children: ReactNode; initialLang?: UiLang }) {
  const [lang, updateLang] = useState<UiLang>(() => initialLang ?? resolveUiLang(
    typeof window === "undefined" ? "" : window.location.search,
    () => window.localStorage.getItem(UI_LANG_KEY),
    typeof navigator === "undefined" ? "en" : navigator.language,
  ));
  const setLang = useCallback((choice: UiLang) => {
    updateLang(choice);
    saveUiLang(choice);
  }, []);
  return <UiLangContext.Provider value={{ lang, setLang }}>{children}</UiLangContext.Provider>;
}

export function useUiLang() { return useContext(UiLangContext); }

/** Plain text for attributes, map overlays and generated demo messages. */
export function t(th: string, en: string, lang: UiLang): string { return lang === "en" ? en : th; }
export function useT() {
  const { lang } = useUiLang();
  return useCallback((th: string, en: string) => t(th, en, lang), [lang]);
}

/** Thai keeps its English gloss; English uses only the English content. */
export function Tr({ th, en }: { th: ReactNode; en: ReactNode }) {
  const { lang } = useUiLang();
  return lang === "en" ? <>{en}</> : <>{th}<small className="rp-gloss">{en}</small></>;
}

export function LanguageToggle() {
  const { lang, setLang } = useUiLang();
  return <div className="rp-language" role="group" aria-label="UI language">
    <button type="button" lang="th" aria-pressed={lang === "th"} onClick={() => setLang("th")}>ไทย</button>
    <button type="button" lang="en" aria-pressed={lang === "en"} onClick={() => setLang("en")}>EN</button>
  </div>;
}


/** Select API display names on a copy. Evidence, messages and source quotes stay verbatim. */
export function localizeNames<T>(value: T, lang: UiLang): T {
  if (lang !== "en" || value == null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map(item => localizeNames(item, lang)) as T;
  const out: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) out[key] = localizeNames(item, lang);
  for (const key of ["name", "label", "sectorName", "district", "address"]) {
    if (typeof out[key + "En"] === "string" && out[key + "En"]) out[key] = out[key + "En"];
  }
  return out as T;
}
