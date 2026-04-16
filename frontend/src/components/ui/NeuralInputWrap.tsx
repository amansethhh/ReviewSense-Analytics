import type { ReactNode } from 'react'

interface NeuralInputWrapProps {
  children: ReactNode
}

/**
 * Neumorphic container for text inputs, textareas, and selects.
 * Creates a 3D embossed container with teal glow on hover/focus.
 * All styling is in components.css (.neural-input-wrap).
 */
export function NeuralInputWrap({ children }: NeuralInputWrapProps) {
  return (
    <div className="neural-input-wrap">
      {children}
    </div>
  )
}
