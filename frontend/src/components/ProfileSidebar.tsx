'use client';

import { X, User, Home, Car, CreditCard, MapPin, Thermometer, Gauge } from 'lucide-react';

interface ProfileSummary {
  rfr?: number;
  household_size?: number;
  income_bracket?: string;
  bracket_color?: string;
  commune?: string;
  dpe_class?: string;
  property_type?: string;
  surface_m2?: number;
}

const BRACKET_LABELS: Record<string, string> = {
  tres_modeste: 'Très modeste',
  modeste: 'Modeste',
  intermediaire: 'Intermédiaire',
  superieur: 'Supérieur',
};

const BRACKET_COLORS: Record<string, string> = {
  bleu: 'bg-blue-500',
  jaune: 'bg-yellow-500',
  violet: 'bg-violet-500',
  rose: 'bg-pink-500',
};

const DPE_COLORS: Record<string, string> = {
  A: 'bg-green-600',
  B: 'bg-green-500',
  C: 'bg-yellow-400',
  D: 'bg-yellow-500',
  E: 'bg-orange-400',
  F: 'bg-orange-600',
  G: 'bg-red-600',
};

export function ProfileSidebar({
  profile,
  isOpen,
  onClose,
}: {
  profile: ProfileSummary;
  isOpen: boolean;
  onClose: () => void;
}) {
  const hasData = Object.keys(profile).length > 0;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:relative z-50 md:z-auto
          w-72 h-full bg-white dark:bg-gray-900
          border-r border-gray-200 dark:border-gray-800
          transform transition-transform duration-200
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          flex-shrink-0
        `}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <User className="w-4 h-4" />
              Votre profil
            </h2>
            <button
              onClick={onClose}
              className="md:hidden p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {!hasData ? (
            <div className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
              Les informations de votre profil
              apparaîtront ici au fil de la conversation.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Income */}
              {(profile.rfr || profile.income_bracket) && (
                <ProfileSection icon={<CreditCard className="w-4 h-4" />} title="Revenus">
                  {profile.rfr && (
                    <ProfileItem
                      label="RFR"
                      value={`${profile.rfr.toLocaleString('fr-FR')} €`}
                    />
                  )}
                  {profile.household_size && (
                    <ProfileItem
                      label="Foyer"
                      value={`${profile.household_size} personne(s)`}
                    />
                  )}
                  {profile.income_bracket && (
                    <div className="flex items-center gap-2 mt-1">
                      {profile.bracket_color && (
                        <div
                          className={`w-3 h-3 rounded-full ${
                            BRACKET_COLORS[profile.bracket_color] || 'bg-gray-400'
                          }`}
                        />
                      )}
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {BRACKET_LABELS[profile.income_bracket] || profile.income_bracket}
                      </span>
                    </div>
                  )}
                </ProfileSection>
              )}

              {/* Property */}
              {(profile.dpe_class || profile.property_type || profile.surface_m2) && (
                <ProfileSection icon={<Home className="w-4 h-4" />} title="Logement">
                  {profile.property_type && (
                    <ProfileItem
                      label="Type"
                      value={profile.property_type === 'maison' ? 'Maison' : 'Appartement'}
                    />
                  )}
                  {profile.surface_m2 && (
                    <ProfileItem label="Surface" value={`${profile.surface_m2} m²`} />
                  )}
                  {profile.dpe_class && (
                    <div className="flex items-center gap-2 mt-1">
                      <div
                        className={`w-8 h-6 rounded text-white text-xs font-bold flex items-center justify-center ${
                          DPE_COLORS[profile.dpe_class] || 'bg-gray-400'
                        }`}
                      >
                        {profile.dpe_class}
                      </div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        Classe DPE
                      </span>
                    </div>
                  )}
                </ProfileSection>
              )}

              {/* Location */}
              {profile.commune && (
                <ProfileSection icon={<MapPin className="w-4 h-4" />} title="Localisation">
                  <ProfileItem label="Commune" value={profile.commune} />
                </ProfileSection>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function ProfileSection({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  );
}

function ProfileItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500 dark:text-gray-400">{label}</span>
      <span className="font-medium text-gray-800 dark:text-gray-200">{value}</span>
    </div>
  );
}
