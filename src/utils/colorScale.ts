// Generates a Tailwind-style 50-900 tint/shade scale from a single admin-
// picked brand color, and applies it to the document as CSS custom
// properties -- see tailwind.config.js's `accent` color, which resolves
// each shade via rgb(var(--color-accent-N) / <alpha-value>) instead of a
// static hex, and src/styles/main.css's :root, which defines the default
// (pre-branding-load, and pre-login) scale for #3995be. This is what
// makes Administration > Company's brand color picker actually change
// the app's buttons/badges/links/focus rings instead of only being saved
// to a database column nothing reads.

type AccentShade = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900

// Fraction of white mixed in for tints (50-400), 0 at the base color
// (500), and fraction of black mixed in for shades (600-900). Mirrors
// how most Tailwind-scale generators build a ramp around one true color
// rather than a fixed lightness curve, so an arbitrary admin-picked hex
// still produces a coherent 10-step scale.
const MIX_TOWARD_WHITE: Partial<Record<AccentShade, number>> = { 50: 0.95, 100: 0.9, 200: 0.75, 300: 0.6, 400: 0.3 }
const MIX_TOWARD_BLACK: Partial<Record<AccentShade, number>> = { 600: 0.15, 700: 0.3, 800: 0.45, 900: 0.6 }

const SHADES: AccentShade[] = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]

function hexToRgb(hex: string): [number, number, number] | undefined {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!match) return undefined
  const value = match[1]
  return [parseInt(value.slice(0, 2), 16), parseInt(value.slice(2, 4), 16), parseInt(value.slice(4, 6), 16)]
}

function mix([r, g, b]: [number, number, number], toward: [number, number, number], fraction: number): [number, number, number] {
  return [
    Math.round(r * (1 - fraction) + toward[0] * fraction),
    Math.round(g * (1 - fraction) + toward[1] * fraction),
    Math.round(b * (1 - fraction) + toward[2] * fraction),
  ]
}

/**
 * Builds the 50-900 scale for a base hex color, as "R G B" space-
 * separated triplets (the form Tailwind's rgb(var(...) / <alpha-value>)
 * pattern expects) -- undefined if the input isn't a valid #rrggbb hex.
 */
function generateAccentScaleTriplets(baseHex: string): Record<AccentShade, string> | undefined {
  const base = hexToRgb(baseHex)
  if (!base) return undefined

  const scale = {} as Record<AccentShade, string>
  for (const shade of SHADES) {
    const rgb =
      shade in MIX_TOWARD_WHITE ? mix(base, [255, 255, 255], MIX_TOWARD_WHITE[shade]!)
      : shade in MIX_TOWARD_BLACK ? mix(base, [0, 0, 0], MIX_TOWARD_BLACK[shade]!)
      : base
    scale[shade] = rgb.join(' ')
  }
  return scale
}

/**
 * Applies a brand color app-wide by setting --color-accent-50 through
 * --color-accent-900 on the document root. Silently no-ops on an
 * invalid hex (keeps whatever scale -- the #3995be default, or a
 * previously-applied one -- is already in place) rather than throwing,
 * since this runs on app boot and after every admin keystroke in the
 * color picker.
 */
export function applyBrandColor(baseHex: string): void {
  const scale = generateAccentScaleTriplets(baseHex)
  if (!scale) return
  const root = document.documentElement
  for (const shade of SHADES) {
    root.style.setProperty(`--color-accent-${shade}`, scale[shade])
  }
}
