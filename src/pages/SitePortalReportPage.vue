<script setup lang="ts">
import { CheckCircle2, Save } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useSitePortalStore } from '@/stores/sitePortalStore'
import { useToastStore } from '@/stores/toastStore'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()
const sitePortalStore = useSitePortalStore()
const toastStore = useToastStore()
const resultDialogStore = useResultDialogStore()

const isLoading = ref(true)
const isSaving = ref(false)

const form = reactive({
  projectId: '',
  receiptType: '',
  supervisionType: 'Full-time' as 'Full-time' | 'Part-time',
  notes: '',
})

const projectOptions = ref<SelectOption[]>([])
const supervisionOptions = computed<SelectOption[]>(() => [
  { label: 'Full-time', value: 'Full-time', labelKey: 'sitePortal.reportPage.supervisionFullTime' },
  { label: 'Part-time', value: 'Part-time', labelKey: 'sitePortal.reportPage.supervisionPartTime' },
])

// Kuwait time explicitly, not the device's local timezone -- this is
// purely the header label, but it has to agree with what the server
// actually files the report against (see status_report_service.py's
// REPORT_FILING_TIMEZONE), or an engineer whose phone clock is set to
// their own timezone could see a date here that doesn't match which
// day their report actually lands on.
const todaysDate = new Date().toLocaleDateString('en-GB', {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  timeZone: 'Asia/Kuwait',
})

onMounted(async () => {
  try {
    await Promise.all([sitePortalStore.loadProjects(), sitePortalStore.loadTodaysReports()])
    projectOptions.value = sitePortalStore.projects.map((p) => ({
      label: p.canFileReport ? p.projectName : `${p.projectName}${t('sitePortal.reportPage.windowClosedSuffix')}`,
      value: p.id,
      disabled: !p.canFileReport,
    }))
    // Default to the first still-open, not-yet-filed project so the
    // common case (an engineer opening the page to file whatever's
    // still outstanding) doesn't require an extra selection -- falls
    // back to the first open project, and only to a closed one if
    // every assigned project's window has actually closed (so there's
    // still something selected to show why).
    const openProjects = sitePortalStore.projects.filter((p) => p.canFileReport)
    const firstUnfiled = openProjects.find((p) => !sitePortalStore.todaysReports[p.id])
    form.projectId = (firstUnfiled ?? openProjects[0] ?? sitePortalStore.projects[0])?.id ?? ''
  } finally {
    isLoading.value = false
  }
})

// The report for whichever project is currently selected -- an engineer
// on several projects files one report per project per day, so "today's
// report" depends entirely on which project is picked above.
const currentReport = computed(() => sitePortalStore.todaysReports[form.projectId])

const selectedProject = computed(() => sitePortalStore.projects.find((p) => p.id === form.projectId))

// Pre-fills (or clears, for a project with nothing filed yet) the rest
// of the form whenever the selected project changes -- this is what
// makes the page double as both "file" (no report yet for this
// project, form starts blank) and "edit" (report already exists for
// this project, form shows what's already there), per project, without
// separate screens for each.
watch(
  () => form.projectId,
  (projectId) => {
    const report = projectId ? sitePortalStore.todaysReports[projectId] : undefined
    form.receiptType = report?.receiptType ?? ''
    form.supervisionType = report?.supervisionType ?? 'Full-time'
    form.notes = report?.notes ?? ''
  },
  { immediate: true },
)

// Two separate reasons the form can be read-only, each with its own
// message: the recipient has already reviewed & attached today's
// report (permanent, this one report), or the selected project's
// filing window itself is closed (every report, today and any other
// day -- see EngineerProjectOption.blockReason from the server, the
// same Kuwait-time/start-target-date/closed-status check the actual
// submit is gated on).
const isReviewed = () => currentReport.value?.status === 'Attached'
const isWindowClosed = computed(() => selectedProject.value ? !selectedProject.value.canFileReport : false)
const isLocked = () => isReviewed() || isWindowClosed.value

const filedCount = computed(() => Object.keys(sitePortalStore.todaysReports).length)

