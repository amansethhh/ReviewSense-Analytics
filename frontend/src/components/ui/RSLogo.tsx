/**
 * RSLogo — Animated Cyber-Orb logo faithfully modelled on the ReviewSense brand image.
 *
 * Structure (all rings share the same centre at cx=24, cy=24 of a 48×48 viewBox):
 *  Ring 1 (outermost) – thick segmented arcs,  r=21.5, rotates CW  4 s
 *  Ring 2             – medium segments,        r=18,   CCW         3 s
 *  Ring 3             – tighter segments,       r=14.5, CW          2.4 s
 *  Ring 4             – fine dashes,            r=11,   CCW         2 s
 *  Inner glow ring    – thin dashes,            r=7.8,  CW+pulse    1.6 s
 *  Halo               – diffuse fill,           r=9     breathes softly
 *  Core orb           – radial gradient,        r=5.5   breathes softly
 *
 * Fix applied: every animated element now has an explicit transformOrigin set so
 * the rotation pivot stays locked to the SVG centre (24, 24). The core/halo pulse
 * scale is reduced (1.0 → 1.08) so the halo never overlaps Ring 4.
 */

export function RSLogo({ size = 36 }: { size?: number }) {
  const cx = 24           // centre x of the 48×48 viewBox
  const cy = 24           // centre y
  const id = 'rsl'        // short unique prefix for gradient/filter IDs

  /** Shared pivot anchor used on every rotating element. */
  const pivot = `${cx}px ${cy}px`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="ReviewSense logo"
      style={{ flexShrink: 0, overflow: 'visible', display: 'block' }}
    >
      <defs>
        {/* Core orb gradient: white hot-centre → cyan → transparent */}
        <radialGradient id={`${id}-core`} cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor="#ffffff" stopOpacity="1"   />
          <stop offset="28%"  stopColor="#aaf4ff" stopOpacity="0.95"/>
          <stop offset="55%"  stopColor="#00D9FF" stopOpacity="0.8" />
          <stop offset="80%"  stopColor="#0088cc" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#003355" stopOpacity="0"   />
        </radialGradient>

        {/* Outer halo — soft glow behind core */}
        <radialGradient id={`${id}-halo`} cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor="#00D9FF" stopOpacity="0.22"/>
          <stop offset="60%"  stopColor="#00D9FF" stopOpacity="0.05"/>
          <stop offset="100%" stopColor="#00D9FF" stopOpacity="0"   />
        </radialGradient>

        {/* Subtle ring glow */}
        <filter id={`${id}-glow`} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="0.4" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>

        {/* Core glow */}
        <filter id={`${id}-core-glow`} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="1.2" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      {/* ── RING 1 — outermost, r=21.5, CW 4 s ── */}
      <circle
        cx={cx} cy={cy} r="21.5"
        stroke="#00D9FF" strokeWidth="3.2" strokeLinecap="round"
        strokeDasharray="17 5.6"
        fill="none"
        filter={`url(#${id}-glow)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-spin-cw 4s linear infinite',
          opacity: 0.65,
        }}
      />

      {/* ── RING 2 — r=18, CCW 3 s ── */}
      <circle
        cx={cx} cy={cy} r="18"
        stroke="#00c8f0" strokeWidth="2.2" strokeLinecap="round"
        strokeDasharray="12 4.5 5 4.5"
        fill="none"
        filter={`url(#${id}-glow)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-spin-ccw 3s linear infinite',
          opacity: 0.55,
        }}
      />

      {/* ── RING 3 — r=14.5, CW 2.4 s ── */}
      <circle
        cx={cx} cy={cy} r="14.5"
        stroke="#00efff" strokeWidth="1.8" strokeLinecap="round"
        strokeDasharray="10 3.8"
        fill="none"
        filter={`url(#${id}-glow)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-spin-cw 2.4s linear infinite',
          opacity: 0.45,
        }}
      />

      {/* ── RING 4 — r=11, CCW 2 s ── */}
      <circle
        cx={cx} cy={cy} r="11"
        stroke="#60EFFF" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="7 3"
        fill="none"
        filter={`url(#${id}-glow)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-spin-ccw 2s linear infinite',
          opacity: 0.38,
        }}
      />

      {/* ── INNER GLOW RING — r=7.8, CW 1.6 s + opacity pulse ──
           r=7.8 keeps it well inside Ring 4 (r=11).
           Only rotates + pulses opacity — no scale — so it never strays from its orbit. */}
      <circle
        cx={cx} cy={cy} r="7.8"
        stroke="#00D9FF" strokeWidth="0.8"
        strokeDasharray="3 2"
        fill="none"
        style={{
          transformOrigin: pivot,
          animation: 'rs-spin-cw 1.6s linear infinite, rs-ring-pulse 2.4s ease-in-out infinite',
        }}
      />

      {/* ── HALO — r=8.2 diffuse fill, breathes very gently (no position change) ──
           Max scale 1.06 keeps it safely inside Ring 4 (r=11). */}
      <circle
        cx={cx} cy={cy} r="8.2"
        fill={`url(#${id}-halo)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-halo-pulse 2s ease-in-out infinite',
        }}
      />

      {/* ── CORE ORB — r=5.5, breathes gently ──
           Max scale 1.06 keeps core inside halo orbit. */}
      <circle
        cx={cx} cy={cy} r="5.5"
        fill={`url(#${id}-core)`}
        filter={`url(#${id}-core-glow)`}
        style={{
          transformOrigin: pivot,
          animation: 'rs-core-pulse 2s ease-in-out infinite',
        }}
      />
    </svg>
  )
}
