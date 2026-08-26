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
  ClientVerification,
  ClientVerificationResult,
  OnboardingCheckContext,
} from '@/types/Client'
import type { BadgeVariant } from '@/types/Ui'

const ONBOARDING_STATE_VARIANTS: Record<ClientOnboardingState, BadgeVariant> = {
  'Information Required': 'warning',
  'Documents Required': 'warning',
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
 * Verifications are append-only history (see client_service.py's
 * create_verification -- re-verifying something adds a new row, it
 * never edits or removes the old one, on purpose, so the audit trail
 * of who checked what and when is never lost). calculateOnboardingState()
 * below needs to know the CURRENT state of each item, not its whole
 * history -- without this, a document that was Pending and later
 * re-verified as Verified would still count as pending forever, because
 * the old Pending row is still sitting in the list. Same bug, worse
 * consequence, for Rejected: a client could get permanently stuck in
 * the Rejected onboarding state even after the actual problem was
 * fixed and re-verified, since the stale Rejected row never goes away
 * on its own.
 *
 * Dedupes to one entry per item -- keyed by documentId when the
 * verification is tied to a specific document (matching how the
 * backend already keeps that document's own verification_status in
 * sync with its latest check), or by the item name otherwise -- keeping
 * only the most recent by verifiedDate.
 */
function latestVerificationPerItem(verifications: ClientVerification[]): ClientVerification[] {
  const latestByKey = new Map<string, ClientVerification>()
  for (const verification of verifications) {
    const key = verification.documentId ?? `item:${verification.item.trim().toLowerCase()}`
    const existing = latestByKey.get(key)
    if (!existing || new Date(verification.verifiedDate) > new Date(existing.verifiedDate)) {
      latestByKey.set(key, verification)
    }
  }
  return Array.from(latestByKey.values())
}

/**
 * Onboarding is only complete (Ready) once Identification is on file --
 * documents (category 'Document') and basic profile info (category
 * 'Information') are earlier gates (Documents Required / Information
 * Required respectively). A document that's been actively rejected on
 * verification still short-circuits straight to Rejected, same as before
 * -- that's a real problem flag, independent of which step the client
 * happens to be on.
 */
export function calculateOnboardingState(
  client: Client,
  documents: ClientDocument[],
  contacts: ClientContact[],
  addresses: ClientAddress[],
  identifications: ClientIdentification[],
  verifications: ClientVerification[],
): ClientOnboardingState {
  if (client.onboardingState === 'Rejected' || client.onboardingState === 'Suspended') {
    return client.onboardingState
  }

  const summary = evaluateOnboardingRequirements({ client, documents, contacts, addresses, identifications })
  const currentVerifications = latestVerificationPerItem(verifications)
  const hasRejectedVerification = currentVerifications.some((verification) => verification.result === 'Rejected')

  if (hasRejectedVerification) return 'Rejected'
  if (summary.missingCategories.includes('Document')) return 'Documents Required'
  if (summary.missingCategories.includes('Information')) return 'Information Required'
  if (summary.missingCategories.includes('Identification')) return 'Under Review'
  return 'Ready'
}
