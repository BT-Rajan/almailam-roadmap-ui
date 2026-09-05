<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import { ICONS } from '@/utils/icons'
import type { AdministrationModule } from '@/constants/administrationModules'

interface Props {
  module: AdministrationModule
}

const props = defineProps<Props>()

const icon = computed(() => ICONS[props.module.icon])
const { t } = useI18n()
</script>

<template>
  <RouterLink :to="{ name: module.routeName }" class="block">
    <Card hoverable class="cursor-pointer">
      <div class="flex items-start gap-4">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
          <component :is="icon" :size="20" />
        </span>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold text-text-primary">{{ t(module.labelKey) }}</p>
          <p class="mt-1 text-sm text-text-muted">{{ t(module.descriptionKey) }}</p>
        </div>
        <ChevronRight :size="18" class="mt-1 shrink-0 text-text-muted" aria-hidden="true" />
      </div>
    </Card>
  </RouterLink>
</template>
