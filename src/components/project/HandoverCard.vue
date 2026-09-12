<script setup lang="ts">
import { CheckCircle2, Mail } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import SignedDocumentUploadDialog from '@/components/common/SignedDocumentUploadDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { projectService } from '@/services/projectService'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { HandoverStatus, Project, WorkflowStage } from '@/types/Project'
import { formatDateTime } from '@/utils/dateFormatter'

// Extracted verbatim out of ProjectOverviewTab.vue (see that file's own
// remaining sections for the others still pending the same split) --
// picked to go first because, unlike the Design/Permit/Supervision
// sections, it doesn't share any state with a sibling section. The one
// real coupling it has to the rest of the workspace -- Design/Permit/
// Supervision status changes need the Handover checklist to reflect
// them immediately, not just on next full reload -- is handled by
// exposing reload() below rather than folding that logic in here, so
// this component doesn't need to know anything about those other
// sections either.
const props = defineProps<{
  project: Project
  client: Client | undefined
  // Same meaning as ProjectOverviewTab's own prop of the same name --
  // see its docstring. Passed straight through rather than re-derived
  // here so both stay in sync with the workflow stepper.
  stageContext: WorkflowStage
}>()

const { t } = useI18n()
const router = useRouter()
const projectStore = useProjectStore()
const toastStore = useToastStore()

// Loaded unconditionally rather than gated behind stageContext, since
// staff can land on a project already past Handover too (reviewing
// after the fact via the stepper).
const handoverStatus = ref<HandoverStatus>()

async function loadHandoverStatus(): Promise<void> {
  try {
    handoverStatus.value = await projectService.getHandoverStatus(props.project.id)
  } catch {
    handoverStatus.value = undefined
  }
}

// Exposed so ProjectOverviewTab's Design/Permit/Supervision action
// handlers can refresh this card's own data after closing/reopening an
// activity elsewhere in the workspace, without this component needing
// to know anything about those sections.
defineExpose({ reload: loadHandoverStatus })

// Same shared usePagination/TablePagination.vue pair as every other
// list in the app -- sliced client-side against the checklist already
// fetched above.
const {
  currentPage: handoverChecklistPage,
  pageSize: handoverChecklistPageSize,
  totalItems: handoverChecklistTotalItems,
  totalPages: handoverChecklistTotalPages,
  startIndex: handoverChecklistStartIndex,
  endIndex: handoverChecklistEndIndex,
  goToPage: goToHandoverChecklistPage,
  setPageSize: setHandoverChecklistPageSize,
  resetPage: resetHandoverChecklistPage,
} = usePagination(() => handoverStatus.value?.checklist.length ?? 0)
const pagedHandoverChecklist = computed(() => (handoverStatus.value?.checklist ?? []).slice(handoverChecklistStartIndex.value, handoverChecklistEndIndex.value))
watch(() => handoverStatus.value?.checklist, () => resetHandoverChecklistPage())

// Gated to the Handover stage's own Overview tab now that Handover is a
// real WorkflowStage (it used to show on every stage's Overview once
// ready, back when hand-over readiness lived outside the stage
// machine) -- status === 'Completed' stays included so a project
// viewed after the fact (stepper jumped elsewhere) still shows its
// hand-over record.
const showHandoverCard = computed(
  () => props.stageContext === 'Handover' || props.project.status === 'Completed',
)

const isHandoverDialogOpen = ref(false)
const isHandoverSaving = ref(false)

// Asked once, right after the project actually completes -- not a
// stage/status option of its own, just a convenience offer to get a
// finished project out of the active list immediately instead of
// leaving that for whenever someone happens to notice it's done and
// archives it by hand later. "No" is a real, equally-valid answer:
// the project stays exactly as it is (Completed, still active) with
// nothing else to undo.
const isArchivePromptOpen = ref(false)
const isArchiving = ref(false)

async function handleConfirmHandover(payload: { file: File }): Promise<void> {
  isHandoverSaving.value = true
  try {
    await projectService.confirmProjectHandover(props.project.id, payload.file)
    await projectStore.refreshProject(props.project.id)
    await loadHandoverStatus()
    isHandoverDialogOpen.value = false
    toastStore.show('success', t('project.overviewTab.handover.confirmedTitle'), t('project.overviewTab.handover.confirmedDescription'))
    isArchivePromptOpen.value = true
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.handover.failedToConfirm'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isHandoverSaving.value = false
  }
}

