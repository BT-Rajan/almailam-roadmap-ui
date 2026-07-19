<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AIReviewPanel from '@/components/document/AIReviewPanel.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'

const route = useRoute()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

const documentId = computed(() => route.params.documentId as string)

function loadData(): void {
  documentStore.loadDocumentDetail(documentId.value)
  documentStore.loadDocumentReview(documentId.value)
}

onMounted(loadData)
watch(documentId, loadData)

function handleSuggestionSelect(suggestion: string): void {
  toastStore.show('info', 'Suggestion noted', suggestion)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      title="AI Document Review"
      :subtitle="documentStore.currentDocument ? documentStore.currentDocument.title : undefined"
    />

    <div v-if="documentStore.isDetailLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <EmptyState
      v-else-if="!documentStore.currentDocument"
      title="Document not found"
      description="This document may have been removed or the link is incorrect."
    />

    <AIReviewPanel
      v-else
      :review="documentStore.currentReview"
      :is-loading="documentStore.isReviewLoading"
      :error="documentStore.reviewError"
      @retry="loadData"
      @suggestion-select="handleSuggestionSelect"
    />
  </div>
</template>
