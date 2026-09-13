import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'forensic-auditor-lang'

function getSystemPrefersEnglish() {
  return typeof navigator !== 'undefined' && !!navigator.language && !navigator.language.toLowerCase().startsWith('es')
}

export function useLanguage() {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || (getSystemPrefersEnglish() ? 'en' : 'es')
    } catch {
      return 'es'
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('lang', lang)
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      /* almacenamiento no disponible; el idioma sigue funcionando en memoria */
    }
  }, [lang])

  const toggle = useCallback(() => {
    setLang((l) => (l === 'es' ? 'en' : 'es'))
  }, [])

  return { lang, toggle, isEn: lang === 'en' }
}
