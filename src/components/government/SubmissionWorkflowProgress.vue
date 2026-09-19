<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ResponseOutcome, SubmissionStage, SubmissionWorkspaceTab } from '@/types/Submission'
import { stepBarClasses, stepLabelClasses } from '@/utils/stepperStyle'
import type { StepStatus } from '@/utils/stepperStyle'
import { SUBMISSION_STAGES, SUBMISSION_WORKSPACE_TABS, getSubmissionOutcomeVariant } from '@/utils/submissionHelpers'

// A permit application's 5-step stepper: Overview, then Prepare / Apply /
// Track / Close. Built to behave exactly like the project's
// WorkflowProgress.vue --
//   - same segmented-bar look, colors (stepperStyle.ts) and
//     "Stage N of M · Label" summary line;
//   - colors follow where the application actually IS (its real stage),
//     not which step you're viewing;
//   - every step is always clickable (a "go to" link, never locked), and
//     clicking emits 'navigate-tab' for the page to switch its panel.
// Overview is a view, not a backend stage, so it always reads complete.
interface Props {
  stage: SubmissionStage
  responseOutcome?: ResponseOutcome | null
}

const props = withDefaults(defineProps<Props>(), { responseOutcome: null })

const emit = defineEmits<{
  'navigate-tab': [tab: SubmissionWorkspaceTab]
}>()

const { t } = useI18n()

const TAB_LABEL_KEYS: Record<SubmissionWorkspaceTab, string> = {
  Overview: 'government.submissionStage.overview',
  Prepare: 'government.submissionStage.prepare',
  Apply: 'government.submissionStage.apply',
  Track: 'government.submissionStage.track',
  Close: 'government.submissionStage.close',
}

const OUTCOME_LABEL_KEYS: Record<ResponseOutcome, string> = {
  Approved: 'government.responseOutcome.approved',
  Rejected: 'government.responseOutcome.rejected',
  'No Response': 'government.responseOutcome.noResponse',
  Withdrawn: 'government.responseOutcome.withdrawn',
}

function tabLabel(tab: SubmissionWorkspaceTab): string {
  return t(TAB_LABEL_KEYS[tab])
}

// Rank of the application's real stage within the 5 steps (Overview is
// rank 0, so Prepare is 1 ... Close is 4).
const currentRank = computed(() => SUBMISSION_STAGES.indexOf(props.stage) + 1)
const isClosed = computed(() => props.stage === 'Close')

function stepStatus(tab: SubmissionWorkspaceTab): StepStatus {
  const rank = SUBMISSION_WORKSPACE_TABS.indexOf(tab)
  // A closed application is finished -- every step, Close included, is
  // done (same as Handover reading complete once the project is).
  if (isClosed.value || rank < currentRank.value) return 'complete'
  if (rank === currentRank.value) return 'current'
  return 'upcoming'
}

function segmentClasses(status: StepStatus): string[] {
  return [...stepBarClasses(status), 'w-full']
}

const outcomeLabel = computed(() => (props.responseOutcome ? t(OUTCOME_LABEL_KEYS[props.responseOutcome]) : undefined))
</script>

<template>
  <!-- No card wrapper of its own -- like WorkflowProgress.vue, this sits
       beneath the page header inside one shared card, separated by a
       hairline. -->
  <div class="border-t border-border-light p-3">
    <div class="mb-2 flex items-center justify-between gap-3">
      <p class="text-sm font-medium text-text-primary">
        {{
          t('project.workflowProgressStage', {
            current: currentRank + 1,
            total: SUBMISSION_WORKSPACE_TABS.length,
            label: tabLabel(stage),
          })
        }}
      </p>
      <StatusBadge
        v-if="isClosed && outcomeLabel"
        :label="t('government.workspacePage.outcomeBadge', { outcome: outcomeLabel })"
        :variant="getSubmissionOutcomeVariant(responseOutcome)"
      />
    </div>
    <div class="overflow-x-auto pb-1">
      <div class="min-w-[520px]">
        <div class="flex items-stretch gap-2" role="group" :aria-label="t('government.workspacePage.tabsAria')">
          <button
            v-for="(tab, index) in SUBMISSION_WORKSPACE_TABS"
            :key="tab"
            type="button"
            class="flex flex-1 flex-col items-stretch gap-1"
            :aria-label="t('common.goToStep', { step: index + 1, label: tabLabel(tab) })"
            :aria-current="stepStatus(tab) === 'current' ? 'step' : undefined"
            @click="emit('navigate-tab', tab)"
          >
            <span :class="segmentClasses(stepStatus(tab))" />
            <span :class="[...stepLabelClasses(stepStatus(tab)), 'text-center']">{{ tabLabel(tab) }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
