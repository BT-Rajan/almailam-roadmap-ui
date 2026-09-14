<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmailListInput from '@/components/common/EmailListInput.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { useScheduledReportStore } from '@/stores/scheduledReportStore'
import { useToastStore } from '@/stores/toastStore'
import { todayIso } from '@/utils/dateFormatter'
import type { ScheduledReportFrequency, ScheduledReportInput, ScheduledReportPeriod, ScheduledReportType } from '@/types/ScheduledReport'
import type { SelectOption } from '@/types/Ui'

// Replaces ScheduledReportDialog.vue's modal -- a dedicated route
// (/admin/scheduled-reports/:scheduleId), same treatment as
// PaymentPlanFormPage.vue: one page decides create vs edit itself from
// whether :scheduleId ('new', or a real id) resolves to an existing
// schedule, rather than a caller-chosen mode prop.

// Every recipient beyond this is rejected by EmailListInput before it's
// even added, and the backend's own ScheduledReportIn.recipients caps
// at the same number (schemas/scheduled_report.py) -- kept in sync so a
// request that somehow bypassed this page still can't exceed it.
const MAX_RECIPIENTS = 5

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const scheduledReportStore = useScheduledReportStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const scheduleId = computed(() => route.params.scheduleId as string)
const isCreateMode = computed(() => scheduleId.value === 'new')

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (scheduledReportStore.schedules.length === 0) await scheduledReportStore.loadSchedules()
  if (projectStore.projects.length === 0) await projectStore.loadProjects()
  isLoading.value = false
}
onMounted(loadData)

const existingSchedule = computed(() =>
  isCreateMode.value ? undefined : scheduledReportStore.schedules.find((schedule) => schedule.id === scheduleId.value),
)

function goBack(): void {
  router.push({ name: ROUTE_NAMES.ADMIN_SCHEDULED_REPORTS })
}

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
  projectStore.projects.map((project) => ({ label: `${project.projectNo} — ${project.projectName}`, value: project.projectNo })),
)

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

// Seeds once loading finishes (from the existing schedule when editing,
// blank otherwise) -- guarded so a later reactive update to
// existingSchedule (e.g. after this page's own save) doesn't silently
// discard in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, existingSchedule.value] as const,
  ([loading, schedule]) => {
    if (loading || isFormSeeded.value) return
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
    isFormSeeded.value = true
  },
  { immediate: true },
)

const isRecurring = computed(() => form.value.frequency !== 'once')

const isSaving = ref(false)

async function handleSubmit(): Promise<void> {
  errorMessage.value = ''
  if (form.value.recipients.length === 0) {
    errorMessage.value = t('administration.scheduledReportsPage.recipientsHint')
    return
  }

  const payload: ScheduledReportInput = {
    ...form.value,
    projectNo: form.value.reportType === 'project_status' ? form.value.projectNo : null,
    period: form.value.reportType === 'financial_summary' ? form.value.period : null,
    sendDatetime: form.value.frequency === 'once' && form.value.sendDatetime ? `${form.value.sendDatetime}:00` : null,
    sendTime: isRecurring.value ? form.value.sendTime : null,
    dayOfWeek: form.value.frequency === 'weekly' ? form.value.dayOfWeek : null,
    dayOfMonth: form.value.frequency === 'monthly' ? form.value.dayOfMonth : null,
    startDate: isRecurring.value ? form.value.startDate : null,
    endDate: isRecurring.value ? form.value.endDate : null,
  }

  isSaving.value = true
  try {
    if (existingSchedule.value) {
      await scheduledReportStore.updateSchedule(existingSchedule.value.id, payload)
    } else {
      await scheduledReportStore.createSchedule(payload)
    }
    toastStore.show('success', t('administration.scheduledReportsPage.scheduleSavedTitle'), t('administration.scheduledReportsPage.scheduleSavedDescription', { name: payload.name }))
    goBack()
  } catch (error) {
    toastStore.show('error', t('administration.scheduledReportsPage.saveFailedTitle'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('administration.scheduledReportsPage.backToSchedules') }}
    </BaseButton>

    <div v-if="isLoading" class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState
      v-else-if="!isCreateMode && !existingSchedule"
      :title="t('administration.scheduledReportsPage.scheduleNotFoundTitle')"
      :description="t('administration.scheduledReportsPage.scheduleNotFoundDescription')"
    />

    <div v-else class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ isCreateMode ? t('administration.scheduledReportsPage.createDialogTitle') : t('administration.scheduledReportsPage.editDialogTitle') }}
      </h1>

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

      <FormActionBar
        class="mt-6"
        :submit-label="t('administration.scheduledReportsPage.save')"
        :loading="isSaving"
        @cancel="goBack"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>
