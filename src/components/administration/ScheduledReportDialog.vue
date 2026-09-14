<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmailListInput from '@/components/common/EmailListInput.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { useProjectStore } from '@/stores/projectStore'
import { todayIso } from '@/utils/dateFormatter'
import type { ScheduledReport, ScheduledReportFrequency, ScheduledReportInput, ScheduledReportPeriod, ScheduledReportType } from '@/types/ScheduledReport'
import type { SelectOption } from '@/types/Ui'

// Every recipient beyond this is rejected by EmailListInput before it's
// even added, and the backend's own ScheduledReportIn.recipients caps
// at the same number (schemas/scheduled_report.py) -- kept in sync so a
// request that somehow bypassed this dialog still can't exceed it.
const MAX_RECIPIENTS = 5

interface Props {
  modelValue: boolean
  schedule?: ScheduledReport
  saving?: boolean
}

const props = withDefaults(defineProps<Props>(), { schedule: undefined, saving: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [payload: ScheduledReportInput]
}>()

const { t } = useI18n()
const projectStore = useProjectStore()

const isEditMode = computed(() => props.schedule !== undefined)

function blankForm(): ScheduledReportInput {
  return {
    name: '',
    reportType: 'business_summary',
    projectNo: null,
    period: 'last_30_days',
    recipients: [],
    subject: null,
    messageBody: null,
    frequency: 'daily',
    sendTime: '09:00',
    sendDatetime: null,
    dayOfWeek: 0,
    dayOfMonth: 1,
    startDate: todayIso(),
    endDate: null,
    isActive: true,
  }
}

const form = ref<ScheduledReportInput>(blankForm())
const errorMessage = ref('')

watch(
  () => [props.modelValue, props.schedule] as const,
  ([isOpen, schedule]) => {
    if (!isOpen) return
    errorMessage.value = ''
    if (schedule) {
      form.value = {
        name: schedule.name,
        reportType: schedule.reportType,
        projectNo: schedule.projectNo,
        period: schedule.period ?? 'last_30_days',
        recipients: [...schedule.recipients],
        subject: schedule.subject,
        messageBody: schedule.messageBody,
        frequency: schedule.frequency,
        sendTime: schedule.sendTime ?? '09:00',
        sendDatetime: schedule.sendDatetime ? schedule.sendDatetime.slice(0, 16) : null,
        dayOfWeek: schedule.dayOfWeek ?? 0,
        dayOfMonth: schedule.dayOfMonth ?? 1,
        startDate: schedule.startDate ?? todayIso(),
        endDate: schedule.endDate,
        isActive: schedule.isActive,
      }
    } else {
      form.value = blankForm()
    }
    if (projectStore.projects.length === 0) projectStore.loadProjects()
  },
  { immediate: true },
)

const REPORT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Business Summary', value: 'business_summary', labelKey: 'administration.scheduledReportsPage.reportTypeBusinessSummary' },
  { label: 'Financial Summary', value: 'financial_summary', labelKey: 'administration.scheduledReportsPage.reportTypeFinancialSummary' },
  { label: 'Project Status', value: 'project_status', labelKey: 'administration.scheduledReportsPage.reportTypeProjectStatus' },
]

const PERIOD_OPTIONS: SelectOption[] = [
  { label: 'Last 7 Days', value: 'last_7_days', labelKey: 'administration.scheduledReportsPage.periodLast7Days' },
  { label: 'Last 30 Days', value: 'last_30_days', labelKey: 'administration.scheduledReportsPage.periodLast30Days' },
  { label: 'This Month', value: 'this_month', labelKey: 'administration.scheduledReportsPage.periodThisMonth' },
  { label: 'Last Month', value: 'last_month', labelKey: 'administration.scheduledReportsPage.periodLastMonth' },
  { label: 'This Quarter', value: 'this_quarter', labelKey: 'administration.scheduledReportsPage.periodThisQuarter' },
  { label: 'This Year', value: 'this_year', labelKey: 'administration.scheduledReportsPage.periodThisYear' },
]

