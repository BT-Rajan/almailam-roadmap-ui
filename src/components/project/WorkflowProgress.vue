<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ProjectWorkspaceTabKey, SelectedPermit, SelectedSupervisionActivity, WorkflowStage } from '@/types/Project'
import type { SelectedServiceActivity } from '@/types/ServiceCatalog'
import { getWorkflowStageLabel, getWorkflowStageLabelKey, getWorkflowStageTabKey } from '@/utils/projectHelpers'

// Design, Government Submission (Permits), and Supervision are three
// independent PARALLEL tracks, not three stops on a line -- Contract
// feeds all three at once (whichever this project actually includes),
// and all three feed into Handover. Drawn as one branching band between
// the Contract and Handover segments: Permit on top, Design in the
// middle, Supervision below -- rather than three separate segments in
// the linear row the other stages get. Only rows for tracks this
// project actually includes render, so the band is 1-3 rows tall.
interface Props {
  currentStage: WorkflowStage
  includesDesign: boolean
  includesGovernmentSubmission: boolean
  includesSupervision: boolean
  // The three tracks' own selected items -- needed here (not just the
  // includes* flags) so each track's segment can show real progress
  // (every item Complete/Cancelled) independently of currentStage,
  // which only ever points at one of the three at a time and stays
  // there until every included track converges on Handover -- without
  // this, the other two tracks' segments would read as permanently
  // "upcoming" even once staff have actually finished them.
  selectedActivities?: SelectedServiceActivity[]
  selectedPermits?: SelectedPermit[]
  selectedSupervisionActivities?: SelectedSupervisionActivity[]
}

const props = withDefaults(defineProps<Props>(), {
  selectedActivities: () => [],
  selectedPermits: () => [],
  selectedSupervisionActivities: () => [],
})

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const { t } = useI18n()

function stageLabel(stage: WorkflowStage): string {
  return t(getWorkflowStageLabelKey(stage) ?? getWorkflowStageLabel(stage))
}

// The four genuinely-sequential stages before the parallel band, in
// order -- unaffected by which of Design/Government Submission/
// Supervision this project includes.
const LINEAR_STAGES: WorkflowStage[] = ['Requirement', 'Quotation', 'Payment Plan', 'Contract']

// Fixed display order for the parallel band -- Permit (top), Design
// (middle), Supervision (bottom), same order regardless of which
// subset this project actually includes.
const PARALLEL_STAGES: WorkflowStage[] = ['Government Submission', 'Design', 'Supervision']

const visibleParallelStages = computed<WorkflowStage[]>(() =>
  PARALLEL_STAGES.filter((stage) => {
    if (stage === 'Design') return props.includesDesign
    if (stage === 'Government Submission') return props.includesGovernmentSubmission
    return props.includesSupervision
  }),
)
const hasParallelBand = computed(() => visibleParallelStages.value.length > 0)

// Once the project has moved into the parallel band or Handover,
// props.currentStage is no longer one of LINEAR_STAGES at all, so a
// plain LINEAR_STAGES.indexOf lookup returns -1 -- with the comparisons
// below, that read every linear stage (including Contract) as "upcoming"
// again instead of "complete" the moment the project left Contract,
// turning their segments from green back to grey. Treat "past all four
// linear stages" as its own rank (LINEAR_STAGES.length) so every one of
// them still compares as strictly less than it and stays complete.
const currentStageRank = computed(() => {
  if (PARALLEL_STAGES.includes(props.currentStage) || props.currentStage === 'Handover') {
    return LINEAR_STAGES.length
  }
  return LINEAR_STAGES.indexOf(props.currentStage)
})

function linearStepStatus(stage: WorkflowStage): 'complete' | 'current' | 'upcoming' {
  const rank = LINEAR_STAGES.indexOf(stage)
  if (rank < currentStageRank.value) return 'complete'
  if (rank === currentStageRank.value) return 'current'
  return 'upcoming'
}

// True once the project has actually left Contract -- the point at
// which every included parallel track becomes simultaneously workable
// (staff can act on any of them regardless of which one currentStage
// happens to be sitting on, same as the top tab bar already lets them).
const isPastContract = computed(
  () => PARALLEL_STAGES.includes(props.currentStage) || props.currentStage === 'Handover',
)

function isTrackDone(stage: WorkflowStage): boolean {
  if (stage === 'Design') {
    return props.selectedActivities.length > 0 && props.selectedActivities.every((a) => a.status === 'Complete' || a.status === 'Cancelled')
  }
  if (stage === 'Government Submission') {
    return props.selectedPermits.length > 0 && props.selectedPermits.every((p) => p.status === 'Complete' || p.status === 'Cancelled')
  }
  return (
    props.selectedSupervisionActivities.length > 0 &&
    props.selectedSupervisionActivities.every((a) => a.status === 'Complete' || a.status === 'Cancelled')
  )
}

