<script setup lang="ts">
import { CheckCircle2, MessageSquare } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import ScopeRevisionHistory from '@/components/project/ScopeRevisionHistory.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { projectService } from '@/services/projectService'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { Project, ProjectWorkspaceTabKey, ScopeOfWork, ScopeRevision } from '@/types/Project'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'
import { triggerBlobDownload } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const router = useRouter()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const isLoading = ref(false)
const error = ref<string>()
const scopeOfWork = ref<ScopeOfWork>()

const scopeDraft = ref('')
const summaryDraft = ref('')
const selectedFile = ref<File>()
const isSaving = ref(false)
const isApproving = ref(false)

async function load(): Promise<void> {
  isLoading.value = true
  error.value = undefined
  try {
    scopeOfWork.value = await projectService.getScopeOfWork(props.project.id)
    scopeDraft.value = scopeOfWork.value.description ?? ''
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load scope of work.'
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
watch(() => props.project.id, load)

const hasTextChanged = computed(() => scopeDraft.value.trim() !== (scopeOfWork.value?.description ?? '').trim())
const canSave = computed(() => scopeDraft.value.trim().length > 0 && (hasTextChanged.value || Boolean(selectedFile.value)))
const canApprove = computed(
  () => scopeOfWork.value?.scopeStatus === 'Draft' && (scopeOfWork.value?.description ?? '').trim().length > 0 && !hasTextChanged.value,
)

async function handleSave(): Promise<void> {
  isSaving.value = true
  try {
    scopeOfWork.value = await projectService.saveScopeOfWork(
      props.project.id,
      scopeDraft.value.trim(),
      summaryDraft.value.trim() || undefined,
      selectedFile.value,
    )
    summaryDraft.value = ''
    selectedFile.value = undefined
    toastStore.show('success', 'Scope of work saved', 'A new revision was recorded.')
  } catch (err) {
    toastStore.show('error', 'Could not save scope of work', err instanceof Error ? err.message : 'Please try again.')
  } finally {
    isSaving.value = false
  }
}

async function handleApprove(): Promise<void> {
  isApproving.value = true
  try {
    const updated = await projectService.approveScopeOfWork(props.project.id)
    await load()
    // approveScopeOfWork can move current_stage server-side (see
    // project_service.try_auto_advance_stage) -- the shared project
    // store's cached copy (what the header badge and Workflow Progress
    // stepper above this tab actually read) doesn't know that on its
    // own, since this call goes straight through projectService rather
    // than one of the store's own mutating actions.
    await projectStore.refreshProject(props.project.id)
    if (updated.currentStage === 'Quotation') {
      toastStore.show('success', 'Scope of work approved', 'The project moved on to Quotation.')
      emit('navigate-tab', 'quotation')
    } else {
      toastStore.show('success', 'Scope of work approved', 'Internal approval recorded.')
    }
  } catch (err) {
    toastStore.show('error', 'Could not approve scope of work', err instanceof Error ? err.message : 'Please try again.')
  } finally {
    isApproving.value = false
  }
}

async function handleDownloadRevision(revision: ScopeRevision): Promise<void> {
  try {
    const blob = await projectService.downloadScopeRevisionDocument(props.project.id, revision.id)
    triggerBlobDownload(blob, revision.documentName ?? `${revision.revision}.pdf`)
  } catch (err) {
    toastStore.show('error', 'Download failed', err instanceof Error ? err.message : 'Please try again.')
  }
}

const projectDetailItems = computed(() => [
  { label: 'Service', value: props.project.service },
  { label: 'Responsible Engineer', value: props.project.engineer },
  { label: 'Start Date', value: formatDate(props.project.startDate) },
  { label: 'Target Completion Date', value: formatDate(props.project.targetDate) },
  { label: 'Priority', value: props.project.priority },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: 'Company Name', value: props.client.companyName },
    { label: 'Contact Person', value: props.client.contactPerson },
    { label: 'Mobile', value: props.client.mobile },
    { label: 'Email', value: props.client.email },
    { label: 'City', value: props.client.city },
  ]
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel title="Project Details" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel title="Client Details" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            Message Client
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            View Full Profile
          </BaseButton>
        </div>
      </div>
    </div>

    <Card>
      <template #header>
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-semibold text-text-primary">Scope of Work</h3>
          <StatusBadge
            v-if="scopeOfWork"
            :label="scopeOfWork.scopeStatus"
            :variant="scopeOfWork.scopeStatus === 'Approved' ? 'success' : 'neutral'"
          />
        </div>
      </template>

      <ErrorState v-if="error" :description="error" @retry="load" />
      <SkeletonLoader v-else-if="isLoading" :rows="5" />

      <div v-else class="flex flex-col gap-4">
        <p v-if="scopeOfWork?.scopeStatus === 'Approved'" class="text-sm text-text-secondary">
          Approved{{ scopeOfWork.scopeApprovedBy ? ` by ${scopeOfWork.scopeApprovedBy}` : '' }}{{
            scopeOfWork.scopeApprovedAt ? ` on ${formatDateTime(scopeOfWork.scopeApprovedAt)}` : ''
          }}. Editing the text below will reopen it for approval.
        </p>

        <TextArea
          v-model="scopeDraft"
          label="Scope of Work"
          placeholder="What has the client asked for..."
          :rows="6"
        />

        <TextArea
          v-model="summaryDraft"
          label="Change Summary (optional)"
          placeholder="What changed in this revision..."
          :rows="2"
        />

        <FileUploader hint="Optional supporting document (PDF, Word, Excel or image)" @select="selectedFile = $event" />

        <div class="flex flex-wrap items-center justify-end gap-2 no-print">
          <BaseButton variant="secondary" :disabled="!canSave" :loading="isSaving" @click="handleSave">
            Save Scope of Work
          </BaseButton>
          <BaseButton :icon="CheckCircle2" :disabled="!canApprove" :loading="isApproving" @click="handleApprove">
            Approve
          </BaseButton>
        </div>
      </div>
    </Card>

    <ScopeRevisionHistory v-if="scopeOfWork" :revisions="scopeOfWork.revisions" @download="handleDownloadRevision" />
  </div>
</template>
