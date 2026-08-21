<script setup lang="ts">
import { MessageSquare } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectCompletionStore } from '@/stores/projectCompletionStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const router = useRouter()
const completionStore = useProjectCompletionStore()
const toastStore = useToastStore()

function loadSummary(): void {
  completionStore.loadSummary(props.project.id)
}

onMounted(loadSummary)
watch(() => props.project.id, loadSummary)

const summary = computed(() => completionStore.summary)

const budgetVariance = computed(() => {
  if (!summary.value || summary.value.plannedBudget === null || summary.value.actualBudget === null) return null
  return summary.value.actualBudget - summary.value.plannedBudget
})

const durationVarianceDays = computed(() => {
  if (!summary.value || summary.value.actualDurationDays === null) return null
  return summary.value.actualDurationDays - summary.value.plannedDurationDays
})

const notesDraft = ref('')
watch(
  () => summary.value?.notes,
  (notes) => {
    notesDraft.value = notes ?? ''
  },
  { immediate: true },
)
const notesDirty = computed(() => notesDraft.value !== (summary.value?.notes ?? ''))

async function saveNotes(): Promise<void> {
  await completionStore.saveNotes(props.project.id, notesDraft.value)
  if (completionStore.saveError) {
    toastStore.show('error', 'Could not save notes', completionStore.saveError)
    return
  }
  toastStore.show('success', 'Notes saved', 'Project notes were updated.')
}

const projectDetailItems = computed(() => [
  { label: 'Service', value: props.project.service },
  { label: 'Responsible Engineer', value: props.project.engineer },
  { label: 'Start Date', value: formatDate(props.project.startDate) },
  { label: 'Target Completion Date', value: formatDate(props.project.targetDate) },
  { label: 'Current Stage', value: props.project.currentStage },
  { label: 'Priority', value: props.project.priority },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: 'Company Name', value: props.client.companyName },
    { label: 'Contact Person', value: props.client.contactPerson },
    { label: 'Mobile', value: props.client.mobile },
    { label: 'Email', value: props.client.email },
    { label: 'City', value: props.client.city },
  ]
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <Card v-if="project.description">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Scope of Work</h3>
      </template>
      <p class="whitespace-pre-wrap text-sm text-text-secondary">{{ project.description }}</p>
    </Card>

    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel title="Project Details" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel title="Client Details" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            Message Client
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            View Full Profile
          </BaseButton>
        </div>
      </div>
    </div>

    <Card>
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Project Summary</h3>
      </template>

      <ErrorState v-if="completionStore.error" :description="completionStore.error" @retry="loadSummary" />

      <SkeletonLoader v-else-if="completionStore.isLoading" :rows="5" />

      <div v-else-if="summary" class="flex flex-col gap-6">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">Planned Budget</p>
            <p class="text-sm font-semibold text-text-primary">
              {{ summary.plannedBudget !== null ? formatCurrency(summary.plannedBudget) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Received Budget</p>
            <p class="text-sm font-semibold text-text-primary">
              {{ summary.actualBudget !== null ? formatCurrency(summary.actualBudget) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Variance</p>
            <p
              class="text-sm font-semibold"
              :class="budgetVariance === null ? 'text-text-primary' : budgetVariance < 0 ? 'text-danger-600' : 'text-success-600'"
            >
              {{ budgetVariance !== null ? formatCurrency(budgetVariance) : '—' }}
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">Planned Duration</p>
            <p class="text-sm font-semibold text-text-primary">{{ summary.plannedDurationDays }} days</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Actual Duration</p>
            <p class="text-sm font-semibold text-text-primary">
              {{ summary.actualDurationDays !== null ? `${summary.actualDurationDays} days` : 'In progress' }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Variance</p>
            <p
              class="text-sm font-semibold"
              :class="durationVarianceDays === null ? 'text-text-primary' : durationVarianceDays > 0 ? 'text-danger-600' : 'text-success-600'"
            >
              {{ durationVarianceDays !== null ? `${durationVarianceDays > 0 ? '+' : ''}${durationVarianceDays} days` : '—' }}
            </p>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <TextArea v-model="notesDraft" label="Key Project Notes" placeholder="Handover notes, lessons learned, anything worth remembering..." :rows="4" />
          <div class="flex justify-end no-print">
            <BaseButton size="sm" :disabled="!notesDirty" :loading="completionStore.isSaving" @click="saveNotes">
              Save Notes
            </BaseButton>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
