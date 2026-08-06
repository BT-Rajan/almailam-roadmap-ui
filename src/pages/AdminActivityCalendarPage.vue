<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { activityCalendarService, type ActivityRecord, type DailySummary, ActivityType, EntityType } from '@/services/activityCalendarService'
import { useToastStore } from '@/stores/toastStore'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'

const toastStore = useToastStore()

// View modes
type ViewMode = 'month' | 'week' | 'day' | 'list'
const viewMode = ref<ViewMode>('month')

// Date selection
const selectedDate = ref(new Date())
const currentMonth = computed(() => {
  return `${selectedDate.value.getFullYear()}-${String(selectedDate.value.getMonth() + 1).padStart(2, '0')}`
})

// Filter options
const projectOptions = ref<SelectOption[]>([])
const userOptions = ref<SelectOption[]>([])
const selectedProject = ref('')
const selectedUser = ref('')

// Activity data
const dailyActivities = ref<Map<string, DailySummary>>(new Map())
const selectedDayActivities = ref<ActivityRecord[]>([])
const selectedDateStr = ref('')
const isLoading = ref(false)
const isDetailsPanelOpen = ref(false)

// Activity type colors for badges
const activityTypeColors: Record<ActivityType, string> = {
  [ActivityType.NEW]: 'bg-green-100 text-green-800',
  [ActivityType.UPDATED]: 'bg-blue-100 text-blue-800',
  [ActivityType.DELAYED]: 'bg-red-100 text-red-800',
  [ActivityType.COMPLETED]: 'bg-emerald-100 text-emerald-800',
  [ActivityType.ASSIGNED]: 'bg-purple-100 text-purple-800',
  [ActivityType.COMMENTED]: 'bg-yellow-100 text-yellow-800',
  [ActivityType.APPROVED]: 'bg-green-100 text-green-800',
  [ActivityType.REJECTED]: 'bg-red-100 text-red-800',
}

// Initialize
onMounted(async () => {
  await loadFilterOptions()
  await loadMonthActivities()
})

async function loadFilterOptions() {
  try {
    const [projects, users] = await Promise.all([
      activityCalendarService.getProjectsForFiltering(),
      activityCalendarService.getUsersForFiltering(),
    ])

    projectOptions.value = [
      { label: 'All Projects', value: '' },
      ...projects.map((p) => ({ label: p.name, value: p.id })),
    ]

    userOptions.value = [
      { label: 'All Users', value: '' },
      ...users.map((u) => ({ label: u.name, value: u.id })),
    ]
  } catch (error) {
    console.error('Failed to load filter options:', error)
    toastStore.addError('Failed to load filter options')
  }
}

async function loadMonthActivities() {
  isLoading.value = true
  try {
    const activities = await activityCalendarService.getMonthActivity(currentMonth.value)
    dailyActivities.value.clear()
    activities.forEach((summary) => {
      dailyActivities.value.set(summary.date, summary)
    })
  } catch (error) {
    console.error('Failed to load month activities:', error)
    toastStore.addError('Failed to load activities')
  } finally {
    isLoading.value = false
  }
}

async function handleDayClick(day: number) {
  const dateStr = `${currentMonth.value}-${String(day).padStart(2, '0')}`
  selectedDateStr.value = dateStr
  const summary = dailyActivities.value.get(dateStr)

  if (summary) {
    selectedDayActivities.value = summary.activities
    isDetailsPanelOpen.value = true
  }
}

function goToPreviousMonth() {
  const current = new Date(selectedDate.value)
  current.setMonth(current.getMonth() - 1)
  selectedDate.value = current
  loadMonthActivities()
}

function goToNextMonth() {
  const current = new Date(selectedDate.value)
  current.setMonth(current.getMonth() + 1)
  selectedDate.value = current
  loadMonthActivities()
}

function goToToday() {
  selectedDate.value = new Date()
  loadMonthActivities()
}

