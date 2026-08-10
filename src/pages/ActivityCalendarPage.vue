<script setup lang="ts">
import { ClipboardPlus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import { useRbac } from '@/composables/useRbac'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { activityCalendarService, type ActivityRecord, type DailySummary, ActivityType, EntityType } from '@/services/activityCalendarService'
import type { TaskInput } from '@/services/taskService'
import { projectService } from '@/services/projectService'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { BadgeVariant } from '@/types/Ui'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'

const router = useRouter()
const toastStore = useToastStore()
const taskStore = useTaskStore()
const { can } = useRbac()

// Only Administrators may browse other users' activity. Everyone else only
// ever sees their own -- this flag decides which endpoints/filters are used
// below, but the actual enforcement has to live on the backend too: the
// /api/admin/activity/* endpoints this calls in admin mode must reject
// non-Administrator callers regardless of what this page sends.
const canViewAll = computed(() => can('activity.viewAll'))

// This page needs a couple of specific date formats (month/year title,
// yyyy-MM-dd date keys, HH:mm timestamps) that the shared formatDate()
// utility (src/utils/dateFormatter.ts) doesn't support -- it only takes
// an ISO string and always returns one fixed display format. Small local
// helpers here rather than changing that shared utility's contract for
// every other page that uses it.
function formatMonthTitle(date: Date): string {
  return date.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
}
function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })
}

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

// Activity type -> the site's shared badge palette (StatusBadge), not raw
// Tailwind colors, so this reads consistently with every other status
// badge in the app.
const activityTypeVariants: Record<ActivityType, BadgeVariant> = {
  [ActivityType.NEW]: 'success',
  [ActivityType.UPDATED]: 'info',
  [ActivityType.DELAYED]: 'danger',
  [ActivityType.COMPLETED]: 'success',
  [ActivityType.ASSIGNED]: 'ai',
  [ActivityType.COMMENTED]: 'warning',
  [ActivityType.APPROVED]: 'success',
  [ActivityType.REJECTED]: 'danger',
}

// Initialize
onMounted(async () => {
  await loadFilterOptions()
  await loadMonthActivities()
})

async function loadFilterOptions() {
  try {
    if (canViewAll.value) {
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
    } else {
      // Non-admins only filter within their own projects -- reuse the
      // regular projects list (already scoped server-side to what this
      // user can see) rather than the admin-only filter endpoint. No user
      // dropdown at all: this page never shows anyone else's activity.
      const page = await projectService.getProjectsPage({ pageSize: 200 })
      projectOptions.value = [
        { label: 'All Projects', value: '' },
        ...page.items.map((p: Project) => ({ label: p.projectName, value: p.id })),
      ]
    }
  } catch (error) {
    console.error('Failed to load filter options:', error)
    toastStore.show('error', 'Failed to load filter options')
  }
}

async function loadMonthActivities() {
  isLoading.value = true
  try {
    const activities = canViewAll.value
      ? await activityCalendarService.getMonthActivity(currentMonth.value)
      : await activityCalendarService.getMyMonthActivity(currentMonth.value)
    dailyActivities.value.clear()
    activities.forEach((summary) => {
      dailyActivities.value.set(summary.date, summary)
    })
  } catch (error) {
    console.error('Failed to load month activities:', error)
    toastStore.show('error', 'Failed to load activities')
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

  if (canViewAll.value && selectedUser.value) {
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

    toastStore.show('success', 'Activities exported successfully')
  } catch (error) {
    console.error('Failed to export activities:', error)
    toastStore.show('error', 'Failed to export activities')
  }
}

function closeDetailsPanel() {
  isDetailsPanelOpen.value = false
  selectedDayActivities.value = []
  selectedDateStr.value = ''
}

// --- Task Management integration -----------------------------------------
// Every activity either already IS a task, or can spin one off. Both paths
// go through the exact same store/components as the Task Board at /tasks
// (see TasksPage.vue) rather than a parallel implementation here, so
// editing status/priority/severity or creating a task behaves identically
// wherever it's opened from.

const tasksLoaded = ref(false)
async function ensureTasksLoaded() {
  if (tasksLoaded.value) return
  await taskStore.loadTasks()
  tasksLoaded.value = true
}

const isTaskDrawerOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
})

const selectedTaskProjectName = computed(
  () => taskStore.getProjectById(taskStore.selectedTask?.projectId ?? '')?.projectName ?? 'Unknown Project',
)

const isCreateTaskDialogOpen = ref(false)
const createTaskDefaultProjectId = ref<string>()
const createTaskDefaultTitle = ref<string>()

