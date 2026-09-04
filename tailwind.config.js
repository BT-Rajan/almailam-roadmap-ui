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
        // Editorial display serif for page headings and hero text -- gives
        // headings a premium, less "default SaaS" feel than Inter alone.
        display: ['"Playfair Display"', 'ui-serif', 'Georgia', 'serif'],
      },
      colors: {
        // Rich graphite/charcoal — the "Uber-black" premium action colour
        primary: {
          50: '#f4f4f5',
          100: '#e7e7ea',
          200: '#d3d3d8',
          300: '#b0b0ba',
          400: '#85858f',
          500: '#5c5c68',
          600: '#2e2e38',
          700: '#1c1c24',
          800: '#131319',
          900: '#0a0a0c',
        },
        // Warm luxury grey scale used for the glass surfaces + chrome
        neutral: {
          0: '#ffffff',
          50: '#f7f7f8',
          100: '#eeeef1',
          200: '#e1e1e6',
          300: '#c9c9d1',
          400: '#a3a3ad',
          500: '#797983',
          600: '#5c5c66',
          700: '#44444d',
          800: '#292930',
          900: '#17171a',
        },
        // Champagne / bronze accent used sparingly for premium highlights
        accent: {
          50: '#fbf8f0',
          100: '#f5ecd8',
          200: '#ead9b0',
          300: '#dcbf7d',
          400: '#cca753',
          500: '#b8903a',
          600: '#96742c',
          700: '#765a22',
          800: '#5b451b',
          900: '#453415',
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
        info: {
          50: '#ecfeff',
          100: '#cffafe',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
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
