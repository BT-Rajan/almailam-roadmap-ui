<script setup lang="ts">
import { MessageSquare, ShieldCheck } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()

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

const isConfirming = ref(false)

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
// record on file, not just any uploaded document. Confirming without
// this fails outright server-side (confirm_requirement_scope raises)
// -- surfaced here proactively so staff know what's still missing
// before they click Confirm rather than only finding out from the
// error toast.
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
// Scope of work has to actually be saved (and not have unsaved edits
// sitting in the textarea) before it's confirmed -- there's no
// separate internal sign-off step, and no client-facing step either,
// so this direct confirm action (canConfirm below) is the only
// approval this stage requires.
const canConfirm = computed(
  () =>
    !isRequirementLocked.value &&
    (scopeOfWork.value?.description ?? '').trim().length > 0 &&
    !hasTextChanged.value &&
    !scopeOfWork.value?.scopeClientConfirmedAt,
)

// A direct staff action, no dialog and no client-facing artifact --
// project_service.confirm_requirement_scope validates the same exit
// criteria this tab already surfaces (scope saved + client
// identification on file) and, on success, moves the project straight
// to Quotation in the same call. There's no separate "advance" step
// afterward: by the time this resolves the project is already on
// Quotation, so navigate there directly.
async function handleConfirm(): Promise<void> {
  isConfirming.value = true
  try {
    scopeOfWork.value = await projectService.confirmRequirementScope(props.project.id)
    // confirmRequirementScope moves current_stage server-side -- the
    // shared project store's cached copy (what the header badge and
    // Workflow Progress stepper above this tab actually read) doesn't
    // know that on its own, since this call goes straight through
    // projectService rather than one of the store's own mutating
    // actions.
    await projectStore.refreshProject(props.project.id)
    toastStore.show('success', t('project.requirementTab.confirmedTitle'), t('project.requirementTab.movedToQuotationDescription'))
    emit('navigate-tab', 'quotation')
  } catch (err) {
    toastStore.show(
      'error',
      t('project.requirementTab.failedToConfirm'),
      err instanceof Error ? err.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isConfirming.value = false
  }
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
    toastStore.show('success', t('project.requirementTab.scopeSavedTitle'), t('project.requirementTab.scopeSavedDescription'))
  } catch (err) {
    toastStore.show('error', t('project.requirementTab.couldNotSaveScope'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}

async function handleDownloadRevision(revision: ScopeRevision): Promise<void> {
  try {
    const blob = await projectService.downloadScopeRevisionDocument(props.project.id, revision.id)
    triggerBlobDownload(blob, revision.documentName ?? `${revision.revision}.pdf`)
  } catch (err) {
    toastStore.show('error', t('common.downloadFailed'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  }
}

const PRIORITY_LABEL_KEYS: Record<string, string> = {
  High: 'project.priority.high',
  Medium: 'project.priority.medium',
  Low: 'project.priority.low',
}
function priorityLabel(priority: string): string {
  return t(PRIORITY_LABEL_KEYS[priority] ?? priority)
}

const projectDetailItems = computed(() => [
  { label: t('project.requirementTab.fields.service'), value: props.project.service },
  { label: t('project.requirementTab.fields.responsibleEngineer'), value: props.project.engineer },
  { label: t('project.requirementTab.fields.startDate'), value: formatDate(props.project.startDate) },
  { label: t('project.requirementTab.fields.targetCompletionDate'), value: formatDate(props.project.targetDate) },
  { label: t('project.requirementTab.fields.priority'), value: priorityLabel(props.project.priority) },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: t('project.requirementTab.fields.companyName'), value: props.client.companyName },
    { label: t('project.requirementTab.fields.contactPerson'), value: props.client.contactPerson },
    { label: t('project.requirementTab.fields.mobile'), value: props.client.mobile },
    { label: t('project.requirementTab.fields.email'), value: props.client.email },
    { label: t('project.requirementTab.fields.city'), value: props.client.city },
  ]
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- Same top-level toolbar position as every other stage tab
         (ProjectQuotationTab/ProjectContractTab's Approve/Sign action,
         ProjectDocumentsTab's Design-mode toolbar) -- the primary
         approval action lives here, not buried in a card header, so
         it's always in the same place regardless of which stage tab
         is open. -->
    <div v-if="!isRequirementLocked" class="flex flex-wrap items-center justify-end gap-2 no-print">
      <BaseButton variant="secondary" size="sm" :disabled="!canSave" :loading="isSaving" @click="handleSave">
        {{ t('project.requirementTab.saveScope') }}
      </BaseButton>
      <BaseButton v-if="canConfirm" size="sm" :icon="ShieldCheck" :loading="isConfirming" @click="handleConfirm">
        {{ t('project.requirementTab.confirm') }}
      </BaseButton>
    </div>

    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel :title="t('project.requirementTab.projectDetailsTitle')" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel :title="t('project.requirementTab.clientDetailsTitle')" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            {{ t('project.requirementTab.messageClient') }}
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            {{ t('project.requirementTab.viewFullProfile') }}
          </BaseButton>
        </div>
      </div>
    </div>

    <Card>
      <template #header>
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.requirementTab.scopeOfWorkTitle') }}</h3>
          <StatusBadge
            :label="scopeOfWork?.scopeClientConfirmedAt ? t('project.requirementTab.confirmed') : t('project.scopeStatus.awaitingConfirmation')"
            :variant="scopeOfWork?.scopeClientConfirmedAt ? 'success' : 'neutral'"
          />
          <span
            v-if="isRequirementLocked"
            class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"
          >
            {{ t('project.requirementTab.contentLocked') }}
          </span>
        </div>
      </template>

      <ErrorState v-if="error" :description="error" @retry="load" />
      <SkeletonLoader v-else-if="isLoading" :rows="5" />

      <div v-else class="flex flex-col gap-4">
        <p v-if="isRequirementLocked" class="text-sm text-text-secondary">
          {{ t('project.requirementTab.lockedNotice') }}
        </p>
        <template v-else-if="scopeOfWork?.scopeClientConfirmedAt">
          <p class="text-sm text-text-secondary">
            {{
              t('project.requirementTab.confirmedOn', {
                on: t('project.requirementTab.confirmedOnFragment', { date: formatDateTime(scopeOfWork.scopeClientConfirmedAt) }),
              })
            }}
          </p>
        </template>
        <p v-else-if="canConfirm" class="text-xs text-warning-600">
          {{ t('project.requirementTab.awaitingConfirmationNotice') }}
        </p>

        <TextArea
          v-model="scopeDraft"
          :label="t('project.requirementTab.scopeOfWorkLabel')"
          :placeholder="t('project.requirementTab.scopeOfWorkPlaceholder')"
          :rows="6"
          :disabled="isRequirementLocked"
        />

        <template v-if="!isRequirementLocked">
          <TextArea
            v-model="summaryDraft"
            :label="t('project.requirementTab.changeSummaryLabel')"
            :placeholder="t('project.requirementTab.changeSummaryPlaceholder')"
            :rows="2"
          />

          <FileUploader :hint="t('project.requirementTab.uploadHint')" @select="selectedFile = $event" />
        </template>

        <p v-if="canConfirm && !hasClientIdentification" class="text-xs text-danger-500">
          {{ t('project.requirementTab.noClientIdNotice') }}
        </p>
      </div>
    </Card>

    <ScopeRevisionHistory v-if="scopeOfWork" :revisions="scopeOfWork.revisions" @download="handleDownloadRevision" />
  </div>
</template>
