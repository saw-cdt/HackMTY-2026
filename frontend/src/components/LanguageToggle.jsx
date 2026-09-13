import { t } from '../i18n/strings'

export default function LanguageToggle({ lang, onToggle }) {
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={t(lang, 'langToggleAriaLabel')}
      title={t(lang, 'langToggleTitle')}
    >
      <span className="icon">ES</span>
      <span className={`switch-track ${lang === 'en' ? 'on' : ''}`}>
        <span className="switch-thumb" />
      </span>
      <span className="icon">EN</span>
    </button>
  )
}
