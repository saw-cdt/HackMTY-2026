export default function ThemeToggle({ isDark, onToggle }) {
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label="Cambiar tema"
      title="Cambiar tema claro / oscuro"
    >
      <span className="icon">☀️</span>
      <span className={`switch-track ${isDark ? 'on' : ''}`}>
        <span className="switch-thumb" />
      </span>
      <span className="icon">🌙</span>
    </button>
  )
}
