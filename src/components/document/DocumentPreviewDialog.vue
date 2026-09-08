<script setup lang="ts">
import { Download } from '@lucide/vue'
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import PDFViewer from '@/components/document/PDFViewer.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'

// Opens a document's real preview inline, from wherever it's referenced
// inside a project (Design tab, Required Documents, filed government
// forms) -- as a dialog over the current page, never a route change.
// Navigating to the standalone /documents/:id page used to drop the
// user out of the project entirely (a different breadcrumb, no way
// back into the project they were working in); this keeps them on the
// exact same project tab throughout.
const props = defineProps<{
  modelValue: boolean
  documentId: string | undefined
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

watch(
  () => [props.modelValue, props.documentId] as const,
  ([open, documentId]) => {
    if (open && documentId) documentStore.loadDocumentDetail(documentId)
  },
  { immediate: true },
)

// Guards against a stale currentDocument (from whatever was last
// previewed/viewed elsewhere via this same store) flashing before the
// fresh load for this dialog's documentId resolves.
const document = computed(() =>
  documentStore.currentDocument?.id === props.documentId ? documentStore.currentDocument : undefined,
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

async function handleDownload(): Promise<void> {
  try {
    await documentStore.downloadCurrentDocument()
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('document.viewerPage.failedToDownloadDocument'), detail)
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="document?.title ?? t('document.viewerPage.documentViewer')" size="lg" @update:model-value="closeDialog">
    <ErrorState v-if="documentStore.error" :description="documentStore.error" />
    <SkeletonLoader v-else-if="documentStore.isDetailLoading || !document" :rows="8" />
    <PDFViewer v-else :document="document" />

    <template #footer>
      <BaseButton v-if="document" :icon="Download" variant="secondary" @click="handleDownload">{{ t('document.viewerPage.download') }}</BaseButton>
      <BaseButton variant="primary" @click="closeDialog">{{ t('common.close') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
