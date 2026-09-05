<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const currentYear = new Date().getFullYear()
const { t } = useI18n()
</script>

<template>
  <footer
    class="flex h-14 shrink-0 items-center justify-between border-t border-[var(--color-border-light)] bg-bg-secondary px-4 text-xs text-[var(--color-text-muted)] lg:px-6"
  >
    <span>&copy; {{ currentYear }} {{ t('common.companyName') }}</span>
    <span>{{ t('common.appName') }}</span>
  </footer>
</template>
