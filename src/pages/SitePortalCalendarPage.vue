<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileText } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useSitePortalStore } from '@/stores/sitePortalStore'
import type { StatusReport } from '@/types/StatusReport'

const sitePortalStore = useSitePortalStore()

const visibleMonth = ref(new Date())
const selectedReport = ref<StatusReport>()
const isDetailOpen = ref(false)

function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const monthTitle = computed(() => visibleMonth.value.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }))

const reportsByDate = computed(() => {
  const map = new Map<string, StatusReport>()
  for (const report of sitePortalStore.calendarReports) map.set(report.reportDate, report)
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

const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

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
  const report = reportsByDate.value.get(formatDateKey(day))
  if (!report) return
  selectedReport.value = report
  isDetailOpen.value = true
}

function isCurrentMonth(day: Date): boolean {
  return day.getMonth() === visibleMonth.value.getMonth()
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h1 class="text-lg font-semibold text-neutral-900">My Reports</h1>
      <p class="text-sm text-neutral-500">View-only -- tap a date to see that day's report.</p>
    </div>

    <Card>
      <div class="mb-4 flex items-center justify-between">
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" aria-label="Previous month" @click="goToPreviousMonth">
          <ChevronLeft class="h-4 w-4" />
        </button>
        <p class="text-sm font-semibold text-neutral-800">{{ monthTitle }}</p>
        <button type="button" class="rounded-lg p-2 hover:bg-bg-hover" aria-label="Next month" @click="goToNextMonth">
          <ChevronRight class="h-4 w-4" />
        </button>
      </div>

      <ErrorState v-if="sitePortalStore.error" :description="sitePortalStore.error" @retry="loadMonth" />

      <div v-else-if="sitePortalStore.isLoading" class="grid grid-cols-7 gap-1">
        <div v-for="cell in 35" :key="cell" class="aspect-square animate-pulse rounded-lg bg-bg-secondary" />
      </div>

      <div v-else>
        <div class="mb-1 grid grid-cols-7 gap-1">
          <div v-for="day in weekDays" :key="day" class="py-1 text-center text-xs font-semibold text-neutral-400">
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
              isCurrentMonth(day) ? 'bg-bg-card text-neutral-800' : 'bg-bg-secondary text-neutral-300',
              reportsByDate.get(formatDateKey(day)) ? 'cursor-pointer hover:border-primary-400 hover:bg-primary-50' : 'cursor-default',
              formatDateKey(day) === formatDateKey(new Date()) ? 'ring-2 ring-accent-400' : '',
            ]"
            @click="handleDayClick(day)"
          >
            <span>{{ day.getDate() }}</span>
            <span
              v-if="reportsByDate.get(formatDateKey(day))"
              class="mt-0.5 h-1.5 w-1.5 rounded-full"
              :class="reportsByDate.get(formatDateKey(day))?.status === 'Attached' ? 'bg-success-500' : 'bg-warning-500'"
            />
          </button>
        </div>

        <EmptyState
          v-if="sitePortalStore.calendarReports.length === 0"
          :icon="FileText"
          title="No reports this month"
          class="mt-4"
        />
      </div>
    </Card>

    <BaseDialog v-model="isDetailOpen" :title="selectedReport?.reportNo" size="md">
      <div v-if="selectedReport" class="flex flex-col gap-3 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-neutral-500">Project</span>
          <span class="font-medium text-neutral-800">{{ selectedReport.projectName }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-neutral-500">Date</span>
          <span class="font-medium text-neutral-800">{{ selectedReport.reportDate }}</span>
        </div>
        <div v-if="selectedReport.receiptType" class="flex items-center justify-between">
          <span class="text-neutral-500">Receipt / Handover</span>
          <span class="font-medium text-neutral-800">{{ selectedReport.receiptType }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-neutral-500">Supervision</span>
          <span class="font-medium text-neutral-800">{{ selectedReport.supervisionType }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-neutral-500">Status</span>
          <StatusBadge
            :label="selectedReport.status"
            :variant="selectedReport.status === 'Attached' ? 'success' : 'warning'"
          />
        </div>
        <div>
          <p class="mb-1 text-neutral-500">Notes</p>
          <p class="whitespace-pre-wrap rounded-lg bg-bg-secondary p-3 text-neutral-800" dir="auto">{{ selectedReport.notes }}</p>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