async function handleActivityClick(activity: ActivityRecord) {
  if (activity.entityType === EntityType.TASK) {
    await ensureTasksLoaded()
    if (taskStore.tasks.some((task) => task.id === activity.entityId)) {
      taskStore.selectTask(activity.entityId)
      return
    }
  }
  // Not a task, or the task couldn't be found (e.g. deleted) -- offer to
  // spin up a follow-up task from this activity instead.
  await ensureTasksLoaded()
  createTaskDefaultProjectId.value = activity.projectId
  createTaskDefaultTitle.value = activity.description || activity.entityName
  isCreateTaskDialogOpen.value = true
}

function handleStatusChange(status: Parameters<typeof taskStore.updateTaskStatus>[1]): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskStatus(taskStore.selectedTaskId, status)
}
function handlePriorityChange(priority: Parameters<typeof taskStore.updateTaskPriority>[1]): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskPriority(taskStore.selectedTaskId, priority)
}
function handleSeverityChange(severity: Parameters<typeof taskStore.updateTaskSeverity>[1]): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskSeverity(taskStore.selectedTaskId, severity)
}
function handleReassign(assignee: string): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
}

async function handleCreateTask(input: TaskInput): Promise<void> {
  const task = await taskStore.createTask(input)
  toastStore.show('success', 'Task created', `"${task.title}" was assigned to ${task.assignedTo}.`)
}
</script>

