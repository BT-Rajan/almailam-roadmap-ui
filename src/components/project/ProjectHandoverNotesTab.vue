<script setup lang="ts">
import { FileText } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import TextArea from '@/components/common/TextArea.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { projectService } from '@/services/projectService'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project } from '@/types/Project'

const props = defineProps<{
  project: Project
}>()

const { t } = useI18n()
const router = useRouter()
const projectStore = useProjectStore()
const toastStore = useToastStore()

// Local draft, seeded from the project and re-seeded whenever a fresh
// copy loads (e.g. switching projects) -- same "edit a draft, save
// explicitly" shape as ProjectOverviewTab.vue's Scope card, not an
// autosave-on-every-keystroke field.
const notes = ref(props.project.handoverNotes ?? '')
watch(
  () => props.project.id,
  () => {
    notes.value = props.project.handoverNotes ?? ''
  },
)

const isSaving = ref(false)
const isDirty = ref(false)
watch(notes, () => {
  isDirty.value = true
})

async function handleSave(): Promise<void> {
  isSaving.value = true
  try {
    await projectService.updateHandoverNotes(props.project.id, notes.value)
    await projectStore.refreshProject(props.project.id)
    isDirty.value = false
    toastStore.show('success', t('project.handoverNotesTab.savedTitle'))
  } catch (error) {
    toastStore.show('error', t('project.handoverNotesTab.failedToSave'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}

function viewReport(): void {
  router.push({ name: ROUTE_NAMES.REPORT_PROJECT })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <Card>
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.handoverNotesTab.notesTitle') }}</h3>
      </template>
      <div class="flex flex-col gap-3">
        <TextArea
          v-model="notes"
          :placeholder="t('project.handoverNotesTab.notesPlaceholder')"
          :rows="8"
        />
        <BaseButton size="sm" :disabled="!isDirty" :loading="isSaving" class="self-start no-print" @click="handleSave">
          {{ t('project.handoverNotesTab.saveNotes') }}
        </BaseButton>
      </div>
    </Card>

    <Card>
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.handoverNotesTab.reportTitle') }}</h3>
      </template>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-sm text-text-secondary">{{ t('project.handoverNotesTab.reportDescription') }}</p>
        <BaseButton variant="secondary" size="sm" :icon="FileText" class="no-print" @click="viewReport">
          {{ t('project.handoverNotesTab.viewReport') }}
        </BaseButton>
      </div>
    </Card>
  </div>
</template>
