import pluginVue from 'eslint-plugin-vue'
import vueTsEslintConfig from '@vue/eslint-config-typescript'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default [
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },
  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**', '**/node_modules/**'],
  },
  ...pluginVue.configs['flat/essential'],
  ...vueTsEslintConfig(),
  skipFormatting,
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      'vue/multi-word-component-names': 'off',
    },
  },
  {
    // `throw new Error(error instanceof Error ? error.message : '...')` turns
    // an ApiError into a bare Error and discards its HTTP status, so nothing
    // downstream can tell a 429 from a 403 or a 500 (that is how the Handover
    // remount loop hid behind a generic "Unable to load contracts").
    name: 'app/services-keep-api-errors',
    files: ['src/services/**/*.ts'],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector:
            "ThrowStatement > NewExpression[callee.name='Error'] > ConditionalExpression[test.operator='instanceof'][test.right.name='Error']",
          message:
            "Don't rebuild the error by hand -- it drops an ApiError's HTTP status. Use `throw asError(error, 'fallback message')` from '@/services/httpClient'.",
        },
      ],
    },
  },
]
