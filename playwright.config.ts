import { defineConfig, devices } from '@playwright/test'

// Run against the Vite dev server (which proxies /api to the backend --
// see vite.config.ts). Start the backend yourself first (see
// backend/.env.example's Quick Start); this config only launches the
// frontend dev server, since Playwright's webServer option launches one
// process and the backend needs its own DB setup step first.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
