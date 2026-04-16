interface LiquidLoaderProps {
  text?: string
}

export function LiquidLoader({ text = 'Loading' }: LiquidLoaderProps) {
  return (
    <div className="liquid-loader">
      <div className="liquid-loader__text">
        {text}
        <span className="liquid-loader__dot">.</span>
        <span className="liquid-loader__dot">.</span>
        <span className="liquid-loader__dot">.</span>
      </div>
      <div className="liquid-loader__track">
        <div className="liquid-loader__fill" />
      </div>
    </div>
  )
}
