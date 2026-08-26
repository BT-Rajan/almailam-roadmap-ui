<script setup lang="ts">
import { CheckCircle2, Circle } from '@lucide/vue'
import { computed, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project } from '@/types/Project'
import type { ProjectExecutionStep } from '@/types/ExecutionStep'

const props = defineProps<{
  project: Project
  // The full 23-item process checklist, already loaded by the parent
  // (ProjectProcessTab.vue via projectStageStore) -- reused here rather
  // than fetched again, since it's the same list, just filtered/
  // presented differently for the "additional services" flow.
  executionSteps: ProjectExecutionStep[]
}>()

const emit = defineEmits<{
  refresh: []
}>()

const projectStore = useProjectStore()
const toastStore = useToastStore()

// Flattened, uniform view of every quoted scope line regardless of
// which of the two backend tables it actually lives in -- the
// checklist itself doesn't need to care that a service activity and a
// type activity are stored separately, only that each is one
// deliverable with a name, a completion state, and a way to toggle it.
interface ScopeLine {
  source: 'service' | 'type_activity'
  itemId: string
  name: string
  detail: string
  isComplete: boolean
}

const scopeLines = computed<ScopeLine[]>(() => [
  ...(props.project.selectedActivities ?? []).map((item) => ({
    source: 'service' as const,
    itemId: item.activityId,
    name: item.activityName,
    detail: item.serviceName,
    isComplete: item.isComplete ?? false,
  })),
  ...(props.project.selectedTypeActivities ?? []).map((item) => ({
    source: 'type_activity' as const,
    itemId: item.id,
    name: item.activityName,
    detail: props.project.typeCategoryName ?? 'Type Activity',
    isComplete: item.isComplete ?? false,
  })),
])

const completedCount = computed(() => scopeLines.value.filter((line) => line.isComplete).length)
const isTogglingScope = ref<string | undefined>(undefined)

async function toggleScopeLine(line: ScopeLine): Promise<void> {
  const key = `${line.source}:${line.itemId}`
  isTogglingScope.value = key
  try {
    await projectStore.setScopeItemComplete(props.project.id, line.source, line.itemId, !line.isComplete)
    emit('refresh')
  } catch (error) {
    toastStore.show('error', 'Could not update scope item', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isTogglingScope.value = undefined
  }
}

// "Were any additional services rendered?" -- '' until answered, same
// not-yet-answered convention as the New Project wizard's permits
// question. Answering 'yes' reveals the full 23-item checklist so
// staff can check off work delivered beyond the original quoted scope;
// answering 'no' (or leaving it unanswered) keeps this panel scoped to
// just the Scope Execution list above.
const additionalServicesRendered = ref<'yes' | 'no' | ''>('')

// Only items not already complete are offered here -- something
// already at 100% isn't "additional", it's already accounted for
// (whether that's an original scope item that happens to share a name
// with a checklist entry, or a previously-recorded additional one).
const availableAdditionalSteps = computed(() => props.executionSteps.filter((step) => step.completionPercentage < 100))

// The contract-coverage question is asked once a step is checked, not
// before -- pendingCoverageStep holds which one, so the yes/no prompt
// renders inline right under that specific row rather than as a
// separate modal interrupting the flow.
const pendingCoverageStep = ref<ProjectExecutionStep | undefined>(undefined)
const isMarkingAdditional = ref(false)

function requestMarkAdditional(step: ProjectExecutionStep): void {
  pendingCoverageStep.value = step
}

function cancelCoveragePrompt(): void {
  pendingCoverageStep.value = undefined
}

async function confirmCoverage(contractCovered: boolean): Promise<void> {
  const step = pendingCoverageStep.value
  if (!step) return
  isMarkingAdditional.value = true
  try {
    await projectStore.markAdditionalExecutionStep(props.project.id, step.id, contractCovered)
    pendingCoverageStep.value = undefined
    emit('refresh')
  } catch (error) {
    toastStore.show('error', 'Could not record additional service', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isMarkingAdditional.value = false
  }
}
</script>

<template>
  <Card>
    <template #header>
      <div>
        <h2 class="text-sm font-semibold text-text-primary">Scope Execution</h2>
        <p class="text-xs text-text-muted">
          The services and type activities this project was actually quoted for -- {{ completedCount }} of
          {{ scopeLines.length }} delivered.
        </p>
      </div>
    </template>

    <div class="flex flex-col gap-4">
      <p v-if="scopeLines.length === 0" class="text-sm text-text-muted">
        This project has no recorded scope items (services or type activities) to track.
      </p>

      <ol v-else class="flex flex-col divide-y divide-border-light">
        <li v-for="line in scopeLines" :key="`${line.source}:${line.itemId}`" class="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
          <Checkbox
            :model-value="line.isComplete"
            :disabled="isTogglingScope === `${line.source}:${line.itemId}`"
            :label="line.name"
            :hint="line.detail"
            @update:model-value="toggleScopeLine(line)"
          />
        </li>
      </ol>

      <div class="border-t border-border-light pt-4">
        <RadioGroup
          v-model="additionalServicesRendered"
          label="Were any additional services rendered beyond this scope?"
          :options="[
            { label: 'Yes', value: 'yes' },
            { label: 'No', value: 'no' },
          ]"
          :vertical="false"
        />
      </div>

      <div v-if="additionalServicesRendered === 'yes'" class="flex flex-col gap-3 rounded-lg border border-border-light p-3">
        <p class="text-xs text-text-muted">
          Check off anything delivered beyond the original scope. Each new item asks whether it's covered under the
          existing contract before it counts as done.
        </p>
        <p v-if="availableAdditionalSteps.length === 0" class="text-sm text-text-muted">
          Every process-checklist activity is already complete -- nothing left to add here.
        </p>
        <ol v-else class="flex flex-col divide-y divide-border-light">
          <li v-for="step in availableAdditionalSteps" :key="step.id" class="flex flex-col gap-2 py-2.5 first:pt-0 last:pb-0">
            <Checkbox
              :model-value="false"
              :disabled="isMarkingAdditional"
              :label="step.name"
              @update:model-value="requestMarkAdditional(step)"
            />
            <div v-if="pendingCoverageStep?.id === step.id" class="ml-7 flex items-center gap-3 rounded-lg bg-bg-hover p-3">
              <span class="text-sm text-text-secondary">Is this covered under the contract?</span>
              <div class="flex gap-2">
                <BaseButton size="sm" :loading="isMarkingAdditional" @click="confirmCoverage(true)">Yes</BaseButton>
                <BaseButton size="sm" variant="secondary" :loading="isMarkingAdditional" @click="confirmCoverage(false)">No</BaseButton>
                <BaseButton size="sm" variant="ghost" :disabled="isMarkingAdditional" @click="cancelCoveragePrompt">Cancel</BaseButton>
              </div>
            </div>
          </li>
        </ol>
      </div>

      <div v-if="scopeLines.length > 0" class="flex items-center gap-2 rounded-lg bg-bg-hover p-3 text-sm">
        <CheckCircle2 v-if="completedCount === scopeLines.length" class="h-4 w-4 shrink-0 text-success-600" aria-hidden="true" />
        <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
        <span class="text-text-secondary">
          {{
            completedCount === scopeLines.length
              ? 'All scope items delivered -- the project can move to Completed once every other requirement is met.'
              : `${scopeLines.length - completedCount} scope item(s) still not delivered -- the project can't move to Completed yet.`
          }}
        </span>
      </div>
    </div>
  </Card>
</template>
