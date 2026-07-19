import { GOVERNMENT_AUTHORITIES } from '@/mock/governmentAuthorities'
import { GOVERNMENT_FORMS } from '@/mock/governmentForms'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getForms(): Promise<GovernmentForm[]> {
  await simulateNetworkDelay()
  return [...GOVERNMENT_FORMS]
}

async function getAuthorities(): Promise<GovernmentAuthority[]> {
  await simulateNetworkDelay()
  return [...GOVERNMENT_AUTHORITIES]
}

export const governmentFormService = {
  getForms,
  getAuthorities,
}
