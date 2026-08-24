<script setup lang="ts">
import { CheckCircle2, Circle, Printer } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'
import { useProjectCompletionStore } from '@/stores/projectCompletionStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import type { ProjectCompletionChecklist } from '@/types/ProjectCompletion'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const completionStore = useProjectCompletionStore()

const project = ref<Project | undefined>()
const client = ref<Client | undefined>()
const isLoading = ref(true)
const loadError = ref('')

const projectId = route.params.projectId as string

async function loadData(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const fetchedProject = await projectService.getProjectById(projectId)
    if (!fetchedProject) {
      loadError.value = 'Project not found.'
      return
    }
    project.value = fetchedProject
    const [fetchedClient] = await Promise.all([
      clientService.getClientById(fetchedProject.clientId),
      completionStore.loadSummary(projectId),
    ])
    client.value = fetchedClient
    if (completionStore.error) loadError.value = completionStore.error
  } catch {
    loadError.value = 'Unable to load the project summary report. Please try again.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

const summary = computed(() => completionStore.summary)
const checklist = computed(() => completionStore.checklist)

const CHECKLIST_ITEMS: { key: keyof ProjectCompletionChecklist; label: string }[] = [
  { key: 'contract', label: 'Contract' },
  { key: 'payments', label: 'Payments' },
  { key: 'design', label: 'Design Approval' },
  { key: 'governmentApproval', label: 'Government Approval' },
  { key: 'fieldWork', label: 'Field Work' },
]

function handlePrint(): void {
  window.print()
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-6 tablet:px-6 tablet:py-8">
    <div class="no-print mb-6 flex items-center justify-between">
      <h1 class="text-lg font-semibold text-text-primary">Project Summary Report</h1>
      <BaseButton :icon="Printer" :disabled="isLoading || !!loadError" @click="handlePrint">Print / Save as PDF</BaseButton>
    </div>

    <ErrorState v-if="loadError" :description="loadError" @retry="loadData" />

    <div v-else-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="10" />
    </div>

    <div v-else-if="project && summary" id="summary-report-print-area" class="flex flex-col gap-6">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <p class="text-xs uppercase tracking-wide text-text-muted">Project Summary Report</p>
        <h2 class="mt-1 text-2xl font-semibold text-text-primary">{{ project.projectName }}</h2>
        <p class="mt-1 text-sm text-text-secondary">{{ project.id }} · {{ project.service }}</p>

        <div class="mt-4 grid grid-cols-2 gap-4 tablet:grid-cols-4">
          <div>
            <p class="text-xs text-text-muted">Client</p>
            <p class="text-sm font-medium text-text-primary">{{ client?.companyName ?? '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Status</p>
            <p class="text-sm font-medium text-text-primary">{{ project.status }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Start Date</p>
            <p class="text-sm font-medium text-text-primary">{{ formatDate(project.startDate) }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">{{ summary.completedAt ? 'Completed On' : 'Target Date' }}</p>
            <p class="text-sm font-medium text-text-primary">
              {{ formatDate(summary.completedAt ?? project.targetDate) }}
            </p>
          </div>
        </div>
      </div>

      <div v-if="checklist" class="rounded-xl border border-border-light bg-bg-card p-6">
        <h3 class="mb-3 text-sm font-semibold text-text-primary">Completion Checklist</h3>
        <ul class="flex flex-col gap-2">
          <li
            v-for="item in CHECKLIST_ITEMS"
            :key="item.key"
            class="flex items-center gap-2.5 rounded-lg border p-2.5"
            :class="checklist[item.key].complete ? 'border-success-200 bg-success-50' : 'border-border-light bg-bg-card'"
          >
            <CheckCircle2 v-if="checklist[item.key].complete" class="h-4 w-4 shrink-0 text-success-600" />
            <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-text-primary">{{ item.label }}</p>
              <p class="text-xs text-text-muted">{{ checklist[item.key].detail }}</p>
            </div>
          </li>
        </ul>
      </div>

      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <h3 class="mb-3 text-sm font-semibold text-text-primary">Budget & Duration</h3>
        <div class="grid grid-cols-2 gap-4 tablet:grid-cols-4">
          <div>
            <p class="text-xs text-text-muted">Planned Budget</p>
            <p class="text-sm font-medium text-text-primary">
              {{ summary.plannedBudget !== null ? formatCurrency(summary.plannedBudget) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Actual Budget</p>
            <p class="text-sm font-medium text-text-primary">
              {{ summary.actualBudget !== null ? formatCurrency(summary.actualBudget) : '—' }}
            </p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Planned Duration</p>
            <p class="text-sm font-medium text-text-primary">{{ summary.plannedDurationDays }} days</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Actual Duration</p>
            <p class="text-sm font-medium text-text-primary">
              {{ summary.actualDurationDays !== null ? `${summary.actualDurationDays} days` : 'In progress' }}
            </p>
          </div>
        </div>
      </div>

      <div v-if="summary.scopeDeviations.length > 0" class="rounded-xl border border-border-light bg-bg-card p-6">
        <h3 class="mb-3 text-sm font-semibold text-text-primary">Scope Deviations</h3>
        <ul class="flex flex-col gap-2">
          <li v-for="deviation in summary.scopeDeviations" :key="deviation.revision" class="text-sm text-text-secondary">
            <span class="font-medium text-text-primary">{{ deviation.revision }}</span>
            ({{ formatDate(deviation.date) }}, {{ deviation.changedBy }}) — {{ deviation.summary }}
          </li>
        </ul>
        <p v-if="summary.deviationNotes" class="mt-3 whitespace-pre-wrap text-sm text-text-secondary">
          {{ summary.deviationNotes }}
        </p>
      </div>

      <div v-if="summary.notes" class="rounded-xl border border-border-light bg-bg-card p-6">
        <h3 class="mb-3 text-sm font-semibold text-text-primary">Notes</h3>
        <p class="whitespace-pre-wrap text-sm text-text-secondary">{{ summary.notes }}</p>
      </div>
    </div>
  </div>
</template>
