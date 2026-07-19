<script setup lang="ts">
import { ArrowRight, ListChecks } from '@lucide/vue'

import Card from '@/components/common/Card.vue'

interface Props {
  suggestions: string[]
}

defineProps<Props>()

const emit = defineEmits<{
  select: [suggestion: string]
}>()
</script>

<template>
  <Card>
    <template #header>
      <div class="flex items-center gap-2">
        <ListChecks class="h-5 w-5 text-ai-600" />
        <h3 class="text-sm font-semibold text-neutral-800">Suggested Actions</h3>
      </div>
    </template>

    <ul class="flex flex-col gap-2">
      <li v-for="suggestion in suggestions" :key="suggestion">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 rounded-lg border border-border-light px-3 py-2.5 text-left text-sm text-neutral-700 transition-colors duration-fast hover:border-ai-200 hover:bg-ai-50"
          @click="emit('select', suggestion)"
        >
          <span>{{ suggestion }}</span>
          <ArrowRight class="h-4 w-4 shrink-0 text-neutral-400" />
        </button>
      </li>
    </ul>
  </Card>
</template>
