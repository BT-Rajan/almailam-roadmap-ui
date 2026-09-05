<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import {
  PROJECT_STAGE_ALLOWED_TRANSITIONS,
  PROJECT_STATUS_ALLOWED_TRANSITIONS,
  isStageReasonRequired,
  isStatusReasonRequired,
} from '@/constants/projectOptions'
import { projectService } from '@/services/projectService'
import { getWorkflowStageLabel } from '@/utils/projectHelpers'
import type { StageEligibility } from '@/types/Project'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    kind: 'stage' | 'status'
    currentValue: string
    loading?: boolean
    // Only meaningful for kind="stage" -- whether this project's
    // workflow includes a Design/Supervision stage at all, so a project
    // that skips one isn't offered it as a stage to move into.
    includesDesign?: boolean
    includesSupervision?: boolean
    // Only meaningful for kind="stage" -- which project to check real
    // exit-criteria eligibility for (see eligibility below). Status
    // changes have no equivalent server-side eligibility check.
    projectId?: string
  }>(),
  { includesDesign: true, includesSupervision: true, projectId: undefined },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { value: string; reason?: string }]
}>()

const { t } = useI18n()

const title = computed(() => (props.kind === 'stage' ? t('project.transitionDialog.changeWorkflowStage') : t('project.transitionDialog.changeProjectStatus')))
const fieldLabel = computed(() => (props.kind === 'stage' ? t('project.transitionDialog.newStage') : t('project.transitionDialog.newStatus')))

const STAGE_LABEL_KEYS: Record<string, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
}

// One real backend check per structurally-possible stage (see
// project_service.get_stage_eligibility) -- lets this dialog disable,
// and explain, a stage the project genuinely can't move to yet instead
// of only finding out after Confirm is clicked. Fetched fresh every
// time the dialog opens, since the project may have changed since the
// last time it was open.
const eligibility = ref<StageEligibility[]>([])
const isLoadingEligibility = ref(false)

const baseOptions = computed(() => {
  const table = props.kind === 'stage' ? PROJECT_STAGE_ALLOWED_TRANSITIONS : PROJECT_STATUS_ALLOWED_TRANSITIONS
  const targets = (table[props.currentValue] ?? []).filter((value) => {
    if (props.kind !== 'stage') return true
    if (value === 'Design') return props.includesDesign
    if (value === 'Supervision') return props.includesSupervision
    return true
  })
  return targets.map((value) => ({
    label: props.kind === 'stage' ? getWorkflowStageLabel(value) : value,
    value,
    labelKey: props.kind === 'stage' ? STAGE_LABEL_KEYS[value] : STATUS_LABEL_KEYS[value],
  }))
})

function eligibilityFor(value: string): StageEligibility | undefined {
  return eligibility.value.find((item) => item.stage === value)
}

const options = computed(() =>
  baseOptions.value.map((option) => {
    if (props.kind !== 'stage') return option
    const entry = eligibilityFor(option.value)
    return entry && !entry.eligible ? { ...option, disabled: true } : option
  }),
)

const selectedEligibility = computed(() => (props.kind === 'stage' ? eligibilityFor(form.value) : undefined))

const form = reactive({ value: '', reason: '' })
const errors = reactive({ value: '', reason: '' })

const reasonRequired = computed(() => {
  if (!form.value) return false
  return props.kind === 'stage'
    ? isStageReasonRequired(props.currentValue, form.value)
    : isStatusReasonRequired(props.currentValue, form.value)
})

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    form.value = baseOptions.value.length === 1 ? baseOptions.value[0].value : ''
    form.reason = ''
    errors.value = ''
    errors.reason = ''
    eligibility.value = []

    if (props.kind === 'stage' && props.projectId) {
      isLoadingEligibility.value = true
      try {
        eligibility.value = await projectService.getStageEligibility(props.projectId)
      } catch {
        // Falls back to "no eligibility info" -- every option stays
        // selectable and the backend still enforces the real rule on
        // submit, same as before this dialog knew how to check ahead.
      } finally {
        isLoadingEligibility.value = false
      }
    }
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.value = form.value ? '' : 'Please select an option'
  errors.reason = reasonRequired.value && !form.reason.trim() ? 'A reason is required for this change' : ''
  if (errors.value || errors.reason) return
  if (selectedEligibility.value && !selectedEligibility.value.eligible) return

  emit('confirm', { value: form.value, reason: form.reason.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="title" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.value" :label="fieldLabel" required :options="options" :error="errors.value" />
      <p v-if="selectedEligibility && !selectedEligibility.eligible" class="-mt-2 text-xs text-danger-500">
        {{ selectedEligibility.reason }}
      </p>
      <TextArea
        v-model="form.reason"
        :label="t('project.transitionDialog.reason')"
        :required="reasonRequired"
        :error="errors.reason"
        :hint="reasonRequired ? t('project.transitionDialog.reasonRequiredHint') : t('common.optional')"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton
        :loading="loading || isLoadingEligibility"
        :disabled="Boolean(selectedEligibility && !selectedEligibility.eligible)"
        @click="handleConfirm"
      >
        {{ t('common.confirm') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
