<script setup lang="ts">
import { CalendarClock, Download, Eye, FileText } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import type { ClientDocument } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'

defineProps<{
  document: ClientDocument
}>()

defineEmits<{
  view: [document: ClientDocument]
  download: [document: ClientDocument]
}>()
</script>

<template>
  <Card>
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <FileText class="h-5 w-5 text-primary-600" />
          </span>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ document.category }}</p>
            <h3 class="text-sm font-semibold leading-snug text-neutral-800">{{ document.title }}</h3>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2 no-print">
          <IconButton :icon="Eye" label="View document" size="sm" @click="$emit('view', document)" />
          <IconButton :icon="Download" label="Download document" size="sm" @click="$emit('download', document)" />
        </div>
      </div>

      <div class="flex items-center justify-end border-t border-border-light pt-3 text-xs text-neutral-500">
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(document.uploadDate) }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
