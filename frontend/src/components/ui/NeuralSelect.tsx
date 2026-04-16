import { SelectHTMLAttributes } from 'react';

interface NeuralSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: { label: string; value: string | number }[];
}

export function NeuralSelect({ options, className = '', ...props }: NeuralSelectProps) {
  return (
    <div className={`neural-select-wrap ${className}`}>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        className="neural-select__arrow"
      >
        <path
          strokeWidth={4}
          strokeLinejoin="round"
          strokeLinecap="round"
          fill="none"
          d="M60.7,53.6,50,64.3m0,0L39.3,53.6M50,64.3V35.7m0,46.4A32.1,32.1,0,1,1,82.1,50,32.1,32.1,0,0,1,50,82.1Z"
        />
      </svg>
      <select className="neural-select" {...props}>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
