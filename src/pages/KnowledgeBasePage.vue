<script setup lang="ts">
import { FileText, Send, Trash2, Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import KnowledgeUploadDialog from '@/components/knowledge/KnowledgeUploadDialog.vue'
import { useRbac } from '@/composables/useRbac'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useToastStore } from '@/stores/toastStore'
import type { SelectOption } from '@/types/Ui'

const knowledgeStore = useKnowledgeStore()
const toastStore = useToastStore()
const { can } = useRbac()

const isUploadDialogOpen = ref(false)
const question = ref('')
const scopeDocumentId = ref('')

const scopeOptions = computed<SelectOption[]>(() => [
  { label: 'All active documents', value: '' },
  ...knowledgeStore.documents.map((document) => ({ label: document.title, value: document.id, disabled: !document.isActive })),
])

function loadData(): void {
  knowledgeStore.loadDocuments()
}

onMounted(loadData)

async function toggleActive(documentId: string, isActive: boolean): Promise<void> {
  try {
    await knowledgeStore.setDocumentActive(documentId, isActive)
  } catch (error) {
    toastStore.show('error', 'Unable to update document', error instanceof Error && error.message ? error.message : 'Please try again.')
  }
}

async function removeDocument(documentId: string, title: string): Promise<void> {
  try {
    await knowledgeStore.deleteDocument(documentId)
    if (scopeDocumentId.value === documentId) scopeDocumentId.value = ''
    toastStore.show('success', 'Document deleted', `${title} was removed from the knowledge base.`)
  } catch (error) {
    toastStore.show('error', 'Unable to delete document', error instanceof Error && error.message ? error.message : 'Please try again.')
  }
}

async function handleAsk(): Promise<void> {
  const trimmed = question.value.trim()
  if (!trimmed) return
  await knowledgeStore.ask(trimmed, scopeDocumentId.value || undefined)
  if (!knowledgeStore.askError) question.value = ''
}

function documentTitle(documentId: string): string {
  return knowledgeStore.documents.find((document) => document.id === documentId)?.title ?? documentId
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Knowledge Base"
      subtitle="Upload a document and ask questions in Arabic, English, or a mix -- answers are grounded strictly in what you upload."
    >
      <template #actions>
        <BaseButton v-if="can('knowledgebase.upload')" :icon="Upload" @click="isUploadDialogOpen = true">
          Upload Document
        </BaseButton>
      </template>
    </PageHeader>

    <ErrorState v-if="knowledgeStore.error" :description="knowledgeStore.error" @retry="loadData" />

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3 laptop:col-span-1">
        <h2 class="text-sm font-semibold text-text-secondary">Documents</h2>

        <div v-if="knowledgeStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="6" />
        </div>

        <EmptyState
          v-else-if="knowledgeStore.documents.length === 0"
          :icon="FileText"
          title="No documents yet"
          description="Upload a document to start asking questions about it."
        />

        <div v-else class="flex flex-col gap-3">
          <div
            v-for="document in knowledgeStore.documents"
            :key="document.id"
            class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-text-primary">{{ document.title }}</p>
                <p class="truncate text-xs text-text-muted">{{ document.originalFilename }} &middot; {{ document.fileSize }}</p>
              </div>
              <IconButton
                v-if="can('knowledgebase.delete')"
                :icon="Trash2"
                label="Delete document"
                size="sm"
                variant="danger"
                @click="removeDocument(document.id, document.title)"
              />
            </div>

            <div class="flex flex-wrap items-center gap-1.5">
              <StatusBadge
                :label="document.extractionOk ? (document.isActive ? 'Active' : 'Inactive') : 'Extraction failed'"
                :variant="document.extractionOk ? (document.isActive ? 'success' : 'neutral') : 'danger'"
                show-dot
              />
              <StatusBadge v-if="document.truncated" label="Truncated" variant="warning" />
            </div>

            <p v-if="!document.extractionOk" class="text-xs text-danger-500">{{ document.extractionError }}</p>
            <p v-else class="text-xs text-text-muted">{{ document.charCount.toLocaleString() }} characters extracted</p>

            <ToggleSwitch
              v-if="can('knowledgebase.upload')"
              :model-value="document.isActive"
              :disabled="!document.extractionOk"
              label="Include in answers"
              @update:model-value="toggleActive(document.id, $event)"
            />
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
        <h2 class="text-sm font-semibold text-text-secondary">Ask</h2>

        <SelectBox
          v-model="scopeDocumentId"
          label="Scope"
          :options="scopeOptions"
          placeholder="All active documents"
        />

        <TextArea
          v-model="question"
          placeholder="اسأل بالعربية أو English أو مزيج من اللغتين..."
          :rows="3"
          :max-length="2000"
        />

        <div class="flex justify-end">
          <BaseButton :icon="Send" :loading="knowledgeStore.isAsking" :disabled="!question.trim()" @click="handleAsk">
            Ask
          </BaseButton>
        </div>

        <p v-if="knowledgeStore.askError" class="text-sm text-danger-500">{{ knowledgeStore.askError }}</p>

        <EmptyState
          v-if="knowledgeStore.history.length === 0 && !knowledgeStore.isAsking"
          title="No questions asked yet"
          description="Ask a question about one of your uploaded documents, or all active documents at once."
        />

        <div v-else class="flex flex-col gap-4">
          <div v-for="entry in knowledgeStore.history" :key="entry.id" class="flex flex-col gap-2">
            <p class="self-end max-w-[85%] rounded-xl rounded-tr-sm bg-primary-500 px-4 py-2 text-sm text-white">
              {{ entry.question }}
            </p>
            <div class="max-w-[85%] rounded-xl rounded-tl-sm border border-border-light bg-bg-secondary px-4 py-3">
              <p class="whitespace-pre-wrap text-sm text-text-primary" dir="auto">{{ entry.answer }}</p>
              <div class="mt-2 flex flex-wrap items-center gap-1.5">
                <StatusBadge
                  v-for="sourceId in entry.sourceDocumentIds"
                  :key="sourceId"
                  :label="documentTitle(sourceId)"
                  variant="neutral"
                />
                <StatusBadge v-if="entry.cached" label="Cached" variant="info" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <KnowledgeUploadDialog v-model="isUploadDialogOpen" />
  </div>
</template>
