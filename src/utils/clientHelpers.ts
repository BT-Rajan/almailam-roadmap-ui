import type { Client, ClientOnboardingState, ClientStatus, ClientVerificationResult } from '@/types/Client'
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

export function getClientDisplayName(client: Client): string {
  if (client.clientType === 'Individual') {
    return client.individualProfile?.fullLegalName ?? client.companyName
  }
  return client.organisationProfile?.legalName ?? client.companyName
}

/** Same "M/s." prefix generated documents already put ahead of a client's
 * name (see backend document_template_service.py's _client_display_name)
 * -- applied here too so a client reads the same gender/entity-neutral
 * way in-app as it does on the paperwork, regardless of whether they're
 * a company or an individual. */
export function getClientFormalName(client: Client): string {
  return `M/s. ${getClientDisplayName(client)}`
}
