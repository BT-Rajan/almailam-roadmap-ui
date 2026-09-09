<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Stepper from '@/components/common/Stepper.vue'
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
// stepper is now the only place Quotation/Contract/Design/Supervision/
// Government Submission are reachable from (their own tab buttons were
// removed as exact duplicates of these same stage names). Requirement
// (formerly Enquiry, displayed as "Scope") jumps to the 'requirement'
// tab key, which renders the same ProjectOverviewTab as 'overview' does
// -- its scope-of-work editing (edit / save & proceed) lives directly on
// that tab's own Scope card. Government Submission is the terminal
// stage -- there is no further stage past it.
// Requirement/Quotation/Contract/Government Submission are common to
// every project; Design and Supervision only show up as steps when this
// project actually includes that kind of work.
const visibleStages = computed<WorkflowStage[]>(() =>
  WORKFLOW_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Supervision') return props.includesSupervision
    return true
  }),
)

const steps = computed(() => visibleStages.value.map((stage) => ({ label: stageLabel(stage) })))

// Rank = position in the full, unfiltered WORKFLOW_STAGES sequence, not
// in visibleStages -- Design/Supervision can drop in or out of
// visibleStages as a project's selected activities change (see
// compute_stage_flags), which would otherwise shift every later
// step's render-array position and desync it from currentStepRank,
// making already-completed steps render as if nothing were done (see
// Stepper.vue's stepRanks prop).
const stepRanks = computed(() => visibleStages.value.map((stage) => WORKFLOW_STAGES.indexOf(stage)))

const currentStepRank = computed(() => WORKFLOW_STAGES.indexOf(props.currentStage))

// Every visible stage has a destination now (see STAGE_TABS above), so
// every step is navigable regardless of its complete/current/upcoming
// status.
const isStepNavigable = (): boolean => true

function handleSelect(index: number): void {
  const stage = visibleStages.value[index]
  if (stage) emit('navigate-tab', getWorkflowStageTabKey(stage))
}
</script>

<template>
  <!-- Slightly tighter than the New Project/New Client wizards' own Stepper
       wrapper (p-4 vs their p-6, mb-3 vs mb-6): this stepper sits stacked on
       top of the header, InfoPanel-free tab content, and the tab bar on
       every single project page load, not shown once per wizard -- the
       extra padding there earns its keep amortized over a whole flow; here
       it was just eating into the vertical space available for the actual
       tab content below it. -->
  <div class="rounded-xl border border-border-light bg-bg-card p-4">
    <h3 class="mb-3 text-sm font-semibold text-text-primary">{{ t('project.workflowProgress') }}</h3>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[720px]">
        <Stepper
          :steps="steps"
          :current-step="currentStepRank"
          :step-ranks="stepRanks"
          clickable
          :is-step-navigable="isStepNavigable"
          @select="handleSelect"
        />
      </div>
    </div>
  </div>
</template>