function parallelStepStatus(stage: WorkflowStage): 'complete' | 'current' | 'upcoming' {
  if (isTrackDone(stage)) return 'complete'
  if (isPastContract.value) return 'current'
  return 'upcoming'
}

function handoverStepStatus(): 'complete' | 'current' | 'upcoming' {
  if (props.currentStage === 'Handover') return 'current'
  return 'upcoming'
}

function handleSelect(stage: WorkflowStage): void {
  emit('navigate-tab', getWorkflowStageTabKey(stage))
}

// Completed = green, current = info (blue), upcoming = neutral border --
// same three-color convention as the wizard Stepper.
function segmentClasses(status: 'complete' | 'current' | 'upcoming'): string[] {
  return [
    'h-1.5 flex-1 rounded-full transition-colors duration-fast cursor-pointer hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500',
    status === 'complete' ? 'bg-success-500' : '',
    status === 'current' ? 'bg-info-500' : '',
    status === 'upcoming' ? 'bg-border-default' : '',
  ]
}

// Fixed-width tick instead of flex-1 -- these sit beside a label in a
// horizontal row (unlike the linear segments, which stack full-width
// above their label), so a growing bar would fight the label for space.
function parallelSegmentClasses(status: 'complete' | 'current' | 'upcoming'): string[] {
  return [
    'h-1.5 w-6 shrink-0 rounded-full transition-colors duration-fast cursor-pointer hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500',
    status === 'complete' ? 'bg-success-500' : '',
    status === 'current' ? 'bg-info-500' : '',
    status === 'upcoming' ? 'bg-border-default' : '',
  ]
}

function labelClasses(status: 'complete' | 'current' | 'upcoming'): string[] {
  return [
    'truncate text-xs hover:text-accent-600 cursor-pointer',
    status === 'current' ? 'font-semibold text-info-600' : 'text-text-muted',
  ]
}

// "Stage N of M" summary -- the parallel band counts as exactly one
// step regardless of how many of the three tracks it actually holds
// (they're parallel, not a sub-sequence to count through), so the total
// is the 4 linear stages, +1 for the band (only when this project
// includes any of the three), +1 for Handover.
const totalSteps = computed(() => LINEAR_STAGES.length + (hasParallelBand.value ? 1 : 0) + 1)
const currentStepIndex = computed(() => {
  if (PARALLEL_STAGES.includes(props.currentStage)) return LINEAR_STAGES.length + 1
  if (props.currentStage === 'Handover') return totalSteps.value
  return LINEAR_STAGES.indexOf(props.currentStage) + 1
})
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
            current: currentStepIndex,
            total: totalSteps,
            label: stageLabel(currentStage),
          })
        }}
      </p>
    </div>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[520px]">
        <div class="flex items-stretch gap-2" role="group" :aria-label="t('project.workflowProgress')">
          <!-- The four linear stages -->
          <button
            v-for="stage in LINEAR_STAGES"
            :key="stage"
            type="button"
            class="flex flex-1 flex-col items-stretch gap-1"
            :aria-label="t('common.goToStep', { step: LINEAR_STAGES.indexOf(stage) + 1, label: stageLabel(stage) })"
            :aria-current="linearStepStatus(stage) === 'current' ? 'step' : undefined"
            @click="handleSelect(stage)"
          >
            <span :class="segmentClasses(linearStepStatus(stage))" />
            <span :class="[...labelClasses(linearStepStatus(stage)), 'text-center']">{{ stageLabel(stage) }}</span>
          </button>

          <!-- Parallel band: Permit (top), Design (middle), Supervision
               (bottom) -- only the rows this project actually includes. -->
          <div v-if="hasParallelBand" class="flex min-w-0 flex-1 flex-col justify-center gap-1.5">
            <button
              v-for="stage in visibleParallelStages"
              :key="stage"
              type="button"
              class="flex min-w-0 items-center gap-1.5"
              :aria-label="t('common.goToStep', { step: LINEAR_STAGES.length + 1, label: stageLabel(stage) })"
              :aria-current="parallelStepStatus(stage) === 'current' ? 'step' : undefined"
              @click="handleSelect(stage)"
            >
              <span :class="parallelSegmentClasses(parallelStepStatus(stage))" />
              <span :class="[...labelClasses(parallelStepStatus(stage)), 'min-w-0 flex-1 text-start']">{{ stageLabel(stage) }}</span>
            </button>
          </div>

          <!-- Handover -->
          <button
            type="button"
            class="flex flex-1 flex-col items-stretch gap-1"
            :aria-label="t('common.goToStep', { step: totalSteps, label: stageLabel('Handover') })"
            :aria-current="handoverStepStatus() === 'current' ? 'step' : undefined"
            @click="handleSelect('Handover')"
          >
            <span :class="segmentClasses(handoverStepStatus())" />
            <span :class="[...labelClasses(handoverStepStatus()), 'text-center']">{{ stageLabel('Handover') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
