<script setup lang="ts">
import { CheckCircle2, Save } from '@lucide/vue'
import { onMounted, reactive, ref, watch } from 'vue'

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
    await Promise.all([sitePortalStore.loadProjects(), sitePortalStore.loadTodaysReport()])
    projectOptions.value = sitePortalStore.projects.map((p) => ({ label: p.projectName, value: p.id }))
  } finally {
    isLoading.value = false
  }
})

// Pre-fill the form whenever today's report loads or changes (e.g. right
// after saving) -- this is what makes the page double as both "file" (no
// report yet, form starts blank) and "edit" (report exists, form shows
// what's already there) without two separate screens.
watch(
  () => sitePortalStore.todaysReport,
  (report) => {
    if (!report) return
    form.projectId = report.projectId
    form.receiptType = report.receiptType ?? ''
    form.supervisionType = report.supervisionType
    form.notes = report.notes
  },
  { immediate: true },
)

const isLocked = () => sitePortalStore.todaysReport?.status === 'Attached'

async function handleSubmit(): Promise<void> {
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
      <h1 class="text-lg font-semibold text-neutral-900">Today's Status Report</h1>
      <p class="text-sm text-neutral-500">{{ todaysDate }}</p>
    </div>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <template v-else>
      <Alert
        v-if="isLocked()"
        variant="success"
        title="Reviewed"
        description="This report has already been reviewed and attached to the project. It can no longer be edited."
      />

      <Card>
        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <SelectBox
            v-model="form.projectId"
            label="Project"
            placeholder="Select project"
            required
            :disabled="isLocked()"
            :options="projectOptions"
          />
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
            Save Report
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
