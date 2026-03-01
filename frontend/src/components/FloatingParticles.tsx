'use client';

import { useEffect, useState } from 'react';

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  duration: number;
  delay: number;
  emoji: string;
}

const EMOJIS = ['🍃', '🌱', '✨', '💚', '🌿', '⚡'];

/**
 * Floating leaf/sparkle particles decorating the background.
 * Purely decorative, uses CSS animations.
 */
export function FloatingParticles({ count = 12 }: { count?: number }) {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const items: Particle[] = Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 14 + Math.random() * 12,
      duration: 15 + Math.random() * 20,
      delay: Math.random() * -20,
      emoji: EMOJIS[i % EMOJIS.length],
    }));
    setParticles(items);
  }, [count]);

  if (particles.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden z-0" aria-hidden="true">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute animate-float-particle opacity-20 dark:opacity-10"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            fontSize: `${p.size}px`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        >
          {p.emoji}
        </div>
      ))}
    </div>
  );
}
