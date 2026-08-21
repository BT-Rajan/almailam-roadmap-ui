<script setup lang="ts">
import { CheckCircle2, Circle, RotateCcw, XCircle } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import WaiveStepDialog from '@/components/project/WaiveStepDialog.vue'
import { PROCESS_STAGES } from '@/constants/processStages'
import { useProjectApprovalStore } from '@/stores/projectApprovalStore'
import { useProjectExecutionStore } from '@/stores/projectExecutionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectApprovalStep } from '@/types/ApprovalProcess'
import type { ProjectExecutionStep } from '@/types/ExecutionStep'
import type { Project } from '@/types/Project'

const props = defineProps<{
  project: Project
}>()

const executionStore = useProjectExecutionStore()
const approvalStore = useProjectApprovalStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

function loadData(): void {
  executionStore.loadSteps(props.project.id)
  approvalStore.loadSteps(props.project.id)
}

onMounted(loadData)
// A project id changing under an already-mounted tab (unlikely given
// how tabs are wired, but worth guarding rather than assuming can't
// happen) should reload rather than keep showing the previous
// project's checklists.
watch(() => props.project.id, loadData)

const isLoading = computed(() => executionStore.isLoading || approvalStore.isLoading)
const error = computed(() => executionStore.error ?? approvalStore.error)

// One unified process view -- the 5 Project Approval Process stages,
// each expanded to the execution steps that feed into it, instead of
// a separate Execution tab and a separate Approval Process modal that
// never talked to each other.
const stagesWithSteps = computed(() =>
  PROCESS_STAGES.map((stage) => ({
    stage,
    approvalStep: approvalStore.steps.find((s) => s.stageKey === stage.key),
    executionSteps: executionStore.steps
      .filter((s) => s.stageKey === stage.key)
      .sort((a, b) => a.sequenceNumber - b.sequenceNumber),
  })),
)

async function refreshProgress(): Promise<void> {
  // The backend recomputes project.progress as part of resolving an
  // execution step -- refresh just this one project so the progress
  // shown elsewhere on this page (header, overview card) picks up the
  // new number too, not just this tab's own checklist state.
  await projectStore.refreshProject(props.project.id)
}

async function handleCompleteExecution(stepId: string): Promise<void> {
  await executionStore.completeStep(props.project.id, stepId)
  if (executionStore.mutationError) {
    toastStore.show('error', 'Could not complete step', executionStore.mutationError)
    return
  }
  await refreshProgress()
}

async function handleUncompleteExecution(stepId: string): Promise<void> {
  await executionStore.uncompleteStep(props.project.id, stepId)
  if (executionStore.mutationError) {
    toastStore.show('error', 'Could not undo step', executionStore.mutationError)
    return
  }
  await refreshProgress()
}

async function handleCompleteApproval(stepId: string): Promise<void> {
  await approvalStore.completeStep(props.project.id, stepId)
  if (approvalStore.mutationError) {
    toastStore.show('error', 'Could not complete stage', approvalStore.mutationError)
  }
}

async function handleUncompleteApproval(stepId: string): Promise<void> {
  await approvalStore.uncompleteStep(props.project.id, stepId)
  if (approvalStore.mutationError) {
    toastStore.show('error', 'Could not undo stage', approvalStore.mutationError)
  }
}

async function handleUnwaiveExecution(stepId: string): Promise<void> {
  await executionStore.unwaiveStep(props.project.id, stepId)
  if (executionStore.mutationError) {
    toastStore.show('error', 'Could not undo waiver', executionStore.mutationError)
    return
  }
  await refreshProgress()
}

async function handleUnwaiveApproval(stepId: string): Promise<void> {
  await approvalStore.unwaiveStep(props.project.id, stepId)
  if (approvalStore.mutationError) {
    toastStore.show('error', 'Could not undo waiver', approvalStore.mutationError)
  }
}

// The waive dialog is shared between execution steps and approval
// stages -- only one of these two refs is set at a time, depending on
// which "Waive" button was clicked.
const waiveExecutionTarget = ref<ProjectExecutionStep | undefined>(undefined)
const waiveApprovalTarget = ref<ProjectApprovalStep | undefined>(undefined)
const isWaiveDialogOpen = ref(false)
const isWaiveSubmitting = ref(false)

function openWaiveExecution(step: ProjectExecutionStep): void {
  waiveExecutionTarget.value = step
  waiveApprovalTarget.value = undefined
  isWaiveDialogOpen.value = true
}

function openWaiveApproval(step: ProjectApprovalStep): void {
  waiveApprovalTarget.value = step
  waiveExecutionTarget.value = undefined
  isWaiveDialogOpen.value = true
}

const waiveDialogStepName = computed(() => waiveExecutionTarget.value?.name ?? waiveApprovalTarget.value?.name)

