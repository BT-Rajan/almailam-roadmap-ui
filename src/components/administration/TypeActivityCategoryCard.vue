<script setup lang="ts">
import { ListChecks } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import type { TypeActivityCategory } from '@/types/TypeActivityCatalog'

defineProps<{
  category: TypeActivityCategory
  active: boolean
}>()

defineEmits<{
  select: [categoryId: string]
}>()
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
    role="button"
    tabindex="0"
    :aria-label="`Select ${category.name} type category`"
    :aria-pressed="active"
    :class="active ? 'border-primary-400 ring-1 ring-primary-400' : ''"
    @click="$emit('select', category.id)"
    @keydown.enter.space.prevent="$emit('select', category.id)"
  >
    <div class="flex items-start gap-3">
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50">
        <ListChecks class="h-4 w-4 text-primary-600" />
      </span>
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-text-primary truncate">{{ category.name }}</p>
        <p class="mt-1 text-sm text-text-muted">{{ category.activities.length }} activities</p>
      </div>
    </div>
  </Card>
</template>
