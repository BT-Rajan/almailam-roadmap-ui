<script setup lang="ts">
import { computed } from 'vue'

import Avatar from '@/components/common/Avatar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import { TEAM_MEMBERS } from '@/constants/team'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  assignedTo: string
}>()

const emit = defineEmits<{
  reassign: [assignee: string]
}>()

const assigneeRole = computed(
  () => TEAM_MEMBERS.find((member) => member.name === props.assignedTo)?.role ?? 'Team Member',
)

const assigneeOptions = computed<SelectOption[]>(() =>
  TEAM_MEMBERS.map((member) => ({ label: member.name, value: member.name })),
)
</script>

<template>
  <div class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4">
    <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Assigned To</p>

    <div class="flex items-center gap-3">
      <Avatar :name="assignedTo" size="md" />
      <div class="min-w-0">
        <p class="truncate text-sm font-semibold text-neutral-800">{{ assignedTo }}</p>
        <p class="truncate text-xs text-neutral-500">{{ assigneeRole }}</p>
      </div>
    </div>

    <SelectBox
      :model-value="assignedTo"
      :options="assigneeOptions"
      label="Reassign to"
      @update:model-value="emit('reassign', $event)"
    />
  </div>
</template>
