<script setup lang="ts">
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { AIConfidence } from '@/types/AiReview'
import type { BadgeVariant } from '@/types/Ui'

interface Props {
  confidence: AIConfidence
}

const props = defineProps<Props>()

const CONFIDENCE_VARIANTS: Record<AIConfidence, BadgeVariant> = {
  high: 'success',
  medium: 'warning',
  low: 'danger',
}

const CONFIDENCE_LABELS: Record<AIConfidence, string> = {
  high: 'High Confidence',
  medium: 'Medium Confidence',
  low: 'Low Confidence',
}
</script>

<template>
  <StatusBadge :label="CONFIDENCE_LABELS[props.confidence]" :variant="CONFIDENCE_VARIANTS[props.confidence]" show-dot />
</template>
