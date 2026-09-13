import { useRef, useState } from 'react'
import BrandMark from './BrandMark'
import ThemeToggle from './ThemeToggle'
import LanguageToggle from './LanguageToggle'
import { t } from '../i18n/strings'

export default function DropZone({ onFile, onLoadDemo, error, isDark, onToggleTheme, lang, onToggleLang }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div className="rest-screen">
      <div style={{ position: 'fixed', top: 20, right: 28, display: 'flex', gap: 10 }}>
        <LanguageToggle lang={lang} onToggle={onToggleLang} />
        <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
      </div>

      <div className="rest-panel">
        <BrandMark size={56} className="rest-logo" />
        <h1 className="rest-title">{t(lang, 'dropProductTitle')}</h1>
        <p className="rest-subtitle">{t(lang, 'dropSubtitle')}</p>

        <div
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <div className="dropzone-icon">⬇</div>
          <div className="dropzone-title">{t(lang, 'dropTitle')}</div>
          <div className="dropzone-hint">{t(lang, 'dropHint')}</div>
          {error && <div className="dropzone-error">{error}</div>}
          <input
            ref={inputRef}
            type="file"
            accept=".db,.json"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) onFile(file)
              e.target.value = ''
            }}
          />
        </div>

        {onLoadDemo && (
          <div className="demo-chip-row">
            <button type="button" className="demo-chip" onClick={onLoadDemo}>
              {t(lang, 'dropDemoBtn')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
