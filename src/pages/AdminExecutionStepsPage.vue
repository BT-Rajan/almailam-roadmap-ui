<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import ExecutionStepEditor from '@/components/administration/ExecutionStepEditor.vue'
import { useExecutionStepSetStore } from '@/stores/executionStepSetStore'
import { useExecutionStepTemplateStore } from '@/stores/executionStepTemplateStore'
import { useToastStore } from '@/stores/toastStore'

const stepSetStore = useExecutionStepSetStore()
const store = useExecutionStepTemplateStore()
const toastStore = useToastStore()

onMounted(() => {
  if (stepSetStore.stepSets.length === 0) stepSetStore.loadStepSets()
})

// Whichever step set is selected in the picker drives which set of
// steps the editor below shows -- projects assigned to OTHER step sets
// are entirely unaffected by edits made here.
watch(
  () => stepSetStore.selectedStepSetId,
  (stepSetId) => {
    if (stepSetId) store.loadTemplate(stepSetId)
  },
  { immediate: true },
)

function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (store.mutationError) toastStore.show('error', 'Change not saved', store.mutationError)
    if (stepSetStore.mutationError) toastStore.show('error', 'Change not saved', stepSetStore.mutationError)
  })
}

function handleUpdate(
  stepId: string,
  fields: { name?: string; weightPercentage?: number; stageKey?: string; isOptional?: boolean; triggerKey?: string },
): void {
  reportIfFailed(store.updateStep(stepId, fields))
}

function handleRemove(stepId: string): void {
  reportIfFailed(store.deleteStep(stepId))
}

function handleMove(stepId: string, direction: 'up' | 'down'): void {
  reportIfFailed(store.moveStep(stepId, direction))
}

function handleAdd(name: string, weightPercentage: number, stageKey: string, isOptional: boolean, triggerKey: string): void {
  reportIfFailed(store.createStep(name, weightPercentage, stageKey, isOptional, triggerKey))
}

const weightIsExact = computed(() => Math.abs(store.totalWeight - 100) < 0.01)

const newSetName = ref('')

function submitNewSet(): void {
  if (newSetName.value.trim().length === 0) return
  reportIfFailed(stepSetStore.createStepSet(newSetName.value.trim(), null))
  newSetName.value = ''
}

function handleRemoveSet(stepSetId: string): void {
  reportIfFailed(stepSetStore.deleteStepSet(stepSetId))
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Process Step Sets"
      subtitle="Named, reusable execution checklists -- e.g. 'Standard Process', 'Commercial Fit-out'. Each project is assigned one set at creation and gets its own copy of exactly that set's steps, so editing a set here only affects projects created afterward. Staff can still add or exclude individual steps on top of whatever set a project was assigned."
    />

    <ErrorState v-if="stepSetStore.error" :description="stepSetStore.error" @retry="stepSetStore.loadStepSets" />

    <template v-else>
      <Card>
        <template #header>
          <h2 class="text-sm font-semibold text-text-primary">Step Sets</h2>
        </template>
        <div class="flex flex-col gap-3">
          <div v-if="stepSetStore.isLoading" class="flex gap-2">
            <SkeletonLoader :rows="1" />
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <div
              v-for="stepSet in stepSetStore.stepSets"
              :key="stepSet.id"
              class="flex items-center gap-1 rounded-full border px-1 py-1 pl-3 text-sm transition-colors"
              :class="
                stepSet.id === stepSetStore.selectedStepSetId
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-border-default bg-bg-card text-text-secondary hover:border-primary-300'
              "
            >
              <button type="button" class="font-medium" @click="stepSetStore.selectStepSet(stepSet.id)">
                {{ stepSet.name }}
              </button>
              <IconButton
                :icon="Trash2"
                label="Remove step set"
                size="sm"
                variant="danger"
                @click="handleRemoveSet(stepSet.id)"
              />
            </div>
          </div>

          <div class="flex items-center gap-2 border-t border-border-light pt-3">
            <TextInput v-model="newSetName" placeholder="New step set name" class="max-w-xs flex-1" />
            <BaseButton :icon="Plus" variant="secondary" :disabled="newSetName.trim().length === 0" @click="submitNewSet">
              Add Step Set
            </BaseButton>
          </div>
        </div>
      </Card>

      <ErrorState v-if="store.error" :description="store.error" @retry="() => stepSetStore.selectedStepSetId && store.loadTemplate(stepSetStore.selectedStepSetId)" />

      <div v-else-if="store.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="8" />
      </div>

      <template v-else-if="stepSetStore.selectedStepSetId">
        <Alert
          v-if="!weightIsExact"
          variant="warning"
          title="Weights don't add up to 100%"
          :description="`Current total: ${store.totalWeight}%. A project on this step set can't reach exactly 100% complete until every step's weight sums to 100.`"
        />
        <Alert
          v-else
          variant="success"
          title="Weights sum to exactly 100%"
          description="A project on this step set with every step completed will show exactly 100% progress."
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
    </template>
  </div>
</template>