const FREQUENCY_OPTIONS: SelectOption[] = [
  { label: 'Once', value: 'once', labelKey: 'administration.scheduledReportsPage.frequencyOnce' },
  { label: 'Daily', value: 'daily', labelKey: 'administration.scheduledReportsPage.frequencyDaily' },
  { label: 'Weekly', value: 'weekly', labelKey: 'administration.scheduledReportsPage.frequencyWeekly' },
  { label: 'Monthly', value: 'monthly', labelKey: 'administration.scheduledReportsPage.frequencyMonthly' },
]

const WEEKDAY_OPTIONS: SelectOption[] = [
  { label: 'Monday', value: '0', labelKey: 'administration.scheduledReportsPage.weekdayMonday' },
  { label: 'Tuesday', value: '1', labelKey: 'administration.scheduledReportsPage.weekdayTuesday' },
  { label: 'Wednesday', value: '2', labelKey: 'administration.scheduledReportsPage.weekdayWednesday' },
  { label: 'Thursday', value: '3', labelKey: 'administration.scheduledReportsPage.weekdayThursday' },
  { label: 'Friday', value: '4', labelKey: 'administration.scheduledReportsPage.weekdayFriday' },
  { label: 'Saturday', value: '5', labelKey: 'administration.scheduledReportsPage.weekdaySaturday' },
  { label: 'Sunday', value: '6', labelKey: 'administration.scheduledReportsPage.weekdaySunday' },
]

const projectOptions = computed<SelectOption[]>(() =>
  projectStore.projects.map((project) => ({ label: `${project.projectNo} \u2014 ${project.projectName}`, value: project.projectNo })),
)

const isRecurring = computed(() => form.value.frequency !== 'once')

function handleClose(): void {
  emit('update:modelValue', false)
}

