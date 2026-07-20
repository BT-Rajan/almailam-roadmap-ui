<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CURRENT_USER_NAME } from '@/constants/team'
import type { TimelineEvent, TimelineEventStatus } from '@/types/Timeline'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  modelValue: boolean
  projectId: string
  event?: TimelineEvent
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [event: TimelineEvent]
}>()

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'Upcoming', value: 'upcoming' },
  { label: 'In Progress', value: 'in-progress' },
  { label: 'Completed', value: 'completed' },
]

const title = ref('')
const status = ref<TimelineEventStatus>('upcoming')
const date = ref('')
const comment = ref('')
const titleError = ref<string>()

const isEditMode = computed(() => Boolean(props.event))

function resetForm(): void {
  title.value = props.event?.title ?? ''
  status.value = props.event?.status ?? 'upcoming'
  date.value = props.event?.date ?? new Date().toISOString().slice(0, 10)
  comment.value = props.event?.description ?? ''
  titleError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function submit(): void {
  if (title.value.trim().length === 0) {
    titleError.value = 'Title is required'
    return
  }

  const savedEvent: TimelineEvent = {
    id: props.event?.id ?? `TLE-NOTE-${crypto.randomUUID().slice(0, 8).toUpperCase()}`,
    projectId: props.projectId,
    type: props.event?.type ?? 'note',
    title: title.value.trim(),
    description: comment.value.trim() || undefined,
    date: date.value,
    status: status.value,
    user: props.event?.user ?? CURRENT_USER_NAME,
  }

  emit('save', savedEvent)
  closeDialog()
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="isEditMode ? 'Update Status' : 'Add Timeline Update'"
    size="md"
    @update:model-value="closeDialog"
  >
    <div class="flex flex-col gap-4">
      <TextInput v-model="title" label="Title" placeholder="e.g. Site inspection completed" required :error="titleError" />

      <SelectBox
        :model-value="status"
        :options="STATUS_OPTIONS"
        label="Status"
        required
        @update:model-value="status = $event as TimelineEventStatus"
      />

      <DatePicker v-model="date" label="Date" required />

      <TextArea v-model="comment" label="Comment" placeholder="Add any notes about this update" :rows="3" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton @click="submit">{{ isEditMode ? 'Save Changes' : 'Add Update' }}</BaseButton>
    </template>
  </BaseDialog>
</template>