async function handleArchiveConfirm(): Promise<void> {
  isArchiving.value = true
  try {
    await projectStore.deleteProject(props.project.id)
    isArchivePromptOpen.value = false
    toastStore.show('success', t('project.overviewTab.handover.archivedTitle'), t('project.overviewTab.handover.archivedDescription'))
    router.push({ name: ROUTE_NAMES.PROJECTS })
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.handover.failedToArchive'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isArchiving.value = false
  }
}

onMounted(loadHandoverStatus)
watch(() => props.project.id, loadHandoverStatus)
</script>

<template>
  <Card v-if="showHandoverCard">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.handover.title') }}</h3>
        <StatusBadge
          v-if="project.status === 'Completed'"
          :label="t('project.overviewTab.handover.acknowledged')"
          variant="success"
        />
        <StatusBadge
          v-else-if="handoverStatus && !handoverStatus.stageReached"
          :label="t('project.overviewTab.handover.notReadyYet')"
          variant="neutral"
        />
        <StatusBadge
          v-else
          :label="t('project.overviewTab.handover.awaitingAcknowledgment')"
          variant="warning"
        />
      </div>
    </template>

    <p
      v-if="project.status !== 'Completed' && handoverStatus && !handoverStatus.stageReached && handoverStatus.notReadyReason"
      class="text-sm text-text-secondary"
    >
      {{ handoverStatus.notReadyReason }}
    </p>

    <ul v-if="handoverStatus?.checklist.length" class="flex flex-col gap-1.5">
      <li
        v-for="item in pagedHandoverChecklist"
        :key="item.id"
        class="flex items-center gap-2 text-sm text-text-secondary"
      >
        <CheckCircle2 class="h-4 w-4 shrink-0 text-status-success" />
        <span>{{ item.title }}</span>
        <span class="text-xs text-text-muted">({{ item.sourceType }})</span>
      </li>
    </ul>
    <TablePagination
      v-if="handoverChecklistTotalItems > 0"
      class="mt-2 rounded-xl border border-border-light"
      :current-page="handoverChecklistPage"
      :total-pages="handoverChecklistTotalPages"
      :total-items="handoverChecklistTotalItems"
      :start-index="handoverChecklistStartIndex"
      :end-index="handoverChecklistEndIndex"
      :page-size="handoverChecklistPageSize"
      @page-change="goToHandoverChecklistPage"
      @page-size-change="setHandoverChecklistPageSize"
    />

    <div class="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-border-light pt-3">
      <p v-if="project.status === 'Completed' && handoverStatus?.handoverAcknowledgedAt" class="text-sm text-text-secondary">
        {{ t('project.overviewTab.handover.acknowledgedOnFragment', { date: formatDateTime(handoverStatus.handoverAcknowledgedAt) }) }}
      </p>
      <p v-else-if="handoverStatus?.handoverSentAt && !project.handoverPaymentConfirmedAt" class="text-sm text-warning-700">
        {{ t('project.overviewTab.handover.confirmPaymentFirst') }}
      </p>
      <p v-else-if="handoverStatus?.handoverSentAt" class="text-sm text-text-secondary">
        {{ t('project.overviewTab.handover.readySinceFragment', { date: formatDateTime(handoverStatus.handoverSentAt) }) }}
      </p>
      <p v-else-if="handoverStatus?.stageReached" class="text-sm text-text-secondary">{{ t('project.overviewTab.handover.readyToSend') }}</p>

      <BaseButton
        v-if="project.status !== 'Completed' && client"
        size="sm"
        :icon="Mail"
        :loading="isHandoverSaving"
        :disabled="!project.handoverPaymentConfirmedAt || !handoverStatus?.stageReached"
        class="no-print"
        @click="isHandoverDialogOpen = true"
      >
        {{ t('project.overviewTab.handover.confirmHandover') }}
      </BaseButton>
    </div>

    <SignedDocumentUploadDialog
      v-if="client"
      v-model="isHandoverDialogOpen"
      :loading="isHandoverSaving"
      :title="t('project.overviewTab.handover.confirmDialogTitle')"
      :description="t('project.overviewTab.handover.confirmDialogDescription')"
      @confirm="handleConfirmHandover"
    />

    <ConfirmationDialog
      v-model="isArchivePromptOpen"
      :title="t('project.overviewTab.handover.archivePromptTitle')"
      :message="t('project.overviewTab.handover.archivePromptMessage')"
      :confirm-label="t('project.overviewTab.handover.archiveYes')"
      :cancel-label="t('project.overviewTab.handover.archiveNo')"
      :loading="isArchiving"
      @confirm="handleArchiveConfirm"
    />
  </Card>
</template>
