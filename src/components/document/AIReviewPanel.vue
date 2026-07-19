<script setup lang="ts">
import ErrorState from '@/components/common/ErrorState.vue'
import AILoadingState from '@/components/ai/AILoadingState.vue'
import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import OCRResultPanel from '@/components/document/OCRResultPanel.vue'
import type { DocumentAIReview } from '@/types/AiReview'

defineProps<{
  review: DocumentAIReview | undefined
  isLoading: boolean
  error?: string
}>()

const emit = defineEmits<{
  retry: []
  'suggestion-select': [suggestion: string]
}>()
</script>

<template>
  <ErrorState
    v-if="error"
    title="AI service is currently unavailable"
    :description="error"
    retry-label="Retry Analysis"
    @retry="emit('retry')"
  />

  <AILoadingState v-else-if="isLoading" />

  <div v-else-if="review" class="flex flex-col gap-6">
    <AIResponseCard :summary="review.summary" :details="review.details" :confidence="review.confidence" />
    <OCRResultPanel :fields="review.extractedFields" />
    <AISuggestionCard :suggestions="review.suggestions" @select="emit('suggestion-select', $event)" />
  </div>
</template>
