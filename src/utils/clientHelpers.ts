import { CLIENT_ONBOARDING_REQUIREMENTS } from '@/constants/clientOptions'
import type {
  Client,
  ClientAddress,
  ClientContact,
  ClientDocument,
  ClientOnboardingState,
  ClientStatus,
  ClientVerification,
  ClientVerificationResult,
  OnboardingCheckContext,
} from '@/types/Client'
import type { BadgeVariant } from '@/types/Ui'

const ONBOARDING_STATE_VARIANTS: Record<ClientOnboardingState, BadgeVariant> = {
  'Information Required': 'warning',
  'Documents Required': 'warning',
  'Verification Required': 'info',
  'Under Review': 'info',
  Ready: 'success',
  Rejected: 'danger',
  Suspended: 'neutral',
}

const STATUS_VARIANTS: Record<ClientStatus, BadgeVariant> = {
  Active: 'success',
  Inactive: 'neutral',
}

const VERIFICATION_VARIANTS: Record<ClientVerificationResult, BadgeVariant> = {
  Pending: 'warning',
  Verified: 'success',
  Rejected: 'danger',
}

export function getClientOnboardingStateVariant(state: ClientOnboardingState): BadgeVariant {
  return ONBOARDING_STATE_VARIANTS[state]
}

export function getClientStatusVariant(status: ClientStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getClientVerificationVariant(result: ClientVerificationResult): BadgeVariant {
  return VERIFICATION_VARIANTS[result]
}

/** True when an identification document's expiry date has already passed. */
export function isIdentificationExpired(expiryDate: string): boolean {
  return expiryDate < new Date().toISOString().slice(0, 10)
}

export function generateClientCode(existingCount: number): string {
  return `CLT-${String(existingCount + 1).padStart(3, '0')}`
}

export function getClientDisplayName(client: Client): string {
  if (client.clientType === 'Individual') {
    return client.individualProfile?.fullLegalName ?? client.companyName
  }
  return client.organisationProfile?.legalName ?? client.companyName
}

interface OnboardingSummary {
  completedCount: number
  totalCount: number
  completionPercentage: number
  missingItems: string[]
  /** Every configured item's satisfied/not state, including optional ones
   * (which don't affect missingItems/completion% but still need a real
   * answer for display -- previously optional items were never evaluated
   * at all and always showed satisfied regardless of the actual data). */
  satisfiedByLabel: Record<string, boolean>
}

/**
 * Evaluates configured onboarding requirements for a client against the
 * contacts/addresses/documents currently on file to produce a completion
 * summary. Each requirement checks its own real data (e.g. "Authorised
 * representative" checks whether any contact is actually flagged as one)
 * rather than a single shared "is the profile complete" flag -- that
 * approach previously meant every Information-category item could only
 * ever be all-satisfied or all-missing together, and "Authorised
 * representative" in particular never checked contacts at all.
 */
export function evaluateOnboardingRequirements(ctx: OnboardingCheckContext): OnboardingSummary {
  const requirements = CLIENT_ONBOARDING_REQUIREMENTS[ctx.client.clientType]
  const requiredItems = requirements.filter((requirement) => requirement.required)

  const missingItems: string[] = []
  const satisfiedByLabel: Record<string, boolean> = {}
  requirements.forEach((requirement) => {
    const satisfied = requirement.isSatisfied(ctx)
    satisfiedByLabel[requirement.label] = satisfied
    if (requirement.required && !satisfied) missingItems.push(requirement.label)
  })

  const completedCount = requiredItems.length - missingItems.length

  return {
    completedCount,
    totalCount: requiredItems.length,
    completionPercentage: requiredItems.length === 0 ? 100 : Math.round((completedCount / requiredItems.length) * 100),
    missingItems,
    satisfiedByLabel,
  }
}

export function calculateOnboardingState(
  client: Client,
  documents: ClientDocument[],
  contacts: ClientContact[],
  addresses: ClientAddress[],
  verifications: ClientVerification[],
): ClientOnboardingState {
  if (client.onboardingState === 'Rejected' || client.onboardingState === 'Suspended') {
    return client.onboardingState
  }

  const summary = evaluateOnboardingRequirements({ client, documents, contacts, addresses })
  const hasRejectedVerification = verifications.some((verification) => verification.result === 'Rejected')
  const hasPendingVerification = verifications.some((verification) => verification.result === 'Pending')

  if (hasRejectedVerification) return 'Rejected'
  if (summary.missingItems.some((item) => item.toLowerCase().includes('document'))) return 'Documents Required'
  if (summary.missingItems.length > 0) return 'Information Required'
  if (hasPendingVerification) return 'Verification Required'
  if (verifications.length === 0) return 'Under Review'
  return 'Ready'
}
