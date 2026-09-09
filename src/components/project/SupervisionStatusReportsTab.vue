<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileText } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import { useStatusReportStore } from '@/stores/statusReportStore'
import type { Project } from '@/types/Project'
import type { StatusReport, StatusReportStatus } from '@/types/StatusReport'

const props = defineProps<{ project: Project }>()

const { t } = useI18n()
const { isRtl } = useLocale()
const statusReportStore = useStatusReportStore()

// Previous/next chevrons point the way the reader moves, which reverses
// with reading direction rather than staying physically fixed -- same
// convention as SitePortalCalendarPage.vue's own month nav.
const previousMonthIcon = computed(() => (isRtl.value ? ChevronRight : ChevronLeft))
const nextMonthIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

const visibleMonth = ref(new Date())
const selectedDateReports = ref<StatusReport[]>([])
const isDetailOpen = ref(false)

function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const monthTitle = computed(() => visibleMonth.value.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }))

// This project's whole report history is fetched once (see onMounted
// below) rather than range-fetched per visible month like the site
// engineer portal's own calendar does -- that one paginates by month
// because a single engineer's reports span every project they've ever
// worked; here the dataset is already scoped to one project, so month
// navigation is just a client-side filter over the one list.
const projectReports = computed<StatusReport[]>(() => statusReportStore.projectReports[props.project.projectNo] ?? [])

const reportsByDate = computed(() => {
  const map = new Map<string, StatusReport[]>()
  for (const report of projectReports.value) {
    const existing = map.get(report.reportDate)
    if (existing) existing.push(report)
    else map.set(report.reportDate, [report])
  }
  return map
})

const calendarDays = computed(() => {
  const year = visibleMonth.value.getFullYear()
  const month = visibleMonth.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())

  const days: Date[] = []
  const current = new Date(startDate)
  while (current <= lastDay || current.getDay() !== 0) {
    days.push(new Date(current))
    current.setDate(current.getDate() + 1)
  }
  return days
})

const weekDays = computed(() => [
  t('project.supervisionReportsTab.weekdaySun'),
  t('project.supervisionReportsTab.weekdayMon'),
  t('project.supervisionReportsTab.weekdayTue'),
  t('project.supervisionReportsTab.weekdayWed'),
  t('project.supervisionReportsTab.weekdayThu'),
  t('project.supervisionReportsTab.weekdayFri'),
  t('project.supervisionReportsTab.weekdaySat'),
])

function loadReports(): void {
  void statusReportStore.loadForProject(props.project.projectNo)
}

onMounted(loadReports)

function goToPreviousMonth(): void {
  const next = new Date(visibleMonth.value)
  next.setMonth(next.getMonth() - 1)
  visibleMonth.value = next
}

function goToNextMonth(): void {
  const next = new Date(visibleMonth.value)
  next.setMonth(next.getMonth() + 1)
  visibleMonth.value = next
}

function handleDayClick(day: Date): void {
  const reports = reportsByDate.value.get(formatDateKey(day))
  if (!reports || reports.length === 0) return
  selectedDateReports.value = reports
  isDetailOpen.value = true
}

function isCurrentMonth(day: Date): boolean {
  return day.getMonth() === visibleMonth.value.getMonth()
}

// One dot per report on a day, capped visually -- in practice a project
// has a single assigned engineer so this is almost always one dot, but
// the data model allows more than one filer per day so the cap (with
// the exact count still visible in the detail dialog) matches the
// portal calendar's own handling.
function dotsFor(day: Date): StatusReport[] {
  return (reportsByDate.value.get(formatDateKey(day)) ?? []).slice(0, 3)
}

