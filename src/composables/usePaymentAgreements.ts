import { computed, onMounted, watch } from 'vue'

import { usePaymentStore } from '@/stores/paymentStore'
import { useServerTimeStore } from '@/stores/serverTimeStore'
import { computeObligationStatus } from '@/utils/paymentHelpers'
import type { AgreementStream, FinancialAgreement, FinancialSummary, PaymentObligation } from '@/types/Payment'
import type { Project } from '@/types/Project'

export interface MonthlyBillStreamPortion {
  stream: AgreementStream
  // False while the stream's own payment plan is still Draft -- its
  // schedule (and therefore what's "due this month") can still change,
  // so it isn't part of the real bill yet. See MonthlyBill.isFinal.
  isFinalized: boolean
  due: number
  received: number
  outstanding: number
}

export interface MonthlyBill {
  monthLabel: string
  currency: string
  streams: MonthlyBillStreamPortion[]
  total: number
  totalReceived: number
  totalOutstanding: number
  // True only once every visible stream that has an obligation due this
  // month is on an Approved payment plan -- "the monthly bill is
  // whatever's due as per the Design & Permit payment due that month
  // plus the Supervision fee ... this gets final when the payment plan
  // is finalized." False doesn't mean the number shown is wrong, just
  // that one of its inputs could still change before it's locked in.
  isFinal: boolean
  // True if the visible streams with something due this month don't
  // all bill in the same currency -- extremely unlikely in practice
  // (Design and Supervision are independent FinancialAgreement rows
  // and could theoretically be created in different currencies), but
  // if it ever happens, total/totalReceived/totalOutstanding/currency
  // above are meaningless (left at 0/'') and the template must show
  // each stream portion separately instead of one blended figure.
  isMixedCurrency: boolean
}

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
  const serverTimeStore = useServerTimeStore()

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

  // Kuwait-local "this month" (see serverTimeStore.ts) -- YYYY-MM, so a
  // plain string-prefix match against each obligation's dueDate finds
  // everything due in the current calendar month without needing to
  // parse dates at all.
  const currentMonthKey = computed(() => serverTimeStore.todayIso?.slice(0, 7))

  // "Whatever's due as per the Design & Permit payment due that month,
  // plus the Supervision fee" -- one combined figure per project,
  // summed across whichever streams actually have something due this
  // month. Cancelled/Waived obligations are excluded (same reasoning
  // as getFinancialSummary -- nothing is really "due" on those).
  // Undefined until serverTimeStore has loaded, or if the project's
  // visible streams somehow end up billing in more than one currency
  // (extremely unlikely in practice -- Design and Supervision are
  // independent FinancialAgreement rows and could theoretically be
  // created in different currencies -- shown separately rather than
  // silently added together in that case; see the template).
  const monthlyBill = computed<MonthlyBill | undefined>(() => {
    const monthKey = currentMonthKey.value
    if (!monthKey) return undefined

    const portions: MonthlyBillStreamPortion[] = []
    let currency: string | undefined
    let mixedCurrency = false

    for (const stream of visibleStreams.value) {
      const agreement = agreementForStream(stream)
      if (!agreement) continue
      const dueThisMonth = obligationsForStream(stream).filter(
        (obligation) => obligation.dueDate.slice(0, 7) === monthKey && !obligation.manualStatus,
      )
      if (dueThisMonth.length === 0) continue

      if (currency === undefined) currency = agreement.currency
      else if (currency !== agreement.currency) mixedCurrency = true

      const due = dueThisMonth.reduce((sum, o) => sum + o.amountDue, 0)
      const received = dueThisMonth.reduce((sum, o) => sum + o.amountReceived, 0)
      portions.push({
        stream,
        isFinalized: agreement.status === 'Approved',
        due,
        received,
        outstanding: Math.max(due - received, 0),
      })
    }

    if (portions.length === 0) return undefined

    if (mixedCurrency || !currency) {
      return { monthLabel: monthKey, currency: '', streams: portions, total: 0, totalReceived: 0, totalOutstanding: 0, isFinal: false, isMixedCurrency: true }
    }

    return {
      monthLabel: monthKey,
      currency,
      streams: portions,
      total: portions.reduce((sum, p) => sum + p.due, 0),
      totalReceived: portions.reduce((sum, p) => sum + p.received, 0),
      totalOutstanding: portions.reduce((sum, p) => sum + p.outstanding, 0),
      isFinal: portions.every((p) => p.isFinalized),
      isMixedCurrency: false,
    }
  })

  async function loadDetailIfNeeded(): Promise<void> {
    await Promise.all(agreementIds.value.map((agreementId) => store.loadAgreementDetail(agreementId)))
  }

  onMounted(loadDetailIfNeeded)
  onMounted(() => void serverTimeStore.loadServerTime())
  watch(agreementIds, loadDetailIfNeeded)

  return {
    visibleStreams,
    agreementForStream,
    obligationsForStream,
    summaryForStream,
    outstandingObligationsForStream,
    monthlyBill,
    agreementIds,
    loadDetailIfNeeded,
  }
}
