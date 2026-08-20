<script setup lang="ts">
import { AlertTriangle, CheckCircle2 } from '@lucide/vue'
import { computed, onMounted } from 'vue'

import Alert from '@/components/common/Alert.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ExecutionStepEditor from '@/components/administration/ExecutionStepEditor.vue'
import { useExecutionStepTemplateStore } from '@/stores/executionStepTemplateStore'
import { useToastStore } from '@/stores/toastStore'

const store = useExecutionStepTemplateStore()
const toastStore = useToastStore()

function loadData(): void {
  store.loadTemplate()
}

onMounted(() => {
  if (store.steps.length === 0) loadData()
})

// Edits save immediately as they're made (see the store), so the only
// feedback needed here is a toast if a particular edit failed --
// matches AdminWorkflowsPage.vue's own convention exactly.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (store.mutationError) {
      toastStore.show('error', 'Change not saved', store.mutationError)
    }
  })
}

function handleUpdate(stepId: string, fields: { name?: string; weightPercentage?: number }): void {
  reportIfFailed(store.updateStep(stepId, fields))
}

function handleRemove(stepId: string): void {
  reportIfFailed(store.deleteStep(stepId))
}

function handleMove(stepId: string, direction: 'up' | 'down'): void {
  reportIfFailed(store.moveStep(stepId, direction))
}

function handleAdd(name: string, weightPercentage: number): void {
  reportIfFailed(store.createStep(name, weightPercentage))
}

const weightIsExact = computed(() => Math.abs(store.totalWeight - 100) < 0.01)
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Execution Steps"
      subtitle="The linear, tangible-act checklist every project follows. Each project gets its own copy of this list the moment it's created -- editing it here only affects projects created afterward."
    />

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <div v-else-if="store.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="8" />
    </div>

    <template v-else>
      <Alert
        v-if="!weightIsExact"
        variant="warning"
        title="Weights don't add up to 100%"
        :description="`Current total: ${store.totalWeight}%. A project can't reach exactly 100% complete until every step's weight sums to 100.`"
      />
      <Alert
        v-else
        variant="success"
        title="Weights sum to exactly 100%"
        description="A project with every step completed will show exactly 100% progress."
      />

      <Card>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-text-primary">Steps</h2>
            <span class="flex items-center gap-1.5 text-xs" :class="weightIsExact ? 'text-success-600' : 'text-warning-600'">
              <component :is="weightIsExact ? CheckCircle2 : AlertTriangle" class="h-3.5 w-3.5" />
              Total weight: {{ store.totalWeight }}%
            </span>
          </div>
        </template>
        <ExecutionStepEditor :steps="store.steps" @update="handleUpdate" @remove="handleRemove" @move="handleMove" @add="handleAdd" />
      </Card>
    </template>
  </div>
</template>