async function handleConfirmWaive(reason: string): Promise<void> {
  isWaiveSubmitting.value = true
  try {
    if (waiveExecutionTarget.value) {
      await executionStore.waiveStep(props.project.id, waiveExecutionTarget.value.id, reason)
      if (executionStore.mutationError) {
        toastStore.show('error', 'Could not waive step', executionStore.mutationError)
        return
      }
      await refreshProgress()
    } else if (waiveApprovalTarget.value) {
      await approvalStore.waiveStep(props.project.id, waiveApprovalTarget.value.id, reason)
      if (approvalStore.mutationError) {
        toastStore.show('error', 'Could not waive stage', approvalStore.mutationError)
        return
      }
    }
    isWaiveDialogOpen.value = false
  } finally {
    isWaiveSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ErrorState v-if="error" :description="error" @retry="loadData" />

    <div v-else-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="10" />
    </div>

    <template v-else>
      <p class="text-xs text-text-muted">
        The Project Approval Process (5 stages) and its execution checklist (23 steps). Steps are resolved in order;
        an optional step can be waived instead of completed when a client's requirements don't call for it.
      </p>

      <Card v-for="{ stage, approvalStep, executionSteps } in stagesWithSteps" :key="stage.key">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <CheckCircle2 v-if="approvalStep?.status === 'Completed'" class="h-5 w-5 shrink-0 text-success-600" />
              <XCircle v-else-if="approvalStep?.status === 'Waived'" class="h-5 w-5 shrink-0 text-text-muted" />
              <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" />
              <h2 class="text-sm font-semibold text-text-primary">{{ stage.label }}</h2>
            </div>

            <div v-if="approvalStep" class="flex items-center gap-2">
              <span v-if="approvalStep.status === 'Waived'" class="text-xs text-text-muted">
                Waived{{ approvalStep.waivedByName ? ` by ${approvalStep.waivedByName}` : '' }}
              </span>
              <span v-else-if="approvalStep.status === 'Completed' && approvalStep.completedByName" class="text-xs text-text-muted">
                Completed by {{ approvalStep.completedByName }}
              </span>

              <BaseButton
                v-if="approvalStep.id === approvalStore.nextActionableStepId"
                size="sm"
                @click="handleCompleteApproval(approvalStep.id)"
              >
                Mark Stage Complete
              </BaseButton>
              <BaseButton
                v-if="approvalStep.id === approvalStore.nextActionableStepId && approvalStep.isOptional"
                size="sm"
                variant="ghost"
                @click="openWaiveApproval(approvalStep)"
              >
                Waive
              </BaseButton>
              <BaseButton
                v-else-if="approvalStep.id === approvalStore.lastResolvedStepId && approvalStep.status === 'Completed'"
                size="sm"
                variant="ghost"
                :icon="RotateCcw"
                @click="handleUncompleteApproval(approvalStep.id)"
              >
                Undo
              </BaseButton>
              <BaseButton
                v-else-if="approvalStep.id === approvalStore.lastResolvedStepId && approvalStep.status === 'Waived'"
                size="sm"
                variant="ghost"
                :icon="RotateCcw"
                @click="handleUnwaiveApproval(approvalStep.id)"
              >
                Undo Waiver
              </BaseButton>
            </div>
          </div>
        </template>

        <p v-if="approvalStep?.status === 'Waived' && approvalStep.waivedReason" class="mb-3 text-xs text-text-muted">
          Reason: {{ approvalStep.waivedReason }}
        </p>

        <p v-if="executionSteps.length === 0" class="text-xs text-text-muted">
          No execution steps feed into this stage -- it's an external approval gate on its own.
        </p>

        <ol v-else class="flex flex-col gap-2">
          <li
            v-for="step in executionSteps"
            :key="step.id"
            class="flex items-center gap-3 rounded-lg border p-3"
            :class="{
              'border-success-200 bg-success-50': step.status === 'Completed',
              'border-border-light bg-bg-secondary': step.status === 'Waived',
              'border-border-light bg-bg-card': step.status === 'Pending',
            }"
          >
            <CheckCircle2 v-if="step.status === 'Completed'" class="h-5 w-5 shrink-0 text-success-600" />
            <XCircle v-else-if="step.status === 'Waived'" class="h-5 w-5 shrink-0 text-text-muted" />
            <Circle v-else class="h-5 w-5 shrink-0 text-text-muted" />

            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-text-primary">{{ step.name }}</p>
              <p class="text-xs text-text-muted">
                {{ step.weightPercentage }}%
                <span v-if="step.status === 'Completed' && step.completedByName"> · Completed by {{ step.completedByName }}</span>
                <span v-else-if="step.status === 'Waived'">
                  · Waived{{ step.waivedByName ? ` by ${step.waivedByName}` : '' }}{{ step.waivedReason ? `: ${step.waivedReason}` : '' }}
                </span>
              </p>
            </div>

            <BaseButton
              v-if="step.id === executionStore.nextActionableStepId"
              size="sm"
              @click="handleCompleteExecution(step.id)"
            >
              Mark Complete
            </BaseButton>
            <BaseButton
              v-if="step.id === executionStore.nextActionableStepId && step.isOptional"
              size="sm"
              variant="ghost"
              @click="openWaiveExecution(step)"
            >
              Waive
            </BaseButton>
            <BaseButton
              v-else-if="step.id === executionStore.lastResolvedStepId && step.status === 'Completed'"
              size="sm"
              variant="ghost"
              :icon="RotateCcw"
              @click="handleUncompleteExecution(step.id)"
            >
              Undo
            </BaseButton>
            <BaseButton
              v-else-if="step.id === executionStore.lastResolvedStepId && step.status === 'Waived'"
              size="sm"
              variant="ghost"
              :icon="RotateCcw"
              @click="handleUnwaiveExecution(step.id)"
            >
              Undo Waiver
            </BaseButton>
          </li>
        </ol>
      </Card>
    </template>

    <WaiveStepDialog
      v-model="isWaiveDialogOpen"
      :step-name="waiveDialogStepName"
      :is-submitting="isWaiveSubmitting"
      @confirm="handleConfirmWaive"
    />
  </div>
</template>
