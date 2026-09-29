/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        // Used by the lettered quotation/contract templates for their
        // Arabic blocks (see src/components/project/letters/).
        arabic: ['"Noto Naskh Arabic"', '"Segoe UI"', 'Tahoma', 'sans-serif'],
        // Page headings, hero text and big numbers. A geometric sans with a
        // little more character than Inter: modern and confident without
        // the editorial serif look, which read as dated in an enterprise app.
        display: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Deep navy -- the enterprise "ink" colour for strong chrome
        // (logo mark, progress, emphasis text). Replaces the old graphite
        // ramp, which read as black-and-grey next to the brand blue.
        primary: {
          50: '#f1f4f9',
          100: '#e2e8f2',
          200: '#c5d0e3',
          300: '#9aabc9',
          400: '#6a80a8',
          500: '#475d85',
          600: '#2c3e63',
          700: '#1c2b4a',
          800: '#131e36',
          900: '#0b1224',
        },
        // Cool slate greys: crisp against white and the brand blue, where
        // the previous warm greys made the light theme look muddy.
        neutral: {
          0: '#ffffff',
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        // Brand accent -- admin-configurable (Administration > Company >
        // Branding), not a fixed hue. Each shade resolves through a CSS
        // custom property (--color-accent-N, defined in src/styles/
        // main.css's :root with a #2563eb default and overridden at
        // runtime by src/utils/colorScale.ts's applyBrandColor) rather
        // than a static hex, so the whole 50-900 ramp -- and everywhere
        // it's used, buttons/badges/links/focus rings included -- follows
        // whatever color an admin picks, without a rebuild. The rgb(...
        // / <alpha-value>) wrapper is Tailwind's documented pattern for
        // CSS-variable colors that still support opacity modifiers like
        // bg-accent-500/10 -- the variable itself holds a plain "R G B"
        // triplet, not a full color, so <alpha-value> can be spliced in.
        accent: {
          50: 'rgb(var(--color-accent-50) / <alpha-value>)',
          100: 'rgb(var(--color-accent-100) / <alpha-value>)',
          200: 'rgb(var(--color-accent-200) / <alpha-value>)',
          300: 'rgb(var(--color-accent-300) / <alpha-value>)',
          400: 'rgb(var(--color-accent-400) / <alpha-value>)',
          500: 'rgb(var(--color-accent-500) / <alpha-value>)',
          600: 'rgb(var(--color-accent-600) / <alpha-value>)',
          700: 'rgb(var(--color-accent-700) / <alpha-value>)',
          800: 'rgb(var(--color-accent-800) / <alpha-value>)',
          900: 'rgb(var(--color-accent-900) / <alpha-value>)',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        // Sky rather than cyan: stays clearly "informational" while sitting
        // comfortably next to the corporate blue instead of clashing with it.
        info: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        ai: {
          50: '#f5f3ff',
          100: '#ede9fe',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
        },
        bg: {
          page: 'var(--color-bg-page)',
          card: 'var(--color-bg-card)',
          secondary: 'var(--color-bg-secondary)',
          sidebar: 'var(--color-bg-sidebar)',
          header: 'var(--color-bg-header)',
          hover: 'var(--color-bg-hover)',
          selected: 'var(--color-bg-selected)',
        },
        border: {
          light: 'var(--color-border-light)',
          default: 'var(--color-border-default)',
          strong: 'var(--color-border-strong)',
          focus: 'var(--color-border-focus)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          inverse: 'var(--color-text-inverse)',
          link: 'var(--color-text-link)',
        },
      },
      spacing: {
        18: '4.5rem',
        70: '17.5rem',
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1.35' }],
        sm: ['0.875rem', { lineHeight: '1.45' }],
        base: ['1rem', { lineHeight: '1.5' }],
        lg: ['1.125rem', { lineHeight: '1.5' }],
        xl: ['1.25rem', { lineHeight: '1.4' }],
        '2xl': ['1.5rem', { lineHeight: '1.35' }],
        '3xl': ['1.875rem', { lineHeight: '1.3' }],
        '4xl': ['2.25rem', { lineHeight: '1.25' }],
        '5xl': ['3rem', { lineHeight: '1.15' }],
      },
      boxShadow: {
        // These read from CSS custom properties (defined per-theme in
        // main.css) rather than fixed rgb values. Previously every one of
        // these was tuned only for the light surface -- a warm, low-opacity
        // black shadow that all but disappears against the near-black dark
        // page background, leaving every card/sidebar/button flat in dark
        // mode. Routing through vars lets .dark redefine them with their
        // own (deeper, higher-contrast) values so both themes get matching
        // depth without touching every component that already uses these
        // utility classes.
        soft: 'var(--shadow-soft)',
        medium: 'var(--shadow-medium)',
        elevated: 'var(--shadow-elevated)',
        glass: 'var(--shadow-glass)',
        'glass-dark': 'var(--shadow-glass)',
        'glass-sm': 'var(--shadow-glass-sm)',
        'glow-accent': 'var(--shadow-glow-accent)',
      },
      borderRadius: {
        md: '0.5rem',
        lg: '0.625rem',
        xl: '0.75rem',
        '2xl': '1rem',
      },
      zIndex: {
        base: '0',
        sticky: '10',
        dropdown: '20',
        drawer: '30',
        modal: '40',
        notification: '50',
        tooltip: '60',
      },
      transitionDuration: {
        fast: '120ms',
        normal: '200ms',
        slow: '320ms',
      },
      screens: {
        tablet: '768px',
        laptop: '1024px',
        desktop: '1280px',
        wide: '1536px',
      },
    },
  },
  plugins: [],
}