// "Pending" / "Attached" are the recipient's own review-queue states --
// from a staff member looking at this project's history, "Pending
// Review" / "Reviewed" reads more clearly than the engineer-portal's
// "Submitted" / "Reviewed" framing (see utils/statusReportHelpers.ts,
// written for the filing engineer's own point of view instead).
const STATUS_LABEL_KEYS: Record<StatusReportStatus, string> = {
  Pending: 'project.supervisionReportsTab.statusPendingReview',
  Attached: 'project.supervisionReportsTab.statusReviewed',
}
function reportStatusLabel(status: StatusReportStatus): string {
  return t(STATUS_LABEL_KEYS[status])
}
function reportStatusVariant(status: StatusReportStatus): 'info' | 'success' {
  return status === 'Attached' ? 'success' : 'info'
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.supervisionReportsTab.title') }}</h3>
      <p class="text-sm text-text-muted">{{ t('project.supervisionReportsTab.subtitle') }}</p>
    </div>

    <Card>
      <div class="mb-4 flex items-center justify-between">
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" :aria-label="t('project.supervisionReportsTab.previousMonth')" @click="goToPreviousMonth">
          <component :is="previousMonthIcon" class="h-4 w-4" />
        </button>
        <p class="text-sm font-semibold text-text-primary">{{ monthTitle }}</p>
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" :aria-label="t('project.supervisionReportsTab.nextMonth')" @click="goToNextMonth">
          <component :is="nextMonthIcon" class="h-4 w-4" />
        </button>
      </div>

      <ErrorState v-if="statusReportStore.projectError" :description="statusReportStore.projectError" @retry="loadReports" />

      <div v-else-if="statusReportStore.isProjectLoading" class="grid grid-cols-7 gap-1">
        <div v-for="cell in 35" :key="cell" class="aspect-square animate-pulse rounded-lg bg-bg-secondary" />
      </div>

      <div v-else>
        <div class="mb-1 grid grid-cols-7 gap-1">
          <div v-for="day in weekDays" :key="day" class="py-1 text-center text-xs font-semibold text-text-muted">
            {{ day }}
          </div>
        </div>

        <div class="grid grid-cols-7 gap-1">
          <button
            v-for="(day, index) in calendarDays"
            :key="index"
            type="button"
            class="relative flex aspect-square flex-col items-center justify-center rounded-lg border border-border-light text-sm transition-colors"
            :class="[
              isCurrentMonth(day) ? 'bg-bg-card text-text-primary' : 'bg-bg-secondary text-text-muted',
              (reportsByDate.get(formatDateKey(day))?.length ?? 0) > 0 ? 'cursor-pointer hover:border-primary-400 hover:bg-primary-50' : 'cursor-default',
              formatDateKey(day) === formatDateKey(new Date()) ? 'ring-2 ring-accent-400' : '',
            ]"
            @click="handleDayClick(day)"
          >
            <span>{{ day.getDate() }}</span>
            <span v-if="dotsFor(day).length > 0" class="mt-0.5 flex items-center gap-0.5">
              <span
                v-for="report in dotsFor(day)"
                :key="report.id"
                class="h-1.5 w-1.5 rounded-full"
                :class="report.status === 'Attached' ? 'bg-success-500' : 'bg-info-500'"
              />
            </span>
          </button>
        </div>

        <EmptyState
          v-if="projectReports.length === 0"
          :icon="FileText"
          :title="t('project.supervisionReportsTab.noReportsTitle')"
          :description="t('project.supervisionReportsTab.noReportsDescription')"
          class="mt-4"
        />
      </div>
    </Card>

    <BaseDialog v-model="isDetailOpen" :title="selectedDateReports.length > 0 ? selectedDateReports[0].reportDate : ''" size="md">
      <div class="flex flex-col gap-5">
        <div v-for="report in selectedDateReports" :key="report.id" class="flex flex-col gap-3 border-b border-border-light pb-4 text-sm last:border-0 last:pb-0">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-text-primary">{{ report.engineerName }}</span>
            <StatusBadge :label="reportStatusLabel(report.status)" :variant="reportStatusVariant(report.status)" />
          </div>
          <div class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('project.supervisionReportsTab.reportNo') }}</span>
            <span class="font-medium text-text-primary">{{ report.reportNo }}</span>
          </div>
          <div v-if="report.receiptType" class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('project.supervisionReportsTab.receiptHandover') }}</span>
            <span class="font-medium text-text-primary">{{ report.receiptType }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('project.supervisionReportsTab.supervision') }}</span>
            <span class="font-medium text-text-primary">{{ report.supervisionType }}</span>
          </div>
          <div>
            <p class="mb-1 text-text-muted">{{ t('project.supervisionReportsTab.notes') }}</p>
            <p class="whitespace-pre-wrap rounded-lg bg-bg-secondary p-3 text-text-primary" dir="auto">{{ report.notes }}</p>
          </div>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
