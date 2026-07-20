import { CLIENT_ONBOARDING_REQUIREMENTS } from '@/constants/clientOptions'
import type {
  Client,
  ClientDocument,
  ClientOnboardingState,
  ClientStatus,
  ClientType,
  ClientVerification,
  ClientVerificationResult,
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
}

/**
 * Evaluates configured onboarding requirements for a client type against the
 * documents and verifications currently on file to produce a completion summary.
 */
export function evaluateOnboardingRequirements(
  clientType: ClientType,
  documents: ClientDocument[],
  hasCompleteProfile: boolean,
): OnboardingSummary {
  const requirements = CLIENT_ONBOARDING_REQUIREMENTS[clientType]
  const requiredItems = requirements.filter((requirement) => requirement.required)

  const missingItems: string[] = []
  requiredItems.forEach((requirement) => {
    const isSatisfied = requirement.category === 'Document' ? documents.length > 0 : hasCompleteProfile
    if (!isSatisfied) missingItems.push(requirement.label)
  })

  const completedCount = requiredItems.length - missingItems.length

  return {
    completedCount,
    totalCount: requiredItems.length,
    completionPercentage: requiredItems.length === 0 ? 100 : Math.round((completedCount / requiredItems.length) * 100),
    missingItems,
  }
}

export function calculateOnboardingState(
  client: Client,
  documents: ClientDocument[],
  verifications: ClientVerification[],
  hasCompleteProfile: boolean,
): ClientOnboardingState {
  if (client.onboardingState === 'Rejected' || client.onboardingState === 'Suspended') {
    return client.onboardingState
  }

  const summary = evaluateOnboardingRequirements(client.clientType, documents, hasCompleteProfile)
  const hasRejectedVerification = verifications.some((verification) => verification.result === 'Rejected')
  const hasPendingVerification = verifications.some((verification) => verification.result === 'Pending')

  if (hasRejectedVerification) return 'Rejected'
  if (summary.missingItems.some((item) => item.toLowerCase().includes('document'))) return 'Documents Required'
  if (summary.missingItems.length > 0) return 'Information Required'
  if (hasPendingVerification) return 'Verification Required'
  if (verifications.length === 0) return 'Under Review'
  return 'Ready'
}
