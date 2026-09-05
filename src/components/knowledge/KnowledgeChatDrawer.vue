<script setup lang="ts">
import { AlertTriangle, ExternalLink, Send, Sparkles } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import type { SelectOption } from '@/types/Ui'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()

const question = ref('')
const scopeDocumentId = ref('')

const isDisabled = computed(() => knowledgeStore.isEnabled === false)

const scopeOptions = computed<SelectOption[]>(() => [
  { label: 'All active documents', value: '' },
  ...knowledgeStore.documents.map((document) => ({ label: document.title, value: document.id, disabled: !document.isActive })),
])

// Loads the document list (for the scope picker) the first time the
// drawer is actually opened, rather than on every app load -- most
// sessions never open it at all.
watch(
  () => knowledgeStore.isDrawerOpen,
  (isOpen) => {
    if (isOpen && knowledgeStore.documents.length === 0 && !knowledgeStore.isLoading) {
      void knowledgeStore.loadDocuments()
    }
  },
)

function documentTitle(documentId: string): string {
  return knowledgeStore.documents.find((document) => document.id === documentId)?.title ?? documentId
}

async function handleAsk(): Promise<void> {
  const trimmed = question.value.trim()
  if (!trimmed || isDisabled.value) return
  await knowledgeStore.ask(trimmed, scopeDocumentId.value || undefined)
  if (!knowledgeStore.askError) question.value = ''
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    void handleAsk()
  }
}

function openFullPage(): void {
  knowledgeStore.closeDrawer()
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_BASE })
}
</script>

<template>
  <BaseDrawer
    :model-value="knowledgeStore.isDrawerOpen"
    title="Knowledge Assistant"
    width="lg"
    @update:model-value="knowledgeStore.closeDrawer"
  >
    <div class="flex flex-col gap-5">
      <div class="flex items-center justify-between gap-3 rounded-lg border border-ai-100 bg-ai-50 px-3 py-2">
        <div class="flex items-center gap-2">
          <Sparkles class="h-4 w-4 text-ai-600" />
          <span class="text-xs font-medium text-text-secondary">Answers only from your uploaded documents</span>
        </div>
        <BaseButton variant="ghost" size="sm" :icon="ExternalLink" icon-position="right" @click="openFullPage">
          Manage documents
        </BaseButton>
      </div>

      <div
        v-if="isDisabled"
        class="flex items-start gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700"
      >
        <AlertTriangle class="h-4 w-4 shrink-0" />
        <span>The knowledgebase assistant is currently disabled. Ask an administrator to enable it in Knowledgebase AI.</span>
      </div>

      <div class="flex flex-col gap-3">
        <SelectBox
          v-model="scopeDocumentId"
          label="Scope"
          :options="scopeOptions"
          placeholder="All active documents"
          :disabled="isDisabled"
        />
        <TextArea
          v-model="question"
          placeholder="اسأل بالعربية أو English أو مزيج من اللغتين... (Ctrl+Enter to send)"
          :rows="3"
          :max-length="2000"
          :disabled="isDisabled"
          @keydown="handleKeydown"
        />
        <p v-if="knowledgeStore.askError" class="text-xs text-danger-500">{{ knowledgeStore.askError }}</p>
        <BaseButton
          :icon="Send"
          :loading="knowledgeStore.isAsking"
          :disabled="isDisabled || !question.trim()"
          full-width
          @click="handleAsk"
        >
          Ask
        </BaseButton>
      </div>

      <div class="flex flex-col gap-4">
        <EmptyState
          v-if="knowledgeStore.history.length === 0 && !knowledgeStore.isAsking"
          title="No questions asked yet"
          description="Ask a question about one of your uploaded documents, or all active documents at once."
        />

        <div v-for="entry in knowledgeStore.history" :key="entry.id" class="flex flex-col gap-2">
          <p class="self-end max-w-[85%] rounded-xl rounded-se-sm bg-primary-500 px-4 py-2 text-sm text-white">
            {{ entry.question }}
          </p>
          <div class="max-w-[85%] rounded-xl rounded-ss-sm border border-border-light bg-bg-secondary px-4 py-3">
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
  </BaseDrawer>
</template>