// Get filtered activities based on selected filters
const filteredActivities = computed(() => {
  let activities = selectedDayActivities.value

  if (selectedProject.value) {
    activities = activities.filter((a) => a.projectId === selectedProject.value)
  }

  if (selectedUser.value) {
    activities = activities.filter((a) => a.userId === selectedUser.value)
  }

  return activities
})

// Get summary stats for calendar display
function getDaySummary(day: number): DailySummary | null {
  const dateStr = `${currentMonth.value}-${String(day).padStart(2, '0')}`
  return dailyActivities.value.get(dateStr) || null
}

// Calendar grid generation
const calendarDays = computed(() => {
  const [year, month] = currentMonth.value.split('-').map(Number)
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())

  const days = []
  const current = new Date(startDate)
  while (current <= lastDay || current.getDay() !== 0) {
    days.push(new Date(current))
    current.setDate(current.getDate() + 1)
  }
  return days
})

const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

async function exportToCSV() {
  try {
    const startDate = `${currentMonth.value}-01`
    const endDate = `${currentMonth.value}-31`
    const blob = await activityCalendarService.exportActivitiesCSV({
      startDate,
      endDate,
      projectId: selectedProject.value,
      userId: selectedUser.value,
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `activity-report-${currentMonth.value}.csv`
    link.click()
    URL.revokeObjectURL(url)

    toastStore.addSuccess('Activities exported successfully')
  } catch (error) {
    console.error('Failed to export activities:', error)
    toastStore.addError('Failed to export activities')
  }
}

function closeDetailsPanel() {
  isDetailsPanelOpen.value = false
  selectedDayActivities.value = []
  selectedDateStr.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <PageHeader
      title="Activity Calendar"
      subtitle="View all updates by team members across projects"
      icon="calendar"
    />

    <div class="p-6 space-y-6">
      <!-- Controls -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <!-- View Mode -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">View Mode</label>
            <SelectBox v-model="viewMode" :options="[
              { label: 'Monthly', value: 'month' },
              { label: 'Weekly', value: 'week' },
              { label: 'Daily', value: 'day' },
              { label: 'List', value: 'list' },
            ]" />
          </div>

          <!-- Project Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Project</label>
            <SelectBox v-model="selectedProject" :options="projectOptions" />
          </div>

          <!-- User Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">User</label>
            <SelectBox v-model="selectedUser" :options="userOptions" />
          </div>

          <!-- Date Picker -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Date</label>
            <input
              v-model="currentMonth"
              type="month"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- Export Button -->
          <div class="flex items-end">
            <button
              @click="exportToCSV"
              class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              📥 Export CSV
            </button>
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex justify-between items-center mt-4">
          <button
            @click="goToPreviousMonth"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
          >
            ← Previous
          </button>
          <button
            @click="goToToday"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            📅 Today
          </button>
          <button
            @click="goToNextMonth"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
          >
            Next →
          </button>
        </div>
      </div>

      <!-- Month View (Main Content) -->
      <div v-if="viewMode === 'month'" class="bg-white rounded-lg shadow overflow-hidden">
        <div class="p-6">
          <h2 class="text-2xl font-bold text-gray-900 mb-6">
            {{ formatDate(selectedDate, 'MMMM yyyy') }}
          </h2>

          <!-- Loading State -->
          <div v-if="isLoading" class="text-center py-12">
            <div class="inline-block">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
            <p class="mt-4 text-gray-600">Loading activities...</p>
          </div>

          <!-- Calendar Grid -->
          <div v-else>
            <!-- Weekday Headers -->
            <div class="grid grid-cols-7 gap-1 mb-2">
              <div
                v-for="day in weekDays"
                :key="day"
                class="text-center font-semibold text-gray-600 py-2"
              >
                {{ day }}
              </div>
            </div>

            <!-- Calendar Days -->
            <div class="grid grid-cols-7 gap-1">
              <div
                v-for="(day, index) in calendarDays"
                :key="index"
                class="aspect-square border border-gray-200 rounded-lg p-2 hover:shadow-md transition cursor-pointer relative"
                :class="{
                  'bg-gray-50': day.getMonth() !== selectedDate.getMonth(),
                  'bg-white': day.getMonth() === selectedDate.getMonth(),
                  'bg-blue-50': formatDate(day, 'yyyy-MM-dd') === formatDate(new Date(), 'yyyy-MM-dd'),
                }"
                @click="
                  () => {
                    if (day.getMonth() === selectedDate.getMonth()) {
                      handleDayClick(day.getDate())
                    }
                  }
                "
              >
                <div class="flex justify-between items-start mb-1">
                  <span
                    class="text-sm font-semibold"
                    :class="{
                      'text-gray-400': day.getMonth() !== selectedDate.getMonth(),
                      'text-gray-900': day.getMonth() === selectedDate.getMonth(),
                    }"
                  >
                    {{ day.getDate() }}
                  </span>
                  <div v-if="day.getMonth() === selectedDate.getMonth()" class="text-xs">
                    {{ getDaySummary(day.getDate())?.total || 0 }}
                  </div>
                </div>

                <!-- Activity Badges -->
                <div v-if="day.getMonth() === selectedDate.getMonth()" class="space-y-1">
                  <div v-if="getDaySummary(day.getDate())?.new" class="text-xs">
                    <span class="inline-block px-2 py-0.5 rounded bg-green-100 text-green-700 font-semibold">
                      📌 {{ getDaySummary(day.getDate())?.new }}
                    </span>
                  </div>
                  <div v-if="getDaySummary(day.getDate())?.updated" class="text-xs">
                    <span class="inline-block px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-semibold">
                      ✏️ {{ getDaySummary(day.getDate())?.updated }}
                    </span>
                  </div>
                  <div v-if="getDaySummary(day.getDate())?.delayed" class="text-xs">
                    <span class="inline-block px-2 py-0.5 rounded bg-red-100 text-red-700 font-semibold">
                      ⏰ {{ getDaySummary(day.getDate())?.delayed }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Details Panel (Side Sheet) -->
      <transition name="slide">
        <div
          v-if="isDetailsPanelOpen"
          class="fixed inset-0 bg-black/50 z-40"
          @click="closeDetailsPanel"
        ></div>
      </transition>

      <transition name="slide">
        <div
          v-if="isDetailsPanelOpen"
          class="fixed right-0 top-0 h-screen w-full sm:w-96 bg-white shadow-2xl z-50 overflow-y-auto"
        >
          <div class="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center">
            <div>
              <h3 class="text-xl font-bold text-gray-900">Activities</h3>
              <p class="text-sm text-gray-600">{{ selectedDateStr }}</p>
            </div>
            <button
              @click="closeDetailsPanel"
              class="text-gray-500 hover:text-gray-700 text-2xl leading-none"
            >
              ✕
            </button>
          </div>

          <div class="p-6 space-y-4">
            <!-- No Activities Message -->
            <div v-if="filteredActivities.length === 0" class="text-center py-8">
              <p class="text-gray-500">No activities on this day</p>
            </div>

            <!-- Activity List -->
            <div v-else class="space-y-4">
              <div v-for="activity in filteredActivities" :key="activity.id" class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <p class="font-semibold text-gray-900">{{ activity.entityName }}</p>
                    <p class="text-sm text-gray-600">{{ activity.projectName }}</p>
                  </div>
                  <span
                    :class="activityTypeColors[activity.type]"
                    class="text-xs font-semibold px-2 py-1 rounded"
                  >
                    {{ activity.type.toUpperCase() }}
                  </span>
                </div>

                <p class="text-sm text-gray-700 mb-2">{{ activity.description }}</p>

                <div class="flex justify-between text-xs text-gray-500">
                  <span>By {{ activity.userName }}</span>
                  <span>{{ formatDate(new Date(activity.timestamp), 'HH:mm') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
