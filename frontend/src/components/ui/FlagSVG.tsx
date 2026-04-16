import type { CSSProperties } from 'react'

/* ─────────────────────────────────────────────────────────────────
   Animated country flags served as WebP from the open-source CDN:
   https://github.com/Malith-Rukshan/animated-country-flags
   URL pattern: https://animated-country-flags.malith.dev/webp/{CODE}.webp

   Language code → ISO 3166-1 alpha-2 country code mapping
   (our internal codes mostly match ISO, with a few exceptions)
   ───────────────────────────────────────────────────────────────── */

const LANG_TO_COUNTRY: Record<string, string> = {
  EN: 'GB',   // English  → United Kingdom
  HI: 'IN',   // Hindi    → India
  ES: 'ES',   // Spanish  → Spain
  FR: 'FR',   // French   → France
  DE: 'DE',   // German   → Germany
  ZH: 'CN',   // Chinese  → China
  PT: 'PT',   // Portuguese → Portugal
  RU: 'RU',   // Russian  → Russia
  JA: 'JP',   // Japanese → Japan
  KO: 'KR',   // Korean   → South Korea
  IT: 'IT',   // Italian  → Italy
  AR: 'SA',   // Arabic   → Saudi Arabia
  NL: 'NL',   // Dutch    → Netherlands
  TR: 'TR',   // Turkish  → Turkey
  SV: 'SE',   // Swedish  → Sweden
  TH: 'TH',   // Thai     → Thailand
}

const CDN = 'https://animated-country-flags.malith.dev/webp'

/* Wrapper style: rounded corners + cinematic 3-D tilt + deep shadow */
const imgStyle: CSSProperties = {
  display: 'block',
  borderRadius: '7px',
  boxShadow:
    '0 10px 28px rgba(0,0,0,0.7), 0 3px 10px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.12)',
  transform: 'perspective(600px) rotateY(-7deg) rotateX(3deg)',
  imageRendering: 'auto',
  objectFit: 'cover',
}

interface FlagSVGProps {
  /** Internal language code (EN, HI, ZH …) */
  code: string
  /** Width in px — height is auto at 2:3 ratio */
  size?: number
}

export function FlagSVG({ code, size = 56 }: FlagSVGProps) {
  const country = LANG_TO_COUNTRY[code.toUpperCase()]
  if (!country) return null

  const height = Math.round((size * 2) / 3)
  const src    = `${CDN}/${country}.webp`

  return (
    <img
      src={src}
      alt={`${country} flag`}
      width={size}
      height={height}
      loading="lazy"
      decoding="async"
      style={imgStyle}
      /* Fallback: show nothing if CDN is unreachable */
      onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }}
    />
  )
}
