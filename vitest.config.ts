import { fileURLToPath, URL } from 'node:url'

import { defineConfig, mergeConfig } from 'vite'
import { defineConfig as defineVitestConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// Deliberately not importing vite.config.ts directly -- it's fine as
// its own small object here since the two config shapes (root `server`
// vs vitest's own `test`) don't really overlap, and duplicating the
// one alias is simpler than fighting mergeConfig's merge semantics.
export default mergeConfig(
  defineConfig({
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }),
  defineVitestConfig({
    test: {
      environment: 'happy-dom',
      // happy-dom enforces CORS just like a real browser -- match its
      // origin to one the backend's CORS_ORIGINS already allows (see
      // backend/.env's CORS_ORIGINS, the same origin the real Vite dev
      // server runs on) rather than opening the backend up further just
      // for this test run.
      environmentOptions: {
        happyDOM: {
          url: 'http://localhost:5173',
        },
      },
      include: ['e2e/component-smoke.test.ts'],
      // No dev-server proxy exists in this environment -- component
      // tests hit the backend directly. See e2e/component-smoke.test.ts.
      env: {
        VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
      },
    },
  }),
)
