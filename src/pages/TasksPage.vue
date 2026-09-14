<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskBoard from '@/components/task/TaskBoard.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useTaskStore } from '@/stores/taskStore'
import { useUserStore } from '@/stores/userStore'
import { getNextTaskStatus } from '@/utils/taskHelpers'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()
const router = useRouter()
const taskStore = useTaskStore()
const userStore = useUserStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})

const projectOptions = computed<SelectOption[]>(() => [
  { label: 'All Projects', value: 'All', labelKey: 'task.tasksPage.allProjects' },
  ...taskStore.projects.map((project) => ({ label: project.projectName, value: project.id })),
])

// Values here are display names, not user ids -- this only filters the
// already-loaded task list client-side (taskStore.filteredTasks
// compares task.assignedTo, which is always a resolved name), unlike
// TaskCreatePage/TaskAssignmentCard which write an assignment back to
// the backend and need real ids for that.
const assigneeOptions = computed<SelectOption[]>(() => [
  { label: 'All Assignees', value: 'All', labelKey: 'task.tasksPage.allAssignees' },
  ...userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: user.name, value: user.name })),
])

function loadData(): void {
  taskStore.loadTasks()
}

onMounted(() => {
  if (taskStore.tasks.length === 0) loadData()
})

function openTask(taskId: string): void {
  router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId } })
}

function advanceTask(taskId: string): void {
  const task = taskStore.tasks.find((item) => item.id === taskId)
  if (!task) return
  const next = getNextTaskStatus(task.status)
  if (next) taskStore.updateTaskStatus(taskId, next)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader :title="t('task.tasksPage.title')" :subtitle="t('task.tasksPage.subtitle')">
      <template #actions>
        <BaseButton variant="secondary" @click="router.push({ name: ROUTE_NAMES.MY_TASKS })">
          {{ t('task.tasksPage.myTasks') }}
        </BaseButton>
        <BaseButton :icon="Plus" @click="router.push({ name: ROUTE_NAMES.TASK_CREATE })">{{ t('task.tasksPage.addTask') }}</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :show-search="false"
      :has-active-filters="taskStore.hasActiveFilters"
      @clear="taskStore.clearFilters"
    >
      <template #filters>
        <div class="w-56">
          <SelectBox
            :model-value="taskStore.projectFilter"
            :options="projectOptions"
            @update:model-value="taskStore.setProjectFilter($event)"
          />
        </div>
        <div class="w-48">
          <SelectBox
            :model-value="taskStore.assigneeFilter"
            :options="assigneeOptions"
            @update:model-value="taskStore.setAssigneeFilter($event)"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="taskStore.error" :description="taskStore.error" @retry="loadData" />

    <div v-else-if="taskStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
      <div v-for="placeholder in 3" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-4">
        <SkeletonLoader :rows="5" />
      </div>
    </div>

    <TaskBoard
      v-else
      :tasks-by-status="taskStore.tasksByStatus"
      :get-project-by-id="taskStore.getProjectById"
      :get-client-name-by-project-id="taskStore.getClientNameByProjectId"
      @open="openTask"
      @advance="advanceTask"
    />
  </div>
</template>
