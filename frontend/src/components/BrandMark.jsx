export default function BrandMark({ size = 26, className = '' }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="12" cy="12" r="7.5" fill="#ff5a8a" />
      <circle cx="20" cy="12" r="7.5" fill="#7c5cfc" />
      <circle cx="12" cy="20" r="7.5" fill="#f5a623" />
      <circle cx="20" cy="20" r="7.5" fill="#3d8bff" />
    </svg>
  )
}
