'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Leaf, Home, Car, Bot, ArrowRight, Sun, Moon, Zap, Shield } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { MistralLogo, MistralLogoAnimated } from '@/components/MistralLogo';
import { FloatingParticles } from '@/components/FloatingParticles';

const DEMO_PROFILES = [
  {
    id: 'marie',
    name: 'Marie',
    description: 'Revenus modestes, maison DPE F à Lyon, Crit\'Air 4',
    emoji: '👩',
  },
  {
    id: 'pierre',
    name: 'Pierre',
    description: 'Revenus intermédiaires, appartement DPE D à Nanterre',
    emoji: '👨',
  },
  {
    id: 'fatima',
    name: 'Fatima',
    description: 'Revenus très modestes, maison DPE G à Grenoble',
    emoji: '👩‍🦱',
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const startChat = async (demoProfile?: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: 'fr',
          demo_mode: !!demoProfile,
          demo_profile: demoProfile || null,
        }),
      });
      const data = await res.json();
      router.push(`/chat?session=${data.session_id}`);
    } catch (err) {
      console.error('Failed to create session:', err);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-gray-950 relative overflow-hidden">
      {/* Background floating particles */}
      <FloatingParticles count={14} />

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <Leaf className="w-8 h-8 text-green-600" />
          <span className="text-xl font-bold text-green-800 dark:text-green-400">GreenRights</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
            <span>propulsé par</span>
            <MistralLogo className="w-4 h-4" />
            <span className="font-medium text-orange-500">Mistral AI</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Hero */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-24">
        <div className="text-center max-w-3xl mx-auto">
          {/* Animated Mistral logo */}
          <div className="flex justify-center mb-6 animate-slide-up">
            <MistralLogoAnimated className="w-16 h-16" />
          </div>

          <div className="inline-flex items-center gap-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-4 py-1.5 rounded-full text-sm font-medium mb-6 animate-slide-up-delay-1 animate-gentle-pulse">
            <Bot className="w-4 h-4" />
            <span>Conseiller IA propulsé par Mistral</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6 leading-tight animate-slide-up-delay-2">
            Découvrez toutes vos{' '}
            <span className="bg-gradient-to-r from-green-600 via-emerald-500 to-green-600 dark:from-green-400 dark:via-emerald-300 dark:to-green-400 animate-text-shimmer">
              aides à la transition écologique
            </span>
          </h1>

          <p className="text-xl text-gray-600 dark:text-gray-300 mb-10 max-w-2xl mx-auto animate-slide-up-delay-3">
            Rénovation énergétique, mobilité propre : notre IA calcule en temps réel
            les montants exacts auxquels vous avez droit. Barèmes officiels 2026.
          </p>

          <div className="animate-slide-up-delay-4">
            <button
              onClick={() => startChat()}
              disabled={loading}
              className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all shadow-lg shadow-green-600/25 hover:shadow-green-600/40 hover:scale-105 active:scale-95 disabled:opacity-50"
            >
              {loading ? 'Chargement...' : 'Commencer ma simulation'}
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-24">
          <FeatureCard
            icon={<Home className="w-6 h-6 text-green-600" />}
            title="Rénovation énergétique"
            description="MaPrimeRénov', CEE, Éco-PTZ : calculez vos aides pour l'isolation, le chauffage, la ventilation…"
          />
          <FeatureCard
            icon={<Car className="w-6 h-6 text-green-600" />}
            title="Mobilité propre"
            description="Prime conversion, bonus vélo, surprime ZFE : trouvez les aides pour votre nouveau véhicule."
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6 text-green-600" />}
            title="Calculs vérifiables"
            description="Chaque montant provient des barèmes officiels ANAH 2026. L'IA ne calcule jamais — elle utilise les outils."
          />
        </div>

        {/* Demo profiles */}
        <div className="mt-24">
          <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
            Essayez avec un profil démo
          </h2>
          <p className="text-center text-gray-500 dark:text-gray-400 mb-8">
            Découvrez GreenRights avec des profils pré-remplis
          </p>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {DEMO_PROFILES.map((profile) => (
              <button
                key={profile.id}
                onClick={() => startChat(profile.id)}
                disabled={loading}
                className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-green-400 dark:hover:border-green-500 transition-all text-left group hover:shadow-md disabled:opacity-50"
              >
                <div className="text-3xl mb-3">{profile.emoji}</div>
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">
                  {profile.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {profile.description}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* How it works */}
        <div className="mt-24 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-12">
            Comment ça marche ?
          </h2>

          <div className="space-y-8">
            <StepCard
              number={1}
              title="Décrivez votre situation"
              description="Répondez aux questions du conseiller IA : revenus, logement, véhicule, projets…"
            />
            <StepCard
              number={2}
              title="Calcul automatique"
              description="L'IA interroge les barèmes officiels 2026 pour calculer chaque aide applicable."
            />
            <StepCard
              number={3}
              title="Recevez votre bilan"
              description="Téléchargez un PDF récapitulatif avec les montants, conditions et démarches à suivre."
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-200 dark:border-gray-800 py-8">
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center justify-center gap-2 mb-2">
            <MistralLogo className="w-4 h-4" />
            <span>Propulsé par <strong className="text-orange-500">Mistral AI</strong></span>
          </div>
          <p>
            GreenRights — Projet de démonstration.
            Barèmes ANAH 2026. Non affilié au gouvernement français.
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl p-6 transition-all hover:shadow-lg hover:shadow-green-100 dark:hover:shadow-green-900/20 hover:-translate-y-1 hover:border-green-300 dark:hover:border-green-700 group">
      <div className="w-12 h-12 bg-green-50 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );
}

function StepCard({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
        {number}
      </div>
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{description}</p>
      </div>
    </div>
  );
}
