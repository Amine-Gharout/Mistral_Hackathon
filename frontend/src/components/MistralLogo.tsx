'use client';

/**
 * Mistral AI logo — the official "M" mark reproduced from the brand SVG.
 */
export function MistralLogo({ className = 'w-8 h-8' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 191 135"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Mistral AI"
    >
      <g clipPath="url(#clip0_mistral)">
        <path d="M54.3221 0H27.1531V27.0892H54.3221V0Z" fill="#A8E6A1" />
        <path d="M162.984 0H135.815V27.0892H162.984V0Z" fill="#A8E6A1" />
        <path d="M81.4823 27.0913H27.1531V54.1805H81.4823V27.0913Z" fill="#6BCB77" />
        <path d="M162.99 27.0913H108.661V54.1805H162.99V27.0913Z" fill="#6BCB77" />
        <path d="M162.972 54.168H27.1531V81.2572H162.972V54.168Z" fill="#38A169" />
        <path d="M54.3221 81.2593H27.1531V108.349H54.3221V81.2593Z" fill="#276749" />
        <path d="M108.661 81.2593H81.4917V108.349H108.661V81.2593Z" fill="#276749" />
        <path d="M162.984 81.2593H135.815V108.349H162.984V81.2593Z" fill="#276749" />
        <path d="M81.4879 108.339H-0.00146484V135.429H81.4879V108.339Z" fill="#1A4731" />
        <path d="M190.159 108.339H108.661V135.429H190.159V108.339Z" fill="#1A4731" />
      </g>
      <defs>
        <clipPath id="clip0_mistral">
          <rect width="190.141" height="135" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
}

/**
 * Animated version with a subtle shimmer effect.
 */
export function MistralLogoAnimated({ className = 'w-10 h-10' }: { className?: string }) {
  return (
    <div className={`relative ${className}`}>
      <div className="absolute inset-0 animate-mistral-glow rounded-lg opacity-50 blur-md bg-gradient-to-r from-green-400 via-emerald-300 to-green-400" />
      <MistralLogo className="relative w-full h-full drop-shadow-lg" />
    </div>
  );
}
