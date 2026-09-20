<script setup lang="ts">
import { Download, Eye, FileText } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import IconButton from '@/components/common/IconButton.vue'
import { useToastStore } from '@/stores/toastStore'
import { formatDate } from '@/utils/dateFormatter'
import { downloadSubmissionFile, viewSubmissionFile } from '@/utils/submissionFiles'
import type { SubmissionFile } from '@/utils/submissionFiles'

// The uploaded files of a permit application (see utils/submissionFiles.ts),
// each with a view link (opens the file in a new tab) and a download
// button. Shared by the application's Overview / Close tabs and the
// project's Scope > Documents tab, so the file rows look and behave the
// same in all of them. Renders bare rows -- wrap in a Card (padded=false)
// or a group of your own.
defineProps<{
  files: SubmissionFile[]
}>()

const { t } = useI18n()
const toastStore = useToastStore()

async function handleView(file: SubmissionFile): Promise<void> {
  try {
    await viewSubmissionFile(file)
  } catch {
    toastStore.show('error', t('project.documentsTab.failedToOpenDocument'), t('common.pleaseTryAgain'))
  }
}

async function handleDownload(file: SubmissionFile): Promise<void> {
  try {
    await downloadSubmissionFile(file)
  } catch {
    toastStore.show('error', t('common.downloadFailed'), t('common.pleaseTryAgain'))
  }
}

function metaLine(file: SubmissionFile): string {
  const parts: string[] = [file.filename]
  if (file.sizeLabel) parts.push(file.sizeLabel)
  if (file.uploadDate && file.uploadedBy) {
    parts.push(t('government.workspacePage.uploadedByLine', { date: formatDate(file.uploadDate), user: file.uploadedBy }))
  }
  return parts.join(' · ')
}
</script>

<template>
  <ul class="flex flex-col divide-y divide-border-light">
    <li v-for="file in files" :key="file.key" class="flex items-center justify-between gap-3 px-5 py-4">
      <div class="flex min-w-0 items-center gap-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
          <FileText class="h-5 w-5" />
        </span>
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-text-primary">{{ file.label }}</p>
          <p class="truncate text-xs text-text-muted">{{ metaLine(file) }}</p>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-1 no-print">
        <IconButton :icon="Eye" :label="t('document.card.viewDocument')" size="sm" @click="handleView(file)" />
        <IconButton v-if="!file.externalLink" :icon="Download" :label="t('common.download')" size="sm" @click="handleDownload(file)" />
      </div>
    </li>
  </ul>
</template>
