<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import { ICONS } from '@/utils/icons'
import type { AdministrationModule } from '@/constants/administrationModules'

interface Props {
  module: AdministrationModule
}

const props = defineProps<Props>()

const icon = computed(() => ICONS[props.module.icon])
</script>

<template>
  <RouterLink :to="{ name: module.routeName }" class="block">
    <Card hoverable class="cursor-pointer">
      <div class="flex items-start gap-4">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
          <component :is="icon" :size="20" />
        </span>
        <div class="min-w-0 flex-1">
          <p class="font-medium text-neutral-900">{{ module.label }}</p>
          <p class="mt-1 text-sm text-neutral-500">{{ module.description }}</p>
        </div>
        <ChevronRight :size="18" class="mt-1 shrink-0 text-neutral-300" aria-hidden="true" />
      </div>
    </Card>
  </RouterLink>
</template>
