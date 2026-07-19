<script setup lang="ts">
import { CalendarClock, FolderKanban, UserRound } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Project } from '@/types/Project'
import type { ProjectDocument } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'
import { getDocumentStatusVariant, getDocumentTypeIcon } from '@/utils/documentHelpers'

const props = defineProps<{
  document: ProjectDocument
  project?: Project
}>()

defineEmits<{
  open: [documentId: string]
}>()

const projectName = computed(() => props.project?.projectName ?? 'Unknown Project')
const typeIcon = computed(() => getDocumentTypeIcon(props.document.type))
</script>

<template>
  <Card hoverable class="cursor-pointer" @click="$emit('open', document.id)">
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <component :is="typeIcon" class="h-5 w-5 text-primary-600" />
          </span>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ document.type }} · {{ document.revision }}</p>
            <h3 class="text-base font-semibold leading-snug text-neutral-800">{{ document.title }}</h3>
          </div>
        </div>
        <StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" show-dot />
      </div>

      <div class="flex items-center gap-2 text-sm text-neutral-500">
        <FolderKanban class="h-4 w-4 shrink-0 text-neutral-400" />
        <span class="truncate">{{ projectName }}</span>
      </div>

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-neutral-500">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ document.uploadedBy }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(document.uploadDate) }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
