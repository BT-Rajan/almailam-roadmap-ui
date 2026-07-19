<script setup lang="ts">
import { Download, Printer } from '@lucide/vue'
import BaseButton from '@/components/common/BaseButton.vue'

interface Props {
  title: string
  subtitle?: string
  generatedDate?: string
  showActions?: boolean
}

withDefaults(defineProps<Props>(), {
  subtitle: undefined,
  generatedDate: undefined,
  showActions: true,
})

defineEmits<{
  print: []
  download: []
}>()

const handlePrint = () => {
  window.print()
}
</script>

<template>
  <div class="space-y-4 pb-6 border-b border-border-light print:border-b-0">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-neutral-900">{{ title }}</h1>
        <p v-if="subtitle" class="text-neutral-600 mt-1">{{ subtitle }}</p>
        <p v-if="generatedDate" class="text-xs text-neutral-400 mt-2">Generated: {{ generatedDate }}</p>
      </div>
      <div v-if="showActions" class="flex gap-2 print:hidden">
        <BaseButton variant="ghost" size="sm" @click="handlePrint">
          <Printer class="h-4 w-4" />
          Print
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="$emit('download')">
          <Download class="h-4 w-4" />
          Export
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  :deep(button) {
    display: none;
  }
}
</style>
