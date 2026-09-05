<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileText } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useSitePortalStore } from '@/stores/sitePortalStore'
import type { StatusReport } from '@/types/StatusReport'
import { engineerStatusLabel, engineerStatusVariant } from '@/utils/statusReportHelpers'

const { t } = useI18n()
const sitePortalStore = useSitePortalStore()

const visibleMonth = ref(new Date())
// A day can now hold more than one report -- an engineer on several
// projects files one per project, so the detail view for a date is a
// list, not a single report.
const selectedDateReports = ref<StatusReport[]>([])
const isDetailOpen = ref(false)

function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const monthTitle = computed(() => visibleMonth.value.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }))

const reportsByDate = computed(() => {
  const map = new Map<string, StatusReport[]>()
  for (const report of sitePortalStore.calendarReports) {
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
  t('sitePortal.calendarPage.weekdaySun'),
  t('sitePortal.calendarPage.weekdayMon'),
  t('sitePortal.calendarPage.weekdayTue'),
  t('sitePortal.calendarPage.weekdayWed'),
  t('sitePortal.calendarPage.weekdayThu'),
  t('sitePortal.calendarPage.weekdayFri'),
  t('sitePortal.calendarPage.weekdaySat'),
])

async function loadMonth(): Promise<void> {
  const year = visibleMonth.value.getFullYear()
  const month = visibleMonth.value.getMonth()
  const start = formatDateKey(new Date(year, month, 1))
  const end = formatDateKey(new Date(year, month + 1, 0))
  await sitePortalStore.loadCalendarRange(start, end)
}

onMounted(loadMonth)
watch(visibleMonth, loadMonth)

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

// One dot per report on a day, capped visually -- an engineer on many
// projects filing several reports in one day shouldn't overflow the
// cell; the count label below covers the exact number either way.
function dotsFor(day: Date): StatusReport[] {
  return (reportsByDate.value.get(formatDateKey(day)) ?? []).slice(0, 3)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h1 class="text-lg font-semibold text-text-primary">{{ t('sitePortal.calendarPage.myReports') }}</h1>
      <p class="text-sm text-text-muted">{{ t('sitePortal.calendarPage.viewOnlyNotice') }}</p>
    </div>

    <Card>
      <div class="mb-4 flex items-center justify-between">
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" :aria-label="t('sitePortal.calendarPage.previousMonth')" @click="goToPreviousMonth">
          <ChevronLeft class="h-4 w-4" />
        </button>
        <p class="text-sm font-semibold text-text-primary">{{ monthTitle }}</p>
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" :aria-label="t('sitePortal.calendarPage.nextMonth')" @click="goToNextMonth">
          <ChevronRight class="h-4 w-4" />
        </button>
      </div>

      <ErrorState v-if="sitePortalStore.error" :description="sitePortalStore.error" @retry="loadMonth" />

      <div v-else-if="sitePortalStore.isLoading" class="grid grid-cols-7 gap-1">
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
          v-if="sitePortalStore.calendarReports.length === 0"
          :icon="FileText"
          :title="t('sitePortal.calendarPage.noReportsThisMonth')"
          class="mt-4"
        />
      </div>
    </Card>

    <BaseDialog
      v-model="isDetailOpen"
      :title="selectedDateReports.length > 0 ? selectedDateReports[0].reportDate : ''"
      size="md"
    >
      <div class="flex flex-col gap-5">
        <div v-for="report in selectedDateReports" :key="report.id" class="flex flex-col gap-3 border-b border-border-light pb-4 text-sm last:border-0 last:pb-0">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-text-primary">{{ report.projectName }}</span>
            <StatusBadge
              :label="engineerStatusLabel(report.status)"
              :variant="engineerStatusVariant(report.status)"
            />
          </div>
          <div class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('sitePortal.calendarPage.reportNo') }}</span>
            <span class="font-medium text-text-primary">{{ report.reportNo }}</span>
          </div>
          <div v-if="report.receiptType" class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('sitePortal.calendarPage.receiptHandover') }}</span>
            <span class="font-medium text-text-primary">{{ report.receiptType }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-text-muted">{{ t('sitePortal.calendarPage.supervision') }}</span>
            <span class="font-medium text-text-primary">{{ report.supervisionType }}</span>
          </div>
          <div>
            <p class="mb-1 text-text-muted">{{ t('sitePortal.calendarPage.notes') }}</p>
            <p class="whitespace-pre-wrap rounded-lg bg-bg-secondary p-3 text-text-primary" dir="auto">{{ report.notes }}</p>
          </div>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
