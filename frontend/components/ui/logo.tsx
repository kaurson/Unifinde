import React from 'react'
import { GraduationCap } from 'lucide-react'
import Link from 'next/link'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
  href?: string
}

export function Logo({ size = 'md', showText = true, className = '', href = '/' }: LogoProps) {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10'
  }

  const textSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl'
  }

  const LogoContent = () => (
    <div className={`flex items-center space-x-2 ${className}`}>
      <GraduationCap className={`${sizeClasses[size]} text-primary`} />
      {showText && (
        <span className={`font-bold gradient-text ${textSizes[size]}`}>
          UniFinder
        </span>
      )}
    </div>
  )

  if (href) {
    return (
      <Link href={href} className="hover:opacity-80 transition-opacity">
        <LogoContent />
      </Link>
    )
  }

  return <LogoContent />
} 