<template>
  <div class="min-h-screen">
    <PageHeader
      title="Activity Calendar"
      :subtitle="canViewAll ? 'View all updates by team members across projects' : 'View your updates across projects'"
    >
      <template #actions>
        <BaseButton variant="secondary" @click="router.push({ name: ROUTE_NAMES.TASKS })">
          Open Task Board
        </BaseButton>
      </template>
    </PageHeader>

    <div class="mt-6 flex flex-col gap-6">
      <!-- Controls -->
      <Card>
        <div
          class="grid grid-cols-1 gap-4"
          :class="canViewAll ? 'md:grid-cols-3 lg:grid-cols-5' : 'md:grid-cols-2 lg:grid-cols-3'"
        >
          <!-- View Mode -->
          <SelectBox
            v-model="viewMode"
            label="View Mode"
            :options="[
              { label: 'Monthly', value: 'month' },
              { label: 'Weekly', value: 'week' },
              { label: 'Daily', value: 'day' },
              { label: 'List', value: 'list' },
            ]"
          />

          <!-- Project Filter -->
          <SelectBox v-model="selectedProject" label="Project" placeholder="All Projects" :options="projectOptions" />

          <!-- User Filter (Administrators only -- everyone else only ever sees their own activity) -->
          <SelectBox
            v-if="canViewAll"
            v-model="selectedUser"
            label="User"
            placeholder="All Users"
            :options="userOptions"
          />

          <!-- Date Picker -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-neutral-700">Date</label>
            <input
              v-model="currentMonth"
              type="month"
              class="h-10 w-full rounded-lg border border-border-default bg-bg-card px-3 text-sm text-neutral-800 transition-colors duration-fast focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/30"
            />
          </div>

          <!-- Export Button (Administrators only) -->
          <div v-if="canViewAll" class="flex items-end">
            <BaseButton full-width @click="exportToCSV">Export CSV</BaseButton>
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="mt-4 flex items-center justify-between">
          <BaseButton variant="secondary" @click="goToPreviousMonth">← Previous</BaseButton>
          <BaseButton @click="goToToday">Today</BaseButton>
          <BaseButton variant="secondary" @click="goToNextMonth">Next →</BaseButton>
        </div>
      </Card>

      <!-- Month View (Main Content) -->
      <Card v-if="viewMode === 'month'" :padded="false">
        <div class="p-6">
          <h2 class="mb-6 text-2xl font-semibold text-neutral-800">
            {{ formatMonthTitle(selectedDate) }}
          </h2>

          <!-- Loading State -->
          <div v-if="isLoading" class="grid grid-cols-7 gap-1">
            <div v-for="cell in 35" :key="cell" class="aspect-square rounded-lg bg-bg-secondary animate-pulse" />
          </div>

          <!-- Calendar Grid -->
          <div v-else>
            <!-- Weekday Headers -->
            <div class="mb-2 grid grid-cols-7 gap-1">
              <div v-for="day in weekDays" :key="day" class="py-2 text-center text-sm font-semibold text-neutral-500">
                {{ day }}
              </div>
            </div>

            <!-- Calendar Days -->
            <div class="grid grid-cols-7 gap-1">
              <div
                v-for="(day, index) in calendarDays"
                :key="index"
                class="relative aspect-square cursor-pointer rounded-lg border border-border-light p-2 transition-shadow duration-fast hover:shadow-glass-sm"
                :class="{
                  'bg-bg-secondary': day.getMonth() !== selectedDate.getMonth(),
                  'bg-bg-card': day.getMonth() === selectedDate.getMonth() && formatDateKey(day) !== formatDateKey(new Date()),
                  'bg-accent-500/10 border-accent-400': formatDateKey(day) === formatDateKey(new Date()),
                }"
                @click="
                  () => {
                    if (day.getMonth() === selectedDate.getMonth()) {
                      handleDayClick(day.getDate())
                    }
                  }
                "
              >
                <div class="mb-1 flex items-start justify-between">
                  <span
                    class="text-sm font-semibold"
                    :class="day.getMonth() !== selectedDate.getMonth() ? 'text-neutral-400' : 'text-neutral-800'"
                  >
                    {{ day.getDate() }}
                  </span>
                  <span v-if="day.getMonth() === selectedDate.getMonth()" class="text-xs text-neutral-400">
                    {{ getDaySummary(day.getDate())?.total || 0 }}
                  </span>
                </div>

                <!-- Activity Badges -->
                <div v-if="day.getMonth() === selectedDate.getMonth()" class="flex flex-col gap-1">
                  <StatusBadge
                    v-if="getDaySummary(day.getDate())?.new"
                    size="sm"
                    variant="success"
                    :label="`${getDaySummary(day.getDate())?.new} new`"
                  />
                  <StatusBadge
                    v-if="getDaySummary(day.getDate())?.updated"
                    size="sm"
                    variant="info"
                    :label="`${getDaySummary(day.getDate())?.updated} updated`"
                  />
                  <StatusBadge
                    v-if="getDaySummary(day.getDate())?.delayed"
                    size="sm"
                    variant="danger"
                    :label="`${getDaySummary(day.getDate())?.delayed} delayed`"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- Other view modes not yet built out -- Monthly is the only one currently backed by data. -->
      <Card v-else>
        <EmptyState title="Coming soon" :description="`The ${viewMode} view isn't available yet -- switch to Monthly.`" />
      </Card>
    </div>

    <!-- Day Activity Details -->
    <BaseDrawer v-model="isDetailsPanelOpen" :title="selectedDateStr" width="md" @close="closeDetailsPanel">
      <div v-if="filteredActivities.length === 0">
        <EmptyState title="No activities on this day" />
      </div>

      <div v-else class="flex flex-col gap-3">
        <Card
          v-for="activity in filteredActivities"
          :key="activity.id"
          hoverable
          class="cursor-pointer"
          @click="handleActivityClick(activity)"
        >
          <div class="flex items-start justify-between gap-2">
            <div>
              <p class="font-semibold text-neutral-800">{{ activity.entityName }}</p>
              <p class="text-sm text-neutral-500">{{ activity.projectName }}</p>
            </div>
            <StatusBadge :variant="activityTypeVariants[activity.type]" :label="activity.type.toUpperCase()" />
          </div>

          <p class="mt-2 text-sm text-neutral-700">{{ activity.description }}</p>

          <div class="mt-2 flex items-center justify-between text-xs text-neutral-400">
            <span v-if="canViewAll">By {{ activity.userName }}</span>
            <span>{{ formatTime(new Date(activity.timestamp)) }}</span>
          </div>

          <div class="mt-3 flex items-center gap-1.5 text-xs font-medium text-primary-600">
            <template v-if="activity.entityType === EntityType.TASK">
              View task details
            </template>
            <template v-else>
              <ClipboardPlus class="h-3.5 w-3.5" />
              Create follow-up task
            </template>
          </div>
        </Card>
      </div>
    </BaseDrawer>

    <!-- Task Details -- identical flow to the Task Board at /tasks (TasksPage.vue) -->
    <BaseDrawer v-model="isTaskDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
      <TaskDetails
        v-if="taskStore.selectedTask"
        :task="taskStore.selectedTask"
        :project-name="selectedTaskProjectName"
        @status-change="handleStatusChange"
        @priority-change="handlePriorityChange"
        @severity-change="handleSeverityChange"
        @reassign="handleReassign"
      />
    </BaseDrawer>

    <!-- Create Task -- identical flow to the Task Board at /tasks (TasksPage.vue) -->
    <TaskFormDialog
      v-model="isCreateTaskDialogOpen"
      :projects="taskStore.projects"
      :default-project-id="createTaskDefaultProjectId"
      :default-title="createTaskDefaultTitle"
      @create="handleCreateTask"
    />
  </div>
</template>
