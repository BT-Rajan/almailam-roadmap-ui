import {
  DEMO_CUSTOMER_PORTAL_CREDENTIALS,
  DEMO_CUSTOMER_PORTAL_PROJECTS,
} from '@/mock/customerPortalCredentials'
import { simulateNetworkDelay } from '@/utils/mockDelay'

// SECURITY NOTE: see src/mock/customerPortalCredentials.ts. This function's
// signature (`projectId` + `mobileNumber` in, boolean out) is deliberately
// shaped like a real API call so that swapping this out for a genuine
// backend verification endpoint later is a one-file change -- but today it
// is only checking against data that shipped in the browser bundle.
async function verifyAccess(projectId: string, mobileNumber: string): Promise<boolean> {
  await simulateNetworkDelay(800)
  return DEMO_CUSTOMER_PORTAL_CREDENTIALS[projectId.toUpperCase()]?.includes(mobileNumber) ?? false
}

async function getDemoProjects(): Promise<typeof DEMO_CUSTOMER_PORTAL_PROJECTS> {
  await simulateNetworkDelay()
  return DEMO_CUSTOMER_PORTAL_PROJECTS
}

export const customerPortalAuthService = {
  verifyAccess,
  getDemoProjects,
}
