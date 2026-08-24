<script setup lang="ts">
import { CheckCircle2, Save } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useSitePortalStore } from '@/stores/sitePortalStore'
import { useToastStore } from '@/stores/toastStore'
import type { SelectOption } from '@/types/Ui'

const sitePortalStore = useSitePortalStore()
const toastStore = useToastStore()
const resultDialogStore = useResultDialogStore()

const isLoading = ref(true)
const isSaving = ref(false)

const form = reactive({
  projectId: '',
  receiptType: '',
  supervisionType: 'Full-time' as 'Full-time' | 'Part-time',
  notes: '',
})

const projectOptions = ref<SelectOption[]>([])
const supervisionOptions: SelectOption[] = [
  { label: 'Full-time', value: 'Full-time' },
  { label: 'Part-time', value: 'Part-time' },
]

const todaysDate = new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

onMounted(async () => {
  try {
    await Promise.all([sitePortalStore.loadProjects(), sitePortalStore.loadTodaysReports()])
    projectOptions.value = sitePortalStore.projects.map((p) => ({ label: p.projectName, value: p.id }))
    // Default to the first not-yet-filed project so the common case
    // (an engineer opening the page to file whatever's still
    // outstanding) doesn't require an extra selection -- falls back to
    // the first project at all if everything's already filed today.
    const firstUnfiled = sitePortalStore.projects.find((p) => !sitePortalStore.todaysReports[p.id])
    form.projectId = (firstUnfiled ?? sitePortalStore.projects[0])?.id ?? ''
  } finally {
    isLoading.value = false
  }
})

// The report for whichever project is currently selected -- an engineer
// on several projects files one report per project per day, so "today's
// report" depends entirely on which project is picked above.
const currentReport = computed(() => sitePortalStore.todaysReports[form.projectId])

// Pre-fills (or clears, for a project with nothing filed yet) the rest
// of the form whenever the selected project changes -- this is what
// makes the page double as both "file" (no report yet for this
// project, form starts blank) and "edit" (report already exists for
// this project, form shows what's already there), per project, without
// separate screens for each.
watch(
  () => form.projectId,
  (projectId) => {
    const report = projectId ? sitePortalStore.todaysReports[projectId] : undefined
    form.receiptType = report?.receiptType ?? ''
    form.supervisionType = report?.supervisionType ?? 'Full-time'
    form.notes = report?.notes ?? ''
  },
  { immediate: true },
)

const isLocked = () => currentReport.value?.status === 'Attached'

const filedCount = computed(() => Object.keys(sitePortalStore.todaysReports).length)

async function handleSubmit(): Promise<void> {
  // Native form submission (Enter key) is a separate trigger path from
  // BaseButton's click handler -- its own click-level guard doesn't cover
  // this, so the re-entrancy check has to live here too.
  if (isSaving.value) return

  if (!form.projectId) {
    toastStore.show('error', 'Project is required', 'Please select which project this report is for.')
    return
  }
  if (!form.notes.trim()) {
    toastStore.show('error', 'Notes are required', 'Please describe today\'s supervision activity.')
    return
  }

  isSaving.value = true
  try {
    await sitePortalStore.fileTodaysReport({
      projectId: form.projectId,
      receiptType: form.receiptType.trim() || undefined,
      supervisionType: form.supervisionType,
      notes: form.notes.trim(),
    })
    resultDialogStore.showSuccess('Report saved', "Today's status report has been filed.")
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to save report', detail)
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div>
      <h1 class="text-lg font-semibold text-text-primary">Today's Status Report</h1>
      <p class="text-sm text-text-muted">{{ todaysDate }}</p>
    </div>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <template v-else>
      <p v-if="sitePortalStore.projects.length > 1" class="text-xs text-text-muted">
        {{ filedCount }} of {{ sitePortalStore.projects.length }} projects reported today
      </p>

      <Alert
        v-if="isLocked()"
        variant="success"
        title="Reviewed"
        description="This project's report has already been reviewed and attached. It can no longer be edited."
      />

      <Card>
        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div>
            <SelectBox
              v-model="form.projectId"
              label="Project"
              placeholder="Select project"
              required
              :options="projectOptions"
            />
            <!-- Per-project filed/pending indicator -- an engineer on
                 several projects needs to see, right where they're
                 picking a project, whether this one still needs today's
                 report or is already done. -->
            <p v-if="form.projectId" class="mt-1.5 flex items-center gap-1.5 text-xs">
              <template v-if="currentReport">
                <CheckCircle2 class="h-3.5 w-3.5 text-success-600" />
                <span class="text-success-600">Today's report filed for this project{{ isLocked() ? ' and reviewed' : '' }}</span>
              </template>
              <span v-else class="text-warning-600">No report filed yet for this project today</span>
            </p>
          </div>

          <TextInput
            v-model="form.receiptType"
            label="Receipt / Handover"
            placeholder="e.g. First floor roof slab"
            :disabled="isLocked()"
          />
          <SelectBox
            v-model="form.supervisionType"
            label="Supervision Type"
            :disabled="isLocked()"
            :options="supervisionOptions"
          />
          <TextArea
            v-model="form.notes"
            label="Notes"
            placeholder="Describe today's supervision activity..."
            :rows="8"
            required
            :disabled="isLocked()"
          />

          <BaseButton v-if="!isLocked()" type="submit" :icon="Save" :loading="isSaving" full-width>
            {{ currentReport ? 'Update Report' : 'Save Report' }}
          </BaseButton>
          <div v-else class="flex items-center justify-center gap-2 rounded-lg bg-success-50 py-2.5 text-sm font-medium text-success-700">
            <CheckCircle2 class="h-4 w-4" />
            Filed and reviewed
          </div>
        </form>
      </Card>
    </template>
  </div>
</template>
