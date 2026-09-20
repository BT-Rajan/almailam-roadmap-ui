import { describe, expect, it } from 'vitest'

// Every page renders inside DashboardLayout's <main>, which adds no
// padding of its own -- each page's root element has to inset its own
// content, or its cards and headings sit flush against the viewport edge
// (the dashboard did exactly that). Pages outside that layout are
// listed with the reason they don't need it.
const OWN_LAYOUT: Record<string, string> = {
  'LoginPage.vue': 'AuthLayout, no dashboard chrome',
  'PlaceholderPage.vue': 'full-screen page that pads itself with px-6',
  'SitePortalLoginPage.vue': 'AuthCard inside the site portal layout',
  'SitePortalCalendarPage.vue': 'SitePortalLayout pads <main> with px-4 py-6',
  'SitePortalReportPage.vue': 'SitePortalLayout pads <main> with px-4 py-6',
}

// Raw source of every page (Vite inlines these; no Node types needed).
const sources = import.meta.glob('./*.vue', { query: '?raw', import: 'default', eager: true }) as Record<string, string>
const pageFiles = Object.keys(sources).map((path) => path.replace('./', ''))

function rootClasses(source: string): string {
  const template = source.slice(source.indexOf('<template>') + '<template>'.length)
  const root = template.match(/<([A-Za-z][\w-]*)([^>]*)>/)
  return root?.[2].match(/class="([^"]*)"/)?.[1] ?? ''
}

describe('every dashboard page insets its own content', () => {
  it('finds the pages', () => {
    expect(pageFiles.length).toBeGreaterThan(30)
  })

  for (const file of pageFiles) {
    if (file in OWN_LAYOUT) continue
    it(`${file} has padding on its root element`, () => {
      const classes = rootClasses(sources[`./${file}`])
      expect(classes, `root classes of ${file}: "${classes}"`).toMatch(/(^|\s)(p|px)-\d/)
    })
  }
})
