<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  titleKey?: string
}>()

const { t } = useI18n()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-bg-secondary px-6">
    <div class="text-center">
      <p class="text-sm font-medium uppercase tracking-wide text-primary-600">{{ t('common.appName') }}</p>
      <h1 class="mt-2 text-2xl font-semibold text-text-primary">{{ props.titleKey ? t(props.titleKey) : t('placeholder.comingSoon') }}</h1>
      <p class="mt-2 text-sm text-text-muted">
        {{ t('placeholder.comingSoonDescription') }}
      </p>
    </div>
  </div>
</template>
