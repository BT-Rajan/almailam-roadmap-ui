<script setup lang="ts">
import { CheckCircle2, ShieldCheck } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { projectService } from '@/services/projectService'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDateTime } from '@/utils/dateFormatter'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import type { HandoverStatus, Project } from '@/types/Project'

const props = defineProps<{
  project: Project
}>()

const { t } = useI18n()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const { visibleStreams, summaryForStream } = usePaymentAgreements(
  () => props.project.id,
  () => props.project,
)

// GET /handover self-heals the project's stage on every read (see
// backend project_service.try_auto_advance_stage) -- fetching it here
// too, not just from the Overview tab, means arriving at this tab
// directly still corrects a project that was already eligible for
// Handover but never actually got there, instead of "Confirm Payment
// Received" failing with a stale-sounding error a moment later.
const handoverStatus = ref<HandoverStatus>()
onMounted(async () => {
  try {
    handoverStatus.value = await projectService.getHandoverStatus(props.project.id)
    if (handoverStatus.value.stageReached) await projectStore.refreshProject(props.project.id)
  } catch {
    handoverStatus.value = undefined
  }
})

// Auto-computed reference status -- every visible billing stream's
// contract amount fully received. Shown alongside (never gating) the
// manual confirmation below, since staff can confirm by hand even if
// obligation tracking is incomplete (e.g. a payment collected outside
// the system) -- see project_service.confirm_handover_payment.
const streamSummaries = computed(() =>
  visibleStreams.value.map((stream) => ({ stream, summary: summaryForStream(stream) })),
)
const isAutoFullyPaid = computed(
  () =>
    streamSummaries.value.length > 0 &&
    streamSummaries.value.every(({ summary }) => summary && summary.totalReceived >= summary.contractAmount),
)

const isSaving = ref(false)

async function handleConfirmPayment(): Promise<void> {
  isSaving.value = true
  try {
    await projectService.confirmHandoverPayment(props.project.id)
    await projectStore.refreshProject(props.project.id)
    toastStore.show('success', t('project.handoverPaymentTab.confirmedTitle'))
  } catch (error) {
    toastStore.show('error', t('project.handoverPaymentTab.failedToConfirm'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}

async function handleUnconfirmPayment(): Promise<void> {
  isSaving.value = true
  try {
    await projectService.unconfirmHandoverPayment(props.project.id)
    await projectStore.refreshProject(props.project.id)
    toastStore.show('success', t('project.handoverPaymentTab.unconfirmedTitle'))
  } catch (error) {
    toastStore.show('error', t('project.handoverPaymentTab.failedToUnconfirm'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <Card>
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.handoverPaymentTab.autoStatusTitle') }}</h3>
      </template>
      <div v-if="streamSummaries.length === 0" class="text-sm text-text-muted">
        {{ t('project.handoverPaymentTab.noBillableStreams') }}
      </div>
      <div v-else class="flex flex-col gap-3">
        <div
          v-for="{ stream, summary } in streamSummaries"
          :key="stream"
          class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
        >
          <span class="text-sm text-text-secondary">{{ getAgreementStreamLabel(stream) }}</span>
          <span class="text-sm font-medium text-text-primary">
            {{ summary ? `${formatCurrency(summary.totalReceived)} / ${formatCurrency(summary.contractAmount)}` : t('project.handoverPaymentTab.noPlanYet') }}
          </span>
        </div>
        <div class="flex items-center gap-2 border-t border-border-light pt-3">
          <StatusBadge
            :label="isAutoFullyPaid ? t('project.handoverPaymentTab.autoFullyPaid') : t('project.handoverPaymentTab.autoNotFullyPaid')"
            :variant="isAutoFullyPaid ? 'success' : 'warning'"
          />
        </div>
      </div>
    </Card>

    <Card>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.handoverPaymentTab.manualTitle') }}</h3>
          <StatusBadge
            v-if="project.handoverPaymentConfirmedAt"
            :label="t('project.handoverPaymentTab.confirmed')"
            variant="success"
          />
          <StatusBadge v-else :label="t('project.handoverPaymentTab.notConfirmed')" variant="warning" />
        </div>
      </template>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-text-secondary">{{ t('project.handoverPaymentTab.manualDescription') }}</p>
        <div v-if="project.handoverPaymentConfirmedAt" class="flex flex-wrap items-center justify-between gap-3">
          <p class="flex items-center gap-2 text-sm text-success-700">
            <CheckCircle2 class="h-4 w-4 shrink-0" />
            {{
              t('project.handoverPaymentTab.confirmedByFragment', {
                name: project.handoverPaymentConfirmedBy ?? t('project.handoverPaymentTab.unknownUser'),
                date: formatDateTime(project.handoverPaymentConfirmedAt),
              })
            }}
          </p>
          <BaseButton variant="secondary" size="sm" :loading="isSaving" class="no-print" @click="handleUnconfirmPayment">
            {{ t('project.handoverPaymentTab.undoConfirmation') }}
          </BaseButton>
        </div>
        <BaseButton
          v-else
          size="sm"
          :icon="ShieldCheck"
          :loading="isSaving"
          class="self-start no-print"
          @click="handleConfirmPayment"
        >
          {{ t('project.handoverPaymentTab.confirmPayment') }}
        </BaseButton>
      </div>
    </Card>
  </div>
</template>
