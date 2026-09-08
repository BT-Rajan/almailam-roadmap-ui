import { CLIENT_ONBOARDING_REQUIREMENTS } from '@/constants/clientOptions'
import type {
  Client,
  ClientAddress,
  ClientContact,
  ClientDocument,
  ClientIdentification,
  ClientOnboardingRequirement,
  ClientOnboardingState,
  ClientStatus,
  ClientVerificationResult,
  OnboardingCheckContext,
} from '@/types/Client'
import type { BadgeVariant } from '@/types/Ui'

const ONBOARDING_STATE_VARIANTS: Record<ClientOnboardingState, BadgeVariant> = {
  'Information Required': 'warning',
  'Documents Required': 'warning',
  'Pending Verification': 'info',
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
  /** Categories of the required-but-unsatisfied items in missingItems --
   * lets calculateOnboardingState() below route a client to the right
   * onboarding state (e.g. a missing Document vs a missing Identification)
   * without string-matching on the label text. */
  missingCategories: ClientOnboardingRequirement['category'][]
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
  const missingCategories: ClientOnboardingRequirement['category'][] = []
  const satisfiedByLabel: Record<string, boolean> = {}
  requirements.forEach((requirement) => {
    const satisfied = requirement.isSatisfied(ctx)
    satisfiedByLabel[requirement.label] = satisfied
    if (requirement.required && !satisfied) {
      missingItems.push(requirement.label)
      missingCategories.push(requirement.category)
    }
  })

  const completedCount = requiredItems.length - missingItems.length

  return {
    completedCount,
    totalCount: requiredItems.length,
    completionPercentage: requiredItems.length === 0 ? 100 : Math.round((completedCount / requiredItems.length) * 100),
    missingItems,
    missingCategories,
    satisfiedByLabel,
  }
}

/**
 * Recommends where a client's onboarding should be, purely from the
 * data on file -- doesn't consult ClientVerification (that's now just
 * an append-only audit record shown on the client workspace, no longer
 * a gate; see the "Pending Verification" state itself, which is proven
 * by a confirmed signed-document upload rather than a document
 * verification result).
 *
 * A client already sitting at 'Rejected' or 'Suspended' stays there --
 * those are exception states a human put the client into on purpose,
 * not something this recommendation should override. Missing documents
 * or missing profile/identification info route back to the relevant
 * data-collection step; once everything required is on file, the
 * recommendation is 'Pending Verification' (request the signed consent
 * upload) unless the client has already cleared that and is 'Ready'.
 */
export function calculateOnboardingState(
  client: Client,
  documents: ClientDocument[],
  contacts: ClientContact[],
  addresses: ClientAddress[],
  identifications: ClientIdentification[],
): ClientOnboardingState {
  if (client.onboardingState === 'Rejected' || client.onboardingState === 'Suspended') {
    return client.onboardingState
  }

  const summary = evaluateOnboardingRequirements({ client, documents, contacts, addresses, identifications })

  if (summary.missingCategories.includes('Document')) return 'Documents Required'
  if (summary.missingCategories.includes('Information') || summary.missingCategories.includes('Identification')) {
    return 'Information Required'
  }
  return client.onboardingState === 'Ready' ? 'Ready' : 'Pending Verification'
}
