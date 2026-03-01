'use client';

import { useTheme } from 'next-themes';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div className="w-9 h-9" />;
  }

  const cycleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  };

  return (
    <button
      onClick={cycleTheme}
      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
      title={`Thème: ${theme}`}
    >
      {theme === 'dark' ? (
        <Moon className="w-5 h-5 text-gray-500" />
      ) : theme === 'light' ? (
        <Sun className="w-5 h-5 text-gray-500" />
      ) : (
        <Monitor className="w-5 h-5 text-gray-500" />
      )}
    </button>
  );
}
