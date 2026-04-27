import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/ThemeProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'GreenRights — Vos aides à la transition écologique',
  description:
    'Découvrez toutes les aides financières pour la rénovation énergétique et la mobilité propre en France.',
  keywords: ['MaPrimeRénov', 'aide rénovation', 'prime conversion', 'ZFE', 'transition écologique'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
