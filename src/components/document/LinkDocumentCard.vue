<script setup lang="ts">
import { CalendarClock, Download, Eye, ExternalLink, Trash2, UserRound } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import type { ProjectLinkDocument } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'

defineProps<{
  document: ProjectLinkDocument
}>()

defineEmits<{
  delete: [document: ProjectLinkDocument]
}>()

// There's no file stored through the app for these -- "View" and
// "Download" both just take the person to wherever the document actually
// lives (a shared drive, a government portal, etc.), same as clicking the
// link itself.
function openDocument(path: string): void {
  window.open(path, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <Card>
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <ExternalLink class="h-5 w-5 text-primary-600" />
          </span>
          <h3 class="text-sm font-semibold leading-snug text-neutral-800">{{ document.name }}</h3>
        </div>
        <div class="flex shrink-0 items-center gap-2 no-print">
          <IconButton :icon="Eye" label="View document" size="sm" @click="openDocument(document.path)" />
          <IconButton :icon="Download" label="Download document" size="sm" @click="openDocument(document.path)" />
          <IconButton :icon="Trash2" label="Remove document" size="sm" variant="danger" @click="$emit('delete', document)" />
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-neutral-500">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ document.addedBy }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(document.addedDate) }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
