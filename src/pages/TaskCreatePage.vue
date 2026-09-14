<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { TaskPriority, TaskSeverity } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

// Replaces TaskFormDialog.vue's modal -- a dedicated route (/tasks/new)
// like NewProjectWizardPage/NewClientWizardPage, instead of a popup.
// TasksPage, MyTasksPage, ProjectTasksTab, and ActivityCalendarPage all
// navigate here now instead of opening a dialog.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const authStore = useAuthStore()
const userStore = useUserStore()
const clientStore = useClientStore()
const taskStore = useTaskStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))

// ?projectId= prefills the project field everywhere it's passed
// (e.g. ActivityCalendarPage's "create a follow-up task" flow).
// ?locked=1 additionally restricts the Project field to just that one
// project and hides it from being changed -- ProjectTasksTab.vue's own
// "Add Task" button always did this (it only ever passed a single-item
// project list), since a task added from inside one project's own
// Tasks tab shouldn't quietly end up filed under a different project.
const queryProjectId = computed(() => {
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
const isProjectLocked = computed(() => route.query.locked === '1')
const queryTitle = computed(() => {
  const value = route.query.title
  return typeof value === 'string' ? value : undefined
})

onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
  if (clientStore.clients.length === 0) clientStore.loadClients()
  if (taskStore.projects.length === 0) taskStore.loadTasks()
  title.value = queryTitle.value ?? ''
  projectId.value = queryProjectId.value ?? ''
  assignedTo.value = authStore.user?.id ?? ''
})

const title = ref('')
const projectId = ref('')
// A real user id (e.g. "USR-004"), not a display name -- the backend
// resolves assignedTo to a real user server-side (task_service.py's
// _resolve_assignee), so sending anything else fails validation
// outright.
const assignedTo = ref('')
const priority = ref<TaskPriority>('Medium')
const severity = ref<TaskSeverity>('Minor')
const startDate = ref('')
const dueDate = ref('')
const dueTime = ref('17:00')
// Optional -- links this task to one of the chosen project's own
// Design activities, so closing every task linked to it can auto-close
// the activity (see project_service.maybe_auto_close_design_activity).
const selectedActivityId = ref('')
const titleError = ref<string>()
const projectError = ref<string>()
const assignedToError = ref<string>()
const dueDateError = ref<string>()
const startDateError = ref<string>()
const isSubmitting = ref(false)

const availableProjects = computed(() => {
  if (isProjectLocked.value) {
    return taskStore.projects.filter((project) => project.id === queryProjectId.value)
  }
  return taskStore.projects
})

const projectOptions = computed<SelectOption[]>(() =>
  availableProjects.value.map((project) => ({ label: project.projectName, value: project.id })),
)

const selectedProject = computed(() => taskStore.projects.find((project) => project.id === projectId.value))

const designActivityOptions = computed<SelectOption[]>(() =>
  (selectedProject.value?.selectedActivities ?? [])
    .filter((activity) => activity.id)
    .map((activity) => ({ label: activity.activityName, value: activity.id as string })),
)

// Every task must belong to exactly one project, and through it, one
// client -- resolving and showing the client here (read-only) as soon
// as a project is picked makes that tagging visible to whoever is
// creating the task, rather than leaving the client implicit.
const selectedClientName = computed<string | undefined>(() => {
  const project = taskStore.projects.find((item) => item.id === projectId.value)
  if (!project) return undefined
  return clientStore.getClientById(project.clientId)?.companyName ?? t('task.formDialog.unknownClient')
})

const assigneeOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active')
    .map((user) => ({
      label: user.id === authStore.user?.id ? t('task.formDialog.assigneeMe', { name: user.name }) : user.name,
      value: user.id,
    })),
)

function goBack(): void {
  if (isProjectLocked.value && queryProjectId.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: queryProjectId.value } })
    return
  }
  router.push({ name: ROUTE_NAMES.TASKS })
}

async function submitTask(): Promise<void> {
  titleError.value = title.value.trim().length === 0 ? t('task.formDialog.titleRequired') : undefined
  projectError.value = projectId.value.length === 0 ? t('task.formDialog.projectRequired') : undefined
  assignedToError.value = assignedTo.value.length === 0 ? t('task.formDialog.assigneeRequired') : undefined
  dueDateError.value = dueDate.value.length === 0 ? t('task.formDialog.dueDateRequired') : undefined
  startDateError.value =
    startDate.value && dueDate.value && startDate.value > dueDate.value ? t('task.formDialog.startDateAfterDueDate') : undefined
  if (titleError.value || projectError.value || assignedToError.value || dueDateError.value || startDateError.value) return

  isSubmitting.value = true
  try {
    const task = await taskStore.createTask({
      projectId: projectId.value,
      title: title.value.trim(),
      assignedTo: assignedTo.value,
      priority: priority.value,
      severity: severity.value,
      startDate: startDate.value || undefined,
      dueDate: dueDate.value,
      dueTime: dueTime.value,
      status: 'Pending',
      selectedActivityId: selectedActivityId.value || undefined,
    })
    toastStore.show('success', t('task.taskActions.taskCreatedTitle'), t('task.taskActions.taskCreatedDescription', { title: task.title, assignee: task.assignedTo }))
    router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId: task.id } })
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToCreateTask'), detail)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ isProjectLocked ? t('task.workspace.backToProject') : t('task.workspace.backToTasks') }}
    </BaseButton>

    <div class="max-w-2xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('task.formDialog.title') }}</h1>

      <div class="flex flex-col gap-4">
        <TextInput
          v-model="title"
          :label="t('task.formDialog.taskTitle')"
          :placeholder="t('task.formDialog.taskTitlePlaceholder')"
          required
          :error="titleError"
        />

        <SelectBox
          v-model="projectId"
          :label="t('task.formDialog.project')"
          :placeholder="t('task.formDialog.projectPlaceholder')"
          :options="projectOptions"
          required
          :disabled="isProjectLocked"
          :error="projectError"
        />
        <p v-if="selectedClientName" class="-mt-2 text-xs text-text-muted">{{ t('task.formDialog.client', { name: selectedClientName }) }}</p>

        <SelectBox
          v-if="designActivityOptions.length > 0"
          v-model="selectedActivityId"
          :label="t('task.formDialog.designActivity')"
          :placeholder="t('task.formDialog.designActivityPlaceholder')"
          :options="designActivityOptions"
        />

        <SelectBox
          :model-value="assignedTo"
          :label="t('task.formDialog.assignTo')"
          :options="assigneeOptions"
          required
          :error="assignedToError"
          @update:model-value="assignedTo = $event"
        />

        <DatePicker v-model="startDate" :label="t('task.formDialog.startDate')" :max="dueDate || undefined" :error="startDateError" />

        <div class="grid grid-cols-2 gap-4">
          <DatePicker v-model="dueDate" :label="t('task.formDialog.completionDate')" required :min="startDate || undefined" :error="dueDateError" />
          <TimePicker v-model="dueTime" :label="t('task.formDialog.completionTime')" required />
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="submitTask">{{ t('task.formDialog.createTask') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
