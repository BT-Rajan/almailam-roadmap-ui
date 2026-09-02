import { computed, onMounted, watch } from 'vue'

import { usePaymentStore } from '@/stores/paymentStore'
import { computeObligationStatus } from '@/utils/paymentHelpers'
import type { AgreementStream, FinancialAgreement, FinancialSummary, PaymentObligation } from '@/types/Payment'
import type { Project } from '@/types/Project'

/**
 * Shared agreement/obligation lookups for a project's payment views --
 * both PaymentPlanPanel.vue (the plan itself: create/edit/delete/
 * approve) and PaymentStatusPanel.vue (money actually collected against
 * it) need the exact same "which streams does this project bill, and
 * what agreement/obligations/summary does each one have" logic, so it
 * lives here once rather than drifting apart in two copies.
 *
 * Takes getters rather than plain values so callers can pass
 * `() => props.projectId` / `() => props.project` and stay reactive to
 * prop changes -- destructuring props directly would freeze these at
 * whatever they were when the composable was first called.
 */
export function usePaymentAgreements(getProjectId: () => string, getProject: () => Project) {
  const store = usePaymentStore()

  const id = computed(getProjectId)
  const proj = computed(getProject)

  // A section is shown per billing stream this project actually includes
  // (see project.includesDesign/includesSupervision) -- plus any stream
  // that already has an agreement, in case that flag and the agreement's
  // existence ever momentarily disagree.
  const visibleStreams = computed<AgreementStream[]>(() => {
    const streams = new Set<AgreementStream>()
    if (proj.value.includesDesign) streams.add('Design')
    if (proj.value.includesSupervision) streams.add('Supervision')
    for (const agreement of store.agreements) {
      if (agreement.projectId === id.value) streams.add(agreement.stream)
    }
    return [...streams]
  })

  function agreementForStream(stream: AgreementStream): FinancialAgreement | undefined {
    return store.getAgreementByProject(id.value, stream)
  }

  function obligationsForStream(stream: AgreementStream): PaymentObligation[] {
    const agreement = agreementForStream(stream)
    return agreement ? store.obligationsForAgreement(agreement.id) : []
  }

  function summaryForStream(stream: AgreementStream): FinancialSummary | undefined {
    const agreement = agreementForStream(stream)
    return agreement ? store.summaryForAgreement(agreement.id) : undefined
  }

  function outstandingObligationsForStream(stream: AgreementStream): PaymentObligation[] {
    return obligationsForStream(stream).filter((obligation) => {
      const status = computeObligationStatus(obligation)
      return status !== 'Paid' && status !== 'Cancelled' && status !== 'Waived'
    })
  }

  const agreementIds = computed(() =>
    visibleStreams.value.map((stream) => agreementForStream(stream)?.id).filter((agreementId): agreementId is string => Boolean(agreementId)),
  )

  async function loadDetailIfNeeded(): Promise<void> {
    await Promise.all(agreementIds.value.map((agreementId) => store.loadAgreementDetail(agreementId)))
  }

  onMounted(loadDetailIfNeeded)
  watch(agreementIds, loadDetailIfNeeded)

  return {
    visibleStreams,
    agreementForStream,
    obligationsForStream,
    summaryForStream,
    outstandingObligationsForStream,
    agreementIds,
    loadDetailIfNeeded,
  }
}
