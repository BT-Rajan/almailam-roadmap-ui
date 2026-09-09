<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { WORKFLOW_STAGES, getWorkflowStageLabel, getWorkflowStageLabelKey, getWorkflowStageTabKey } from '@/utils/projectHelpers'

interface Props {
  currentStage: WorkflowStage
  // Design and/or Supervision only appear as steps when this project
  // actually includes that kind of work (see Project.includesDesign/
  // includesSupervision) -- every other stage is common to all projects.
  includesDesign: boolean
  includesSupervision: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const { t } = useI18n()

function stageLabel(stage: WorkflowStage): string {
  return t(getWorkflowStageLabelKey(stage) ?? getWorkflowStageLabel(stage))
}

// Every one of these stages jumps to the tab that covers it -- this
// stepper is the only place Quotation/Contract/Design/Supervision/
// Government Submission are reachable from (their own tab buttons were
// removed as exact duplicates of these same stage names). Requirement
// (formerly Enquiry, displayed as "Scope") jumps to the 'requirement'
// tab key, which renders the same ProjectOverviewTab as 'overview' does
// -- its scope-of-work editing (edit / save & proceed) lives directly on
// that tab's own Scope card. Government Submission is the terminal
// stage -- there is no further stage past it.
const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence, not
// in visibleStages -- Design/Supervision can drop in or out of
// visibleStages as a project's selected activities change, which would
// otherwise shift every later step's render-array position and desync
// it from currentStageRank, silently turning already-completed steps
// grey.
const currentStageRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))
const currentVisibleIndex = computed(() => visibleStages.value.indexOf(props.currentStage))

function stepStatus(stage: WorkflowStage): 'complete' | 'current' | 'upcoming' {
  const rank = WORKFLOW_STAGES.indexOf(stage)
  if (rank < currentStageRank.value) return 'complete'
  if (rank === currentStageRank.value) return 'current'
  return 'upcoming'
}

function handleSelect(stage: WorkflowStage): void {
  emit('navigate-tab', getWorkflowStageTabKey(stage))
}

// Completed = green, current = info (blue), upcoming = neutral border --
// same three-color convention as the wizard Stepper, just rendered as a
// segment instead of a circle so all six-to-seven stages fit on one
// slim row instead of a tall circle-and-label grid.
function segmentClasses(stage: WorkflowStage): string[] {
  const status = stepStatus(stage)
  return [
    'h-1.5 flex-1 rounded-full transition-colors duration-fast cursor-pointer hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500',
    status === 'complete' ? 'bg-success-500' : '',
    status === 'current' ? 'bg-info-500' : '',
    status === 'upcoming' ? 'bg-border-default' : '',
  ]
}

function labelClasses(stage: WorkflowStage): string[] {
  const status = stepStatus(stage)
  return [
    'flex-1 truncate text-center text-xs px-0.5 hover:text-accent-600 cursor-pointer',
    status === 'current' ? 'font-semibold text-info-600' : 'text-text-muted',
  ]
}
</script>

<template>
  <!-- No card wrapper of its own -- this renders directly beneath
       ProjectHeader.vue inside a single shared card (see
       ProjectWorkspacePage.vue), separated only by a hairline, instead
       of each being its own bordered box with a gap between them. -->
  <div class="border-t border-border-light p-3">
    <div class="mb-2 flex items-center justify-between gap-3">
      <p class="text-sm font-medium text-text-primary">
        {{
          t('project.workflowProgressStage', {
            current: currentVisibleIndex + 1,
            total: visibleStages.length,
            label: stageLabel(currentStage),
          })
        }}
      </p>
    </div>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[420px]">
        <div class="flex items-center gap-1" role="group" :aria-label="t('project.workflowProgress')">
          <button
            v-for="stage in visibleStages"
            :key="stage"
            type="button"
            :class="segmentClasses(stage)"
            :aria-label="t('common.goToStep', { step: visibleStages.indexOf(stage) + 1, label: stageLabel(stage) })"
            :aria-current="stepStatus(stage) === 'current' ? 'step' : undefined"
            @click="handleSelect(stage)"
          />
        </div>
        <div class="mt-1 flex items-start gap-1">
          <button v-for="stage in visibleStages" :key="stage" type="button" :class="labelClasses(stage)" @click="handleSelect(stage)">
            {{ stageLabel(stage) }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
