<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'
import type { TaskInput } from '@/services/taskService'
import type { Project } from '@/types/Project'
import type { TaskPriority, TaskSeverity } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const SEVERITY_OPTIONS: SelectOption[] = [
  { label: 'Critical', value: 'Critical' },
  { label: 'Major', value: 'Major' },
  { label: 'Minor', value: 'Minor' },
]

const props = defineProps<{
  modelValue: boolean
  projects: Project[]
  defaultProjectId?: string
  defaultTitle?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  create: [task: TaskInput]
}>()

const authStore = useAuthStore()
const userStore = useUserStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})

const title = ref('')
const projectId = ref('')
// A real user id (e.g. "USR-004"), not a display name -- the backend
// resolves assignedTo to a real user server-side (task_service.py's
// _resolve_assignee), so sending anything else fails validation
// outright. This previously defaulted to, and only ever offered,
// five hardcoded fake names from src/constants/team.ts that didn't
// correspond to any real account -- meaning creating a task here could
// never actually succeed.
const assignedTo = ref('')
const priority = ref<TaskPriority>('Medium')
const severity = ref<TaskSeverity>('Minor')
const dueDate = ref('')
const dueTime = ref('17:00')
const titleError = ref<string>()
const dueDateError = ref<string>()

const projectOptions = computed<SelectOption[]>(() =>
  props.projects.map((project) => ({ label: project.projectName, value: project.id })),
)

const assigneeOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active')
    .map((user) => ({ label: user.id === authStore.user?.id ? `${user.name} (Me)` : user.name, value: user.id })),
)

const canSubmit = computed(
  () => title.value.trim().length > 0 && projectId.value.length > 0 && assignedTo.value.length > 0 && dueDate.value.length > 0,
)

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      projectId.value = props.defaultProjectId ?? props.projects[0]?.id ?? ''
      title.value = props.defaultTitle ?? ''
      assignedTo.value = authStore.user?.id ?? ''
    }
  },
)

function resetForm(): void {
  title.value = ''
  assignedTo.value = authStore.user?.id ?? ''
  priority.value = 'Medium'
  severity.value = 'Minor'
  dueDate.value = ''
  dueTime.value = '17:00'
  titleError.value = undefined
  dueDateError.value = undefined
}

function closeDialog(): void {
  emit('update:modelValue', false)
  resetForm()
}

function submitTask(): void {
  titleError.value = title.value.trim().length === 0 ? 'Task title is required' : undefined
  dueDateError.value = dueDate.value.length === 0 ? 'Completion date is required' : undefined
  if (!canSubmit.value) return

  emit('create', {
    projectId: projectId.value,
    title: title.value.trim(),
    assignedTo: assignedTo.value,
    priority: priority.value,
    severity: severity.value,
    dueDate: dueDate.value,
    dueTime: dueTime.value,
    status: 'Pending',
  })
  closeDialog()
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Create Task" size="md" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="title"
        label="Task Title"
        placeholder="e.g. Review structural drawings"
        required
        :error="titleError"
      />

      <SelectBox v-model="projectId" label="Project" placeholder="Select project" :options="projectOptions" required />

      <SelectBox
        :model-value="assignedTo"
        label="Assign To"
        :options="assigneeOptions"
        required
        @update:model-value="assignedTo = $event"
      />

      <div class="grid grid-cols-2 gap-4">
        <SelectBox
          :model-value="priority"
          label="Priority"
          :options="PRIORITY_OPTIONS"
          @update:model-value="priority = $event as TaskPriority"
        />
        <SelectBox
          :model-value="severity"
          label="Severity"
          :options="SEVERITY_OPTIONS"
          @update:model-value="severity = $event as TaskSeverity"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <DatePicker v-model="dueDate" label="Completion Date" required :error="dueDateError" />
        <TimePicker v-model="dueTime" label="Completion Time" required />
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" @click="submitTask">Create Task</BaseButton>
    </template>
  </BaseDialog>
</template>
