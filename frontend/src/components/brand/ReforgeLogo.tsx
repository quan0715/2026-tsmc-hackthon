interface ReforgeLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizes = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
}

export function ReforgeLogo({ size = 'md', className = '' }: ReforgeLogoProps) {
  return (
    <img
      src="/reforge-logo.svg"
      alt="Reforge"
      className={`${sizes[size]} ${className}`}
    />
  )
}
