<script setup lang="ts">
import { Download, FileText, CheckCircle2, Clock, RefreshCw } from '@lucide/vue'
import { computed } from 'vue'
import type { ProjectDeliverable } from '@/types/CustomerPortal'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'

interface Props {
  deliverables: ProjectDeliverable[]
}

const props = defineProps<Props>()

defineEmits<{
  download: [documentId: string]
}>()

const getStatusIcon = (status: string) => {
  if (status === 'delivered') return FileText
  if (status === 'approved') return CheckCircle2
  if (status === 'revision') return RefreshCw
  return Clock
}

const getStatusColor = (status: string) => {
  if (status === 'approved') return 'bg-success-50 border-success-200'
  if (status === 'delivered') return 'bg-info-50 border-info-200'
  if (status === 'revision') return 'bg-warning-50 border-warning-200'
  return 'bg-neutral-50 border-neutral-200'
}

const getStatusBadgeColor = (status: string) => {
  if (status === 'approved') return 'bg-success-100 text-success-700'
  if (status === 'delivered') return 'bg-info-100 text-info-700'
  if (status === 'revision') return 'bg-warning-100 text-warning-700'
  return 'bg-neutral-100 text-neutral-700'
}

// A "pending" deliverable is still a Draft internally -- nothing has
// been shared with the customer yet, so there's nothing real to
// download (the backend enforces this too, this just avoids offering a
// button that would only ever fail).
const isDownloadable = (status: string) => status !== 'pending'

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })

const completedCount = computed(() => props.deliverables.filter(d => d.status === 'approved').length)

const deliveryRate = computed(() =>
  props.deliverables.length > 0 ? Math.round((completedCount.value / props.deliverables.length) * 100) : 0
)
</script>

<template>
  <Card>
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-neutral-900">Deliverables</h2>
        <span class="text-sm font-medium text-neutral-600">
          {{ completedCount }}/{{ deliverables.length }} completed ({{ deliveryRate }}%)
        </span>
      </div>
    </template>

    <div v-if="deliverables.length === 0">
      <EmptyState :icon="FileText" title="No deliverables yet" description="Drawings, reports, and other deliverables will appear here as they're shared." />
    </div>

    <div v-else class="space-y-3">
      <!-- Progress Bar -->
      <div class="h-2 bg-neutral-200 rounded-full overflow-hidden">
        <div class="h-full bg-success-500 rounded-full" :style="{ width: `${deliveryRate}%` }" />
      </div>

      <!-- Deliverables List -->
      <div class="space-y-3">
        <div v-for="deliverable in deliverables" :key="deliverable.id" :class="['p-4 rounded-lg border', getStatusColor(deliverable.status)]">
          <div class="flex items-start gap-3">
            <component :is="getStatusIcon(deliverable.status)" class="h-5 w-5 text-neutral-400 flex-shrink-0 mt-0.5" />
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <h3 class="font-medium text-neutral-900">{{ deliverable.name }}</h3>
                  <p v-if="deliverable.description" class="text-sm text-neutral-600 mt-1">{{ deliverable.description }}</p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <span :class="['text-xs font-medium px-2.5 py-1 rounded-full', getStatusBadgeColor(deliverable.status)]">
                    {{ deliverable.status }}
                  </span>
                  <IconButton
                    v-if="isDownloadable(deliverable.status)"
                    :icon="Download"
                    label="Download document"
                    size="sm"
                    @click="$emit('download', deliverable.id)"
                  />
                </div>
              </div>

              <!-- Metadata -->
              <div class="flex flex-wrap gap-3 mt-3 text-xs text-neutral-600">
                <span>Type: <strong>{{ deliverable.type }}</strong></span>
                <span v-if="deliverable.deliveryDate">
                  Delivered: <strong>{{ formatDate(deliverable.deliveryDate) }}</strong>
                </span>
                <span v-if="deliverable.approvalDate" class="text-success-600">
                  Approved: <strong>{{ formatDate(deliverable.approvalDate) }}</strong>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
