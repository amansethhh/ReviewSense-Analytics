import { useId } from 'react'

interface HoloToggleProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}

export function HoloToggle({ label, checked, onChange }: HoloToggleProps) {
  const id = useId()

  return (
    <div className="holo-toggle">
      <input
        className="holo-toggle__input"
        id={id}
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
      />
      <label className="holo-toggle__track" htmlFor={id}>
        <div className="holo-toggle__track-line" />
        <div className="holo-toggle__thumb">
          <div className="holo-toggle__thumb-core" />
          <div className="holo-toggle__thumb-inner" />
          <div className="holo-toggle__scan" />
        </div>
        <div className="holo-toggle__rings">
          <div className="holo-toggle__ring" />
          <div className="holo-toggle__ring" />
        </div>
        <div className="holo-toggle__glow" />
      </label>
      <span className="holo-toggle__label">{label}</span>
    </div>
  )
}
