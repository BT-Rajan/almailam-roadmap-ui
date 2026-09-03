<script setup lang="ts">
import { ArrowRight, CheckCircle2, MessageSquare } from '@lucide/vue'
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
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { Project, ProjectWorkspaceTabKey, ScopeOfWork, ScopeRevision } from '@/types/Project'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { hasProjectPassedStage } from '@/utils/projectHelpers'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const router = useRouter()
const projectStore = useProjectStore()
const clientStore = useClientStore()
const quotationStore = useQuotationStore()
const toastStore = useToastStore()

// Once any of this project's quotations has been finalized, the scope
// it was built against is frozen too -- see backend project_service.
// _assert_requirement_editable. Reads straight from quotationStore.
// quotations without loading it here -- ProjectWorkspacePage.vue's own
// loadData() already fetches this project's quotations before any tab
// (this one included) ever mounts.
const isRequirementLocked = computed(() => quotationStore.quotations.some((quotation) => quotation.finalizedAt))

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

// Mirrors the real exit criterion for Requirement -> Quotation exactly
// (project_service._assert_stage_exit_criteria) -- an identification
// record on file, not just any uploaded document. Approving without
// this used to "succeed" but silently leave the project stuck at
// Requirement with no explanation (try_auto_advance_stage no-ops
// quietly when the criteria aren't met yet) -- surfaced here instead so
// staff know what's actually still missing before they click Approve.
function loadClientIdentification(): void {
  if (props.client) clientStore.loadClientDetail(props.client.id)
}

onMounted(load)
onMounted(loadClientIdentification)
watch(() => props.project.id, load)
watch(() => props.client?.id, loadClientIdentification)

const hasClientIdentification = computed(() => clientStore.identifications.length > 0)
const hasTextChanged = computed(() => scopeDraft.value.trim() !== (scopeOfWork.value?.description ?? '').trim())
const canSave = computed(
  () => !isRequirementLocked.value && scopeDraft.value.trim().length > 0 && (hasTextChanged.value || Boolean(selectedFile.value)),
)
// Scope approval itself is an internal sign-off independent of client
// identification (see project_service.approve_scope_of_work) -- only
// the *stage* move to Quotation needs identification on file too (see
// _assert_stage_exit_criteria). So this button stays enabled without
// it (approving scope while waiting on the client's ID is a legitimate
// sequence), but the warning below sets the right expectation first.
const canApprove = computed(
  () =>
    !isRequirementLocked.value &&
    scopeOfWork.value?.scopeStatus === 'Draft' &&
    (scopeOfWork.value?.description ?? '').trim().length > 0 &&
    !hasTextChanged.value,
)

// Mirrors the real Requirement -> Quotation exit criterion exactly
// (project_service._assert_stage_exit_criteria: scope Approved + client
// identification on file) -- the project has already auto-advanced to
// Quotation the moment both became true (see try_auto_advance_stage),
// so this is just the UI convenience of jumping straight to that tab
// instead of leaving staff to find it via the stepper. Guarded by
// hasProjectPassedStage the same way as the other "Advance to X"
// buttons, so it doesn't linger once the project has moved on further
// still (e.g. Payment Plan or beyond) on a later visit to this tab.
const canAdvanceToQuotation = computed(
  () =>
    scopeOfWork.value?.scopeStatus === 'Approved' &&
    hasClientIdentification.value &&
    !hasProjectPassedStage(props.project.currentStage, 'Quotation'),
)

function handleAdvanceToQuotation(): void {
  emit('navigate-tab', 'quotation')
}

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
    } else if (!hasClientIdentification.value) {
      toastStore.show(
        'success',
        'Scope of work approved',
        "Internal approval recorded, but the project stays at Requirement until the client's identification document is on file too.",
      )
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
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-semibold text-text-primary">Scope of Work</h3>
            <StatusBadge
              v-if="scopeOfWork"
              :label="scopeOfWork.scopeStatus"
              :variant="scopeOfWork.scopeStatus === 'Approved' ? 'success' : 'neutral'"
            />
            <span
              v-if="isRequirementLocked"
              class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
            >
              Content Locked
            </span>
          </div>

          <div v-if="!isRequirementLocked || canAdvanceToQuotation" class="flex flex-wrap items-center gap-2 no-print">
            <template v-if="!isRequirementLocked">
              <BaseButton variant="secondary" size="sm" :disabled="!canSave" :loading="isSaving" @click="handleSave">
                Save Scope of Work
              </BaseButton>
              <BaseButton size="sm" :icon="CheckCircle2" :disabled="!canApprove" :loading="isApproving" @click="handleApprove">
                Approve
              </BaseButton>
            </template>
            <BaseButton v-if="canAdvanceToQuotation" size="sm" :icon="ArrowRight" @click="handleAdvanceToQuotation">
              Advance to Quotation
            </BaseButton>
          </div>
        </div>
      </template>

      <ErrorState v-if="error" :description="error" @retry="load" />
      <SkeletonLoader v-else-if="isLoading" :rows="5" />

      <div v-else class="flex flex-col gap-4">
        <p v-if="isRequirementLocked" class="text-sm text-text-secondary">
          This project's quotation has already been finalized against this scope, so it's locked -- a change here
          would no longer match what was quoted.
        </p>
        <p v-else-if="scopeOfWork?.scopeStatus === 'Approved'" class="text-sm text-text-secondary">
          Approved{{ scopeOfWork.scopeApprovedBy ? ` by ${scopeOfWork.scopeApprovedBy}` : '' }}{{
            scopeOfWork.scopeApprovedAt ? ` on ${formatDateTime(scopeOfWork.scopeApprovedAt)}` : ''
          }}. Editing the text below will reopen it for approval.
        </p>

        <TextArea
          v-model="scopeDraft"
          label="Scope of Work"
          placeholder="What has the client asked for..."
          :rows="6"
          :disabled="isRequirementLocked"
        />

        <template v-if="!isRequirementLocked">
          <TextArea
            v-model="summaryDraft"
            label="Change Summary (optional)"
            placeholder="What changed in this revision..."
            :rows="2"
          />

          <FileUploader hint="Optional supporting document (PDF, Word, Excel or image)" @select="selectedFile = $event" />
        </template>

        <p v-if="canApprove && !hasClientIdentification" class="text-xs text-danger-500">
          The client has no identification document on file yet (e.g. Civil ID) -- Approve will still record this
          internal sign-off, but the project will stay at Requirement until identification is added too.
        </p>
      </div>
    </Card>

    <ScopeRevisionHistory v-if="scopeOfWork" :revisions="scopeOfWork.revisions" @download="handleDownloadRevision" />
  </div>
</template>
