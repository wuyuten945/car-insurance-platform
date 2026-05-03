'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { dictionaries, type Lang } from './translations';

interface Ctx {
  lang: Lang;
  setLang: (l: Lang) => void;
  toggleLang: () => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<Ctx | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>('zh');

  useEffect(() => {
    try {
      const saved = localStorage.getItem('app.lang');
      if (saved === 'zh' || saved === 'en') setLangState(saved);
    } catch {
      /* ignore */
    }
  }, []);

  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem('app.lang', l);
    } catch {
      /* ignore */
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = l === 'zh' ? 'zh-TW' : 'en';
    }
  };

  const toggleLang = () => setLang(lang === 'zh' ? 'en' : 'zh');

  const t = (key: string, vars?: Record<string, string | number>): string => {
    const dict = dictionaries[lang] || dictionaries.zh;
    let str = dict[key] ?? dictionaries.zh[key] ?? key;
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
      });
    }
    return str;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useT() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    // Fallback for components rendered outside provider (shouldn't happen)
    return {
      lang: 'zh' as Lang,
      setLang: () => {},
      toggleLang: () => {},
      t: (k: string) => k,
    };
  }
  return ctx;
}
