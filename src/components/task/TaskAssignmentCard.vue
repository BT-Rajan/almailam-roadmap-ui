<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import Avatar from '@/components/common/Avatar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import { useUserStore } from '@/stores/userStore'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  assignedTo: string
}>()

const emit = defineEmits<{
  // A real user id (e.g. "USR-004"), not a display name -- the backend
  // resolves this to a real user server-side, so the reassignment
  // dropdown has to work in ids even though `assignedTo` itself (the
  // task's current, already-resolved assignee) is a display name.
  reassign: [assigneeUserId: string]
}>()

const { t } = useI18n()
const userStore = useUserStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})

const currentAssigneeUser = computed(() => userStore.users.find((user) => user.name === props.assignedTo))
const assigneeRole = computed(() => currentAssigneeUser.value?.designation ?? currentAssigneeUser.value?.role ?? t('task.teamMember'))

const assigneeOptions = computed<SelectOption[]>(() =>
  userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: user.name, value: user.id })),
)
</script>

<template>
  <div class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4">
    <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('task.assignmentCard.assignedTo') }}</p>

    <div class="flex items-center gap-3">
      <Avatar :name="assignedTo" size="md" />
      <div class="min-w-0">
        <p class="truncate text-sm font-semibold text-text-primary">{{ assignedTo }}</p>
        <p class="truncate text-xs text-text-muted">{{ assigneeRole }}</p>
      </div>
    </div>

    <SelectBox
      :model-value="currentAssigneeUser?.id ?? ''"
      :options="assigneeOptions"
      :label="t('task.assignmentCard.reassignTo')"
      @update:model-value="emit('reassign', $event)"
    />
  </div>
</template>
