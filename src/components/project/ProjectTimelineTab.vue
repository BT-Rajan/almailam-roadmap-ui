<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ProjectTimeline from '@/components/project/ProjectTimeline.vue'
import TimelineEntryDialog from '@/components/project/TimelineEntryDialog.vue'
import { useTimelineStore } from '@/stores/timelineStore'
import type { TimelineEvent } from '@/types/Timeline'

const props = defineProps<{
  events: TimelineEvent[]
  projectId: string
}>()

const timelineStore = useTimelineStore()

const isDialogOpen = ref(false)
const editingEvent = ref<TimelineEvent | undefined>(undefined)

function openAdd(): void {
  editingEvent.value = undefined
  isDialogOpen.value = true
}

function openEdit(event: TimelineEvent): void {
  editingEvent.value = event
  isDialogOpen.value = true
}

function handleSave(event: TimelineEvent): void {
  if (editingEvent.value) {
    void timelineStore.saveEventUpdate(props.projectId, event.id, {
      title: event.title,
      description: event.description,
      status: event.status,
      date: event.date,
    })
  } else {
    void timelineStore.createEvent(props.projectId, {
      title: event.title,
      description: event.description,
      status: event.status,
      date: event.date,
    })
  }
}
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton variant="secondary" size="sm" :icon="Plus" class="no-print" @click="openAdd">
      Add Update
    </BaseButton>
  </div>
  <ProjectTimeline :events="events" editable @edit="openEdit" />

  <TimelineEntryDialog
    v-model="isDialogOpen"
    :project-id="props.projectId"
    :event="editingEvent"
    @save="handleSave"
  />
</template>
