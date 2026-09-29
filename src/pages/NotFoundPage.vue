<script setup lang="ts">
import { ArrowLeft, Compass } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'

const { t } = useI18n()
const router = useRouter()
</script>

<!-- Rendered inside AuthLayout's card, so it must fit that card rather
     than fill the screen. The dashboard route bounces signed-out visitors
     to the login page, so one link covers both cases. -->
<template>
  <div class="flex flex-col items-center py-4 text-center">
    <span class="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-50 text-accent-600 dark:bg-accent-500/15">
      <Compass class="h-7 w-7" />
    </span>
    <p class="mt-5 font-display text-5xl font-bold text-accent-500">404</p>
    <h1 class="mt-2 font-display text-xl font-bold text-text-primary">{{ t('placeholder.pageNotFound') }}</h1>
    <p class="mt-2 max-w-xs text-sm text-text-secondary">{{ t('placeholder.pageNotFoundDescription') }}</p>
    <BaseButton class="mt-6" :icon="ArrowLeft" @click="router.push({ name: ROUTE_NAMES.DASHBOARD })">
      {{ t('placeholder.backToDashboard') }}
    </BaseButton>
  </div>
</template>
