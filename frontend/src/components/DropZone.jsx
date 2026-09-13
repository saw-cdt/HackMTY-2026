import { useRef, useState } from 'react'
import BrandMark from './BrandMark'
import ThemeToggle from './ThemeToggle'

export default function DropZone({ onFile, onLoadDemo, error, isDark, onToggleTheme }) {
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
      <div style={{ position: 'fixed', top: 20, right: 28 }}>
        <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
      </div>

      <div className="rest-panel">
        <BrandMark size={56} className="rest-logo" />
        <h1 className="rest-title">The Forensic Auditor</h1>
        <p className="rest-subtitle">
          Suelta el estate de una empresa (.db) y el agente reconstruye, sin ayuda humana,
          quién se llevó el dinero y por qué el resto no calificó.
        </p>

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
          <div className="dropzone-title">Suelta el archivo .db aquí</div>
          <div className="dropzone-hint">o haz clic para elegirlo — funciona sin conexión</div>
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
              Cargar demo — estate_seed004.db
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
