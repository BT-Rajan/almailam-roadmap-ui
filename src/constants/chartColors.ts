// Single source of truth for report chart series colors -- see the
// matching custom properties in src/styles/main.css. Previously each
// chart component/page hardcoded its own '#3B82F6' etc. literal.
export const CHART_COLORS = {
  blue: 'var(--chart-blue)',
  purple: 'var(--chart-purple)',
  cyan: 'var(--chart-cyan)',
  amber: 'var(--chart-amber)',
} as const

export const DEFAULT_CHART_COLOR = CHART_COLORS.blue

// Status-driven chart colors, matching the app's own danger/warning/success
// token scale (see tailwind.config.js) rather than an unrelated stock hue.
export const STATUS_CHART_COLORS = {
  danger: 'var(--chart-danger)',
  warning: 'var(--chart-warning)',
  success: 'var(--chart-success)',
} as const

// Semantic names the backend sends for status series (see report_service.
// _status_color). Used as a raw SVG fill, a name like "success" isn't a
// valid color, so the browser painted those bars black.
const SEMANTIC_CHART_COLORS: Record<string, string> = {
  primary: 'var(--chart-primary)',
  info: 'var(--chart-info)',
  ...STATUS_CHART_COLORS,
}

/** A chart color from a data point: a semantic name, a CSS color, or the default. */
export function resolveChartColor(color: string | undefined): string {
  if (!color) return DEFAULT_CHART_COLOR
  return SEMANTIC_CHART_COLORS[color] ?? color
}
