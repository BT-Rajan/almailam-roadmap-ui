<script setup lang="ts">
import { Check, Clock, Download, FileCheck2, Loader2, Upload } from '@lucide/vue'
import type { Component } from 'vue'

import StatusBadge from '@/components/common/StatusBadge.vue'
import type { RequiredDocumentStatus, SubmissionDocument } from '@/types/Submission'
import { getDocumentStatusVariant } from '@/utils/submissionHelpers'

interface Props {
  documents: SubmissionDocument[]
  // Uploading a required document is only allowed while the submission
  // sits in Draft -- callers pass this through rather than duplicating
  // the status check here.
  canUpload: boolean
  // Which document (if any) has an upload in flight, so the button for
  // just that row can show a spinner.
  uploadingDocumentId?: number
}

defineProps<Props>()

const emit = defineEmits<{
  upload: [documentId: number, file: File]
  download: [documentId: number]
}>()

const STATUS_ICONS: Record<RequiredDocumentStatus, Component> = {
  Pending: Clock,
  Uploaded: FileCheck2,
  Verified: Check,
}

function handleFileChange(documentId: number, event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  emit('upload', documentId, file)
  ;(event.target as HTMLInputElement).value = ''
}
</script>

<template>
  <ul class="flex flex-col divide-y divide-border-light">
    <li v-for="document in documents" :key="document.id" class="flex flex-col gap-2 py-3">
      <div class="flex items-center justify-between gap-3">
        <span class="inline-flex items-center gap-2 text-sm text-text-secondary">
          <component :is="STATUS_ICONS[document.status]" class="h-4 w-4 text-text-muted" />
          {{ document.name }}
        </span>
        <StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" size="sm" />
      </div>

      <div class="flex items-center justify-between gap-3 pl-6">
        <span v-if="document.originalFilename" class="truncate text-xs text-text-muted">
          {{ document.originalFilename }}
          <template v-if="document.fileSizeLabel"> &middot; {{ document.fileSizeLabel }}</template>
          <template v-if="document.uploadDate"> &middot; uploaded {{ document.uploadDate }}</template>
        </span>
        <span v-else class="text-xs text-text-muted">Not uploaded yet</span>

        <div class="flex shrink-0 items-center gap-2">
          <button
            v-if="document.originalFilename"
            type="button"
            class="inline-flex items-center gap-1 rounded-md border border-border-default px-2 py-1 text-xs font-medium text-text-secondary hover:bg-bg-secondary"
            @click="emit('download', document.id)"
          >
            <Download class="h-3.5 w-3.5" />
            Download
          </button>

          <label
            v-if="canUpload"
            class="inline-flex cursor-pointer items-center gap-1 rounded-md border border-primary-300 bg-primary-50 px-2 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100"
          >
            <Loader2 v-if="uploadingDocumentId === document.id" class="h-3.5 w-3.5 animate-spin" />
            <Upload v-else class="h-3.5 w-3.5" />
            {{ document.originalFilename ? 'Replace' : 'Upload' }}
            <input
              type="file"
              class="hidden"
              accept=".pdf,.doc,.docx,.dwg,.xlsx,.png,.jpg,.jpeg,.tiff,.tif"
              @change="handleFileChange(document.id, $event)"
            />
          </label>
        </div>
      </div>
    </li>
  </ul>
</template>
