<script setup lang="ts">
import Alert from '@/components/common/Alert.vue'
import type { ClientDuplicateMatch } from '@/types/Client'
import { getClientDisplayName } from '@/utils/clientHelpers'

defineProps<{
  matches: ClientDuplicateMatch[]
}>()

defineEmits<{
  view: [clientId: string]
}>()
</script>

<template>
  <div v-if="matches.length > 0" class="flex flex-col gap-2">
    <Alert
      variant="warning"
      title="Possible existing client found"
      :description="`This client may already exist in the system. Review the matches below before creating a new profile.`"
    />
    <ul class="flex flex-col gap-2">
      <li
        v-for="match in matches"
        :key="match.client.id"
        class="flex items-center justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-4 py-2.5"
      >
        <div class="flex flex-col">
          <span class="text-sm font-medium text-neutral-800">{{ getClientDisplayName(match.client) }}</span>
          <span class="text-xs text-neutral-500">Matched on {{ match.matchedOn.join(', ') }} · {{ match.client.code }}</span>
        </div>
        <button
          type="button"
          class="text-xs font-medium text-primary-600 hover:text-primary-700"
          @click="$emit('view', match.client.id)"
        >
          View Profile
        </button>
      </li>
    </ul>
  </div>
</template>
