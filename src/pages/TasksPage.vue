<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
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
import { projectService } from '@/services/projectService'
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

// Project filter: id + name only (not every full project record).
const projects = ref<{ id: string; name: string }[]>([])
const projectOptions = computed<SelectOption[]>(() => [
  { label: 'All Projects', value: 'All', labelKey: 'task.tasksPage.allProjects' },
  ...projects.value.map((project) => ({ label: project.name, value: project.id })),
])

// User ids -- the server filters the board by assignee.
const assigneeOptions = computed<SelectOption[]>(() => [
  { label: 'All Assignees', value: 'All', labelKey: 'task.tasksPage.allAssignees' },
  ...userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: user.name, value: user.id })),
])

// Each column is loaded from the server a page at a time, filtered there
// -- not every task ever created downloaded and filtered here.
function loadData(): void {
  void taskStore.loadBoard()
}

onMounted(async () => {
  loadData()
  try {
    projects.value = await projectService.getProjectOptions()
  } catch {
    projects.value = []
  }
})

function openTask(taskId: string): void {
  router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId } })
}

function advanceTask(taskId: string): void {
  const task = Object.values(taskStore.tasksByStatus).flat().find((item) => item.id === taskId)
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

    <div v-else-if="taskStore.isBoardLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
      <div v-for="placeholder in 3" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-4">
        <SkeletonLoader :rows="5" />
      </div>
    </div>

    <TaskBoard
      v-else
      :tasks-by-status="taskStore.tasksByStatus"
      :totals="taskStore.boardTotals"
      :get-project-by-id="taskStore.getProjectById"
      :get-client-name-by-project-id="taskStore.getClientNameByProjectId"
      @open="openTask"
      @advance="advanceTask"
      @load-more="taskStore.loadMoreBoard"
    />
  </div>
</template>
