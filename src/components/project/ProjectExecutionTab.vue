<script setup lang="ts">
import { CheckCircle2, Circle, RotateCcw } from '@lucide/vue'
import { onMounted, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { useProjectExecutionStore } from '@/stores/projectExecutionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project } from '@/types/Project'

const props = defineProps<{
  project: Project
}>()

const store = useProjectExecutionStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

function loadData(): void {
  store.loadSteps(props.project.id)
}

onMounted(loadData)
// Switching between projects while this tab stays mounted (unlikely
// given how tabs are wired, but a project id changing under an already-
// open tab is exactly the kind of thing worth guarding rather than
// assuming can't happen) should reload rather than keep showing the
// previous project's checklist.
watch(() => props.project.id, loadData)

async function handleComplete(stepId: string): Promise<void> {
  await store.completeStep(props.project.id, stepId)
  if (store.mutationError) {
    toastStore.show('error', 'Could not complete step', store.mutationError)
    return
  }
  // The backend recomputes project.progress as part of completing a
  // step -- refresh just this one project so the progress shown
  // elsewhere on this page (header, overview card) picks up the new
  // number too, not just this tab's own checklist state.
  await projectStore.refreshProject(props.project.id)
}

async function handleUncomplete(stepId: string): Promise<void> {
  await store.uncompleteStep(props.project.id, stepId)
  if (store.mutationError) {
    toastStore.show('error', 'Could not undo step', store.mutationError)
    return
  }
  await projectStore.refreshProject(props.project.id)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <div v-else-if="store.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="8" />
    </div>

    <Card v-else>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-text-primary">Execution Checklist</h2>
          <span class="text-xs text-text-muted">{{ project.progress }}% complete</span>
        </div>
      </template>

      <p class="mb-4 text-xs text-text-muted">
        Steps are completed in order. Undoing is only possible for the most recently completed step.
      </p>

      <ol class="flex flex-col gap-2">
        <li
          v-for="step in store.steps"
          :key="step.id"
          class="flex items-center gap-3 rounded-lg border p-3"
          :class="step.status === 'Completed' ? 'border-success-200 bg-success-50' : 'border-border-light bg-bg-card'"
        >
          <CheckCircle2 v-if="step.status === 'Completed'" class="h-5 w-5 shrink-0 text-success-600" />
          <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" />

          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-text-primary">{{ step.name }}</p>
            <p class="text-xs text-text-muted">
              {{ step.weightPercentage }}%
              <span v-if="step.status === 'Completed' && step.completedByName">
                · Completed by {{ step.completedByName }}
              </span>
            </p>
          </div>

          <BaseButton
            v-if="step.id === store.nextActionableStepId"
            size="sm"
            @click="handleComplete(step.id)"
          >
            Mark Complete
          </BaseButton>
          <BaseButton
            v-else-if="step.id === store.lastCompletedStepId"
            size="sm"
            variant="ghost"
            :icon="RotateCcw"
            @click="handleUncomplete(step.id)"
          >
            Undo
          </BaseButton>
        </li>
      </ol>
    </Card>
  </div>
</template>
