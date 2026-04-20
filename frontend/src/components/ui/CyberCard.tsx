import { useRef, useCallback, memo, type ReactNode, type CSSProperties } from 'react'
import './CyberCard.css'

interface CyberCardProps {
  children: ReactNode
  style?: CSSProperties
}

/**
 * Cyber-themed 3D tilt card with scan line, corner brackets,
 * glowing elements, and cyber-line animations.
 *
 * PERF: Mouse handler throttled to 60fps (16ms) to prevent
 * layout thrashing during rapid mouse movement.
 */
export const CyberCard = memo(function CyberCard({ children, style }: CyberCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const rafRef = useRef<number>(0)

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    // Throttle to animation frame (60fps) — prevents layout thrashing
    if (rafRef.current) return
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = 0
      const el = cardRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const midX = rect.width / 2
      const midY = rect.height / 2
      const rotateY = ((x - midX) / midX) * 10
      const rotateX = ((midY - y) / midY) * 10
      el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
    })
  }, [])

  const handleMouseLeave = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = 0
    }
    const el = cardRef.current
    if (!el) return
    el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)'
  }, [])

  return (
    <div
      className="cyber-card"
      ref={cardRef}
      style={style}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Corner brackets */}
      <span className="cyber-card__corner cyber-card__corner--tl" />
      <span className="cyber-card__corner cyber-card__corner--tr" />
      <span className="cyber-card__corner cyber-card__corner--bl" />
      <span className="cyber-card__corner cyber-card__corner--br" />

      {/* Scan line */}
      <div className="cyber-card__scan-line" />

      {/* Cyber horizontal lines */}
      <div className="cyber-card__lines">
        <span /><span /><span /><span />
      </div>

      {/* Glare overlay */}
      <div className="cyber-card__glare" />

      {/* Glow elements */}
      <div className="cyber-card__glow cyber-card__glow--1" />
      <div className="cyber-card__glow cyber-card__glow--2" />

      {/* Content */}
      <div className="cyber-card__content">
        {children}
      </div>
    </div>
  )
})
