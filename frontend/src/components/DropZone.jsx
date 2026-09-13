import { useCallback, useRef, useState } from 'react'

export default function DropZone({ onSubmission, onEstate, loading }) {
  const input = useRef(null)
  const [over, setOver] = useState(false)

  const handleFiles = useCallback(
    (files) => {
      for (const f of files) {
        if (/\.json$/i.test(f.name)) onSubmission(f)
        else if (/\.db$/i.test(f.name) || /\.sqlite$/i.test(f.name)) onEstate(f)
      }
    },
    [onSubmission, onEstate],
  )

  return (
    <div
      className={`dropzone${over ? ' dragover' : ''}`}
      onClick={() => input.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        if (e.dataTransfer.files) handleFiles(e.dataTransfer.files)
      }}
    >
      <input
        ref={input}
        type="file"
        multiple
        accept=".json,.db,.sqlite"
        style={{ display: 'none' }}
        onChange={(e) => handleFiles(e.target.files)}
      />
      <p className="big">
        Suelten su <span className="primary">estate</span>
      </p>
      <p className="hint">
        estate_seedNNN.db — el expediente completo &nbsp;·&nbsp; submission_seedNNN.json — el informe
        del agente
      </p>
      {loading ? (
        <span className="chip"><span className="spin" /> leyendo el archivo…</span>
      ) : (
        <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); input.current?.click() }}>
          Elegir archivo
        </button>
      )}
    </div>
  )
}