async function handleSubmit(): Promise<void> {
  // Native form submission (Enter key) is a separate trigger path from
  // BaseButton's click handler -- its own click-level guard doesn't cover
  // this, so the re-entrancy check has to live here too.
  if (isSaving.value) return

  if (!form.projectId) {
    toastStore.show('error', 'Project is required', 'Please select which project this report is for.')
    return
  }
  if (!form.notes.trim()) {
    toastStore.show('error', 'Notes are required', 'Please describe today\'s supervision activity.')
    return
  }

  isSaving.value = true
  try {
    await sitePortalStore.fileTodaysReport({
      projectId: form.projectId,
      receiptType: form.receiptType.trim() || undefined,
      supervisionType: form.supervisionType,
      notes: form.notes.trim(),
    })
    resultDialogStore.showSuccess('Report submitted', "Today's status report has been submitted. You can keep editing and re-submitting it until 11:59 PM Kuwait time.")
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to save report', detail)
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h1 class="text-lg font-semibold text-text-primary">{{ t('sitePortal.reportPage.todaysStatusReport') }}</h1>
      <p class="text-sm text-text-muted">{{ todaysDate }}</p>
    </div>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <template v-else>
      <p v-if="sitePortalStore.projects.length > 1" class="text-xs text-text-muted">
        {{ t('sitePortal.reportPage.projectsReportedToday', { filed: filedCount, total: sitePortalStore.projects.length }) }}
      </p>

      <Alert
        v-if="isReviewed()"
        variant="success"
        :title="t('sitePortal.reportPage.reviewedTitle')"
        :description="t('sitePortal.reportPage.reviewedDescription')"
      />
      <Alert
        v-else-if="isWindowClosed"
        variant="warning"
        :title="t('sitePortal.reportPage.filingWindowClosedTitle')"
        :description="selectedProject?.blockReason ?? t('sitePortal.reportPage.filingWindowClosedDefaultDescription')"
      />
      <Alert
        v-else
        variant="info"
        :title="t('sitePortal.reportPage.editableTitle')"
        :description="t('sitePortal.reportPage.editableDescription')"
      />

      <Card>
        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div>
            <SelectBox
              v-model="form.projectId"
              :label="t('sitePortal.reportPage.project')"
              :placeholder="t('sitePortal.reportPage.selectProject')"
              required
              :options="projectOptions"
            />
            <!-- Per-project filed/pending indicator -- an engineer on
                 several projects needs to see, right where they're
                 picking a project, whether this one still needs today's
                 report or is already done. -->
            <p v-if="form.projectId && !isWindowClosed" class="mt-1.5 flex items-center gap-1.5 text-xs">
              <template v-if="currentReport">
                <CheckCircle2 class="h-3.5 w-3.5 text-success-600" />
                <span class="text-success-600">{{ isReviewed() ? t('sitePortal.reportPage.reportFiledAndReviewed') : t('sitePortal.reportPage.reportSubmitted') }}</span>
              </template>
              <span v-else class="text-warning-600">{{ t('sitePortal.reportPage.noReportFiledYet') }}</span>
            </p>
          </div>

          <TextInput
            v-model="form.receiptType"
            :label="t('sitePortal.reportPage.receiptHandover')"
            :placeholder="t('sitePortal.reportPage.receiptHandoverPlaceholder')"
            :disabled="isLocked()"
          />
          <SelectBox
            v-model="form.supervisionType"
            :label="t('sitePortal.reportPage.supervisionType')"
            :disabled="isLocked()"
            :options="supervisionOptions"
          />
          <TextArea
            v-model="form.notes"
            :label="t('sitePortal.reportPage.notes')"
            :placeholder="t('sitePortal.reportPage.notesPlaceholder')"
            :rows="8"
            required
            :disabled="isLocked()"
          />

          <BaseButton v-if="!isLocked()" type="submit" :icon="Save" :loading="isSaving" full-width>
            {{ currentReport ? t('sitePortal.reportPage.updateResubmit') : t('sitePortal.reportPage.submitReport') }}
          </BaseButton>
          <div v-else-if="isReviewed()" class="flex items-center justify-center gap-2 rounded-lg bg-success-50 py-2.5 text-sm font-medium text-success-700">
            <CheckCircle2 class="h-4 w-4" />
            {{ t('sitePortal.reportPage.filedAndReviewed') }}
          </div>
        </form>
      </Card>
    </template>
  </div>
</template>
