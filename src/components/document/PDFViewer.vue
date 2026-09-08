<script setup lang="ts">
import { FileQuestion, Link as LinkIcon } from '@lucide/vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { documentService } from '@/services/documentService'
import type { ProjectDocument } from '@/types/Document'

const props = defineProps<{
  document: ProjectDocument
}>()

const { t } = useI18n()

const isLoading = ref(false)
const loadError = ref<string | undefined>(undefined)
const objectUrl = ref<string | undefined>(undefined)
const blobType = ref('')

// Only PDFs and images can be rendered inline in the browser with no
// extra dependency -- everything else (Word, Excel, DWG, ...) falls
// back to a plain "preview not available" state instead of a blank or
// broken frame.
const previewKind = computed<'pdf' | 'image' | 'unsupported'>(() => {
  if (blobType.value === 'application/pdf') return 'pdf'
  if (blobType.value.startsWith('image/')) return 'image'
  return 'unsupported'
})

function revokeCurrentUrl(): void {
  if (objectUrl.value) {
    URL.revokeObjectURL(objectUrl.value)
    objectUrl.value = undefined
  }
}

// Previously this component never fetched or rendered any real file at
// all -- it was a static mock (icon + title + fake "Preview page N"
// text) regardless of what was actually uploaded. This fetches the
// real bytes and renders them via a Blob object URL, the same download
// endpoint VersionHistory/download actions already use, just consumed
// as a preview instead of a Save-As.
async function loadPreview(): Promise<void> {
  revokeCurrentUrl()
  loadError.value = undefined
  blobType.value = ''

  // A link-only document (no uploaded file) has nothing to fetch.
  if (!props.document.originalFilename) return

  isLoading.value = true
  try {
    const blob = await documentService.downloadDocument(props.document.id)
    blobType.value = blob.type
    objectUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    loadError.value = error instanceof Error && error.message ? error.message : t('document.pdfViewer.failedToLoadPreview')
  } finally {
    isLoading.value = false
  }
}

watch(() => props.document.id, loadPreview, { immediate: true })
onBeforeUnmount(revokeCurrentUrl)

function openExternalLink(): void {
  if (props.document.externalLink) window.open(props.document.externalLink, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <div class="flex min-h-[420px] flex-col overflow-hidden rounded-lg border border-border-light bg-bg-secondary">
    <div v-if="isLoading" class="flex-1 p-6">
      <SkeletonLoader :rows="8" />
    </div>

    <ErrorState v-else-if="loadError" class="flex-1" :description="loadError" @retry="loadPreview" />

    <EmptyState
      v-else-if="!document.originalFilename"
      class="flex-1"
      :icon="LinkIcon"
      :title="t('document.pdfViewer.linkOnlyTitle')"
      :description="t('document.pdfViewer.linkOnlyDescription')"
      :action-label="document.externalLink ? t('document.pdfViewer.openLink') : undefined"
      @action="openExternalLink"
    />

    <iframe
      v-else-if="previewKind === 'pdf' && objectUrl"
      :src="objectUrl"
      :title="document.title"
      class="min-h-[600px] w-full flex-1 border-0"
    />

    <div v-else-if="previewKind === 'image' && objectUrl" class="flex flex-1 items-center justify-center overflow-auto p-4">
      <img :src="objectUrl" :alt="document.title" class="max-h-[70vh] max-w-full object-contain" />
    </div>

    <EmptyState
      v-else
      class="flex-1"
      :icon="FileQuestion"
      :title="t('document.pdfViewer.unsupportedTitle')"
      :description="t('document.pdfViewer.unsupportedDescription')"
    />
  </div>
</template>
