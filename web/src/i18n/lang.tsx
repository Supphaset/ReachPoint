import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

/**
 * Thai / English switch. Thai is the default. The choice is kept per browser (localStorage) and can be forced
 * with `?lang=th` or `?lang=en` (the /demo page uses this so each phone keeps its own language).
 * Words people typed (caller quotes, flag reasons, medical notes) are never translated.
 */
export type Lang = "th" | "en";

/** One entry of the word list: the same meaning in both languages. */
export interface Pair {
  en: string;
  th: string;
}

const KEY = "reachpoint.lang";

function initial(): Lang {
  if (typeof window === "undefined") return "th";
  try {
    const q = new URLSearchParams(window.location.search).get("lang");
    if (q === "th" || q === "en") return q;
    const saved = localStorage.getItem(KEY);
    if (saved === "th" || saved === "en") return saved;
  } catch {
    /* storage blocked: use the default */
  }
  return "th";
}

// Outside a provider (unit tests, static renders) screens read English.
const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: "en", setLang: () => {} });

export function LangProvider({ children, lang: fixed }: { children: ReactNode; lang?: Lang }) {
  const [lang, set] = useState<Lang>(fixed ?? initial);
  const setLang = (l: Lang) => {
    set(l);
    try {
      localStorage.setItem(KEY, l);
    } catch {
      /* private mode: keep it for this page only */
    }
  };
  useEffect(() => {
    document.documentElement.lang = lang; // screen readers and Thai line breaking follow the chosen language
  }, [lang]);
  return <Ctx.Provider value={{ lang, setLang }}>{children}</Ctx.Provider>;
}

/** `const { t, lang } = useLang(); t(S.call.send)` */
export function useLang() {
  const { lang, setLang } = useContext(Ctx);
  const t = (p: Pair) => p[lang];
  /** A server field with an optional Thai twin: shows Thai when we have it, the original otherwise. */
  const pick = (en: string, th?: string | null) => (lang === "th" && th ? th : en);
  return { lang, setLang, t, pick };
}

export function LangSwitch() {
  const { lang, setLang } = useLang();
  return (
    <div className="lang-switch" role="group" aria-label="Language / ภาษา">
      <button type="button" aria-pressed={lang === "th"} onClick={() => setLang("th")} lang="th">
        ไทย
      </button>
      <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")} lang="en">
        EN
      </button>
    </div>
  );
}
