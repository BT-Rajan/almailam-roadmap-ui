import { defineConfig, devices } from '@playwright/test'

// A deliberately separate stream from the main playwright.config.ts /
// e2e/ folder (see e2e-workflow/README.md for why). Same "you start the
// backend yourself" contract as the main config -- this only launches
// the Vite dev server, which proxies /api to whatever VITE_API_PROXY_TARGET
// (or the default localhost:8000) is already running.
//
// workers: 1 and no fullyParallel: this suite is one continuous story
// (one client -> one project -> one workflow run -> its reports) told
// across four numbered files that share state via .artifacts/state.json
// (see helpers/state.ts). They must run in file order, one at a time,
// in a single worker -- never in parallel with each other.
export default defineConfig({
  testDir: '.',
  testMatch: /\d\d-.*\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: 'list',
  globalSetup: require.resolve('./global-setup.ts'),
  globalTeardown: require.resolve('./global-teardown.ts'),
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
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
      name: 'Desktop Chrome',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
