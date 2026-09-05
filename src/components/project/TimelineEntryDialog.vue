<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useAuthStore } from '@/stores/authStore'
import type { TimelineEvent, TimelineEventStatus } from '@/types/Timeline'
import type { SelectOption } from '@/types/Ui'
import { uuid } from '@/utils/uuid'

const authStore = useAuthStore()

const props = defineProps<{
  modelValue: boolean
  projectId: string
  event?: TimelineEvent
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [event: TimelineEvent]
}>()

const { t } = useI18n()

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'Upcoming', value: 'upcoming', labelKey: 'project.timelineEntryDialog.statusUpcoming' },
  { label: 'In Progress', value: 'in-progress', labelKey: 'project.timelineEntryDialog.statusInProgress' },
  { label: 'Completed', value: 'completed', labelKey: 'project.timelineEntryDialog.statusCompleted' },
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
    id: props.event?.id ?? `TLE-NOTE-${uuid().slice(0, 8).toUpperCase()}`,
    projectId: props.projectId,
    type: props.event?.type ?? 'note',
    title: title.value.trim(),
    description: comment.value.trim() || undefined,
    date: date.value,
    status: status.value,
    user: props.event?.user ?? authStore.user?.name ?? 'Unknown',
  }

  emit('save', savedEvent)
  closeDialog()
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="isEditMode ? t('project.timelineEntryDialog.updateStatusTitle') : t('project.timelineEntryDialog.addUpdateTitle')"
    size="md"
    @update:model-value="closeDialog"
  >
    <div class="flex flex-col gap-4">
      <TextInput v-model="title" :label="t('project.timelineEntryDialog.title')" :placeholder="t('project.timelineEntryDialog.titlePlaceholder')" required :error="titleError" />

      <SelectBox
        :model-value="status"
        :options="STATUS_OPTIONS"
        :label="t('project.timelineEntryDialog.status')"
        required
        @update:model-value="status = $event as TimelineEventStatus"
      />

      <DatePicker v-model="date" :label="t('project.timelineEntryDialog.date')" required />

      <TextArea v-model="comment" :label="t('project.timelineEntryDialog.comment')" :placeholder="t('project.timelineEntryDialog.commentPlaceholder')" :rows="3" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton @click="submit">{{ isEditMode ? t('common.saveChanges') : t('project.timelineEntryDialog.addUpdate') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