function handleSubmit(): void {
  errorMessage.value = ''
  if (form.value.recipients.length === 0) {
    errorMessage.value = t('administration.scheduledReportsPage.recipientsHint')
    return
  }
  emit('save', {
    ...form.value,
    projectNo: form.value.reportType === 'project_status' ? form.value.projectNo : null,
    period: form.value.reportType === 'financial_summary' ? form.value.period : null,
    sendDatetime: form.value.frequency === 'once' && form.value.sendDatetime ? `${form.value.sendDatetime}:00` : null,
    sendTime: isRecurring.value ? form.value.sendTime : null,
    dayOfWeek: form.value.frequency === 'weekly' ? form.value.dayOfWeek : null,
    dayOfMonth: form.value.frequency === 'monthly' ? form.value.dayOfMonth : null,
    startDate: isRecurring.value ? form.value.startDate : null,
    endDate: isRecurring.value ? form.value.endDate : null,
  })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="isEditMode ? t('administration.scheduledReportsPage.editDialogTitle') : t('administration.scheduledReportsPage.createDialogTitle')"
    size="lg"
    :closable="!saving"
    @update:model-value="handleClose"
  >
    <div class="flex flex-col gap-6">
      <p v-if="errorMessage" class="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">{{ errorMessage }}</p>

      <FormSection :title="t('administration.scheduledReportsPage.sectionBasics')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <div class="tablet:col-span-2">
            <TextInput v-model="form.name" :label="t('administration.scheduledReportsPage.name')" :placeholder="t('administration.scheduledReportsPage.namePlaceholder')" required />
          </div>
          <SelectBox
            :model-value="form.reportType"
            :label="t('administration.scheduledReportsPage.reportType')"
            :options="REPORT_TYPE_OPTIONS"
            @update:model-value="(value) => (form.reportType = value as ScheduledReportType)"
          />
          <SelectBox
            v-if="form.reportType === 'project_status'"
            :model-value="form.projectNo ?? ''"
            :label="t('administration.scheduledReportsPage.project')"
            :placeholder="t('administration.scheduledReportsPage.projectPlaceholder')"
            :options="projectOptions"
            @update:model-value="(value) => (form.projectNo = value || null)"
          />
          <SelectBox
            v-if="form.reportType === 'financial_summary'"
            :model-value="form.period ?? 'last_30_days'"
            :label="t('administration.scheduledReportsPage.period')"
            :options="PERIOD_OPTIONS"
            @update:model-value="(value) => (form.period = value as ScheduledReportPeriod)"
          />
        </div>
      </FormSection>

      <FormSection :title="t('administration.scheduledReportsPage.sectionRecipients')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <div class="tablet:col-span-2">
            <EmailListInput
              :model-value="form.recipients"
              :label="t('administration.scheduledReportsPage.sectionRecipients')"
              :hint="t('administration.scheduledReportsPage.recipientsHint')"
              :placeholder="t('administration.scheduledReportsPage.recipientsPlaceholder')"
              :max="MAX_RECIPIENTS"
              required
              @update:model-value="(value) => (form.recipients = value)"
            />
          </div>
          <TextInput
            :model-value="form.subject ?? ''"
            :label="t('administration.scheduledReportsPage.subject')"
            :placeholder="t('administration.scheduledReportsPage.subjectPlaceholder')"
            @update:model-value="(value) => (form.subject = value || null)"
          />
          <div class="tablet:col-span-2">
            <TextArea
              :model-value="form.messageBody ?? ''"
              :label="t('administration.scheduledReportsPage.messageBody')"
              :placeholder="t('administration.scheduledReportsPage.messageBodyPlaceholder')"
              :rows="3"
              @update:model-value="(value) => (form.messageBody = value || null)"
            />
          </div>
        </div>
      </FormSection>

      <FormSection :title="t('administration.scheduledReportsPage.sectionSchedule')">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <SelectBox
            :model-value="form.frequency"
            :label="t('administration.scheduledReportsPage.frequency')"
            :options="FREQUENCY_OPTIONS"
            @update:model-value="(value) => (form.frequency = value as ScheduledReportFrequency)"
          />

          <template v-if="form.frequency === 'once'">
            <div>
              <label class="mb-1.5 block text-sm font-medium text-text-primary">{{ t('administration.scheduledReportsPage.sendDate') }}</label>
              <input
                :value="form.sendDatetime ?? ''"
                type="datetime-local"
                class="h-10 w-full rounded-lg border border-border-default bg-bg-card px-3 text-sm text-text-primary focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/30"
                @input="(event) => (form.sendDatetime = (event.target as HTMLInputElement).value || null)"
              />
            </div>
          </template>

          <template v-else>
            <TimePicker
              :model-value="form.sendTime ?? ''"
              :label="t('administration.scheduledReportsPage.sendTimeLabel')"
              required
              @update:model-value="(value) => (form.sendTime = value)"
            />
            <SelectBox
              v-if="form.frequency === 'weekly'"
              :model-value="String(form.dayOfWeek)"
              :label="t('administration.scheduledReportsPage.dayOfWeek')"
              :options="WEEKDAY_OPTIONS"
              @update:model-value="(value) => (form.dayOfWeek = Number(value))"
            />
            <NumberInput
              v-if="form.frequency === 'monthly'"
              :model-value="form.dayOfMonth ?? 1"
              :label="t('administration.scheduledReportsPage.dayOfMonth')"
              :min="1"
              :max="31"
              @update:model-value="(value) => (form.dayOfMonth = Number(value))"
            />
            <DatePicker
              :model-value="form.startDate ?? ''"
              :label="t('administration.scheduledReportsPage.startDate')"
              required
              @update:model-value="(value) => (form.startDate = value)"
            />
            <DatePicker
              :model-value="form.endDate ?? ''"
              :label="t('administration.scheduledReportsPage.endDate')"
              :hint="t('administration.scheduledReportsPage.endDateHint')"
              :min="form.startDate ?? undefined"
              @update:model-value="(value) => (form.endDate = value || null)"
            />
          </template>

          <div class="tablet:col-span-2">
            <ToggleSwitch v-model="form.isActive" :label="t('administration.scheduledReportsPage.isActive')" :hint="t('administration.scheduledReportsPage.isActiveHint')" />
          </div>
        </div>
      </FormSection>
    </div>

    <template #footer>
      <FormActionBar :submit-label="t('administration.scheduledReportsPage.save')" :loading="saving" @cancel="handleClose" @submit="handleSubmit" />
    </template>
  </BaseDialog>
</template>
