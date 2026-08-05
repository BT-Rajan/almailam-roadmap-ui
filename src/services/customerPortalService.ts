import {
  CUSTOMER_PORTAL_DELIVERABLES,
  CUSTOMER_PORTAL_MILESTONES,
  CUSTOMER_PORTAL_PROJECTS,
  CUSTOMER_PORTAL_UPDATES,
} from '@/mock/customerPortal'
import type {
  CustomerProjectStatus,
  ProjectDeliverable,
  ProjectMilestone,
  ProjectUpdate,
} from '@/types/CustomerPortal'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const DEFAULT_PROJECT_ID = 'PROJ-2024-001'

export interface CustomerProjectView {
  project: CustomerProjectStatus
  milestones: ProjectMilestone[]
  deliverables: ProjectDeliverable[]
  updates: ProjectUpdate[]
}

async function getProjectView(projectId: string): Promise<CustomerProjectView> {
  await simulateNetworkDelay()
  return {
    project: CUSTOMER_PORTAL_PROJECTS[projectId] ?? CUSTOMER_PORTAL_PROJECTS[DEFAULT_PROJECT_ID],
    milestones: CUSTOMER_PORTAL_MILESTONES[projectId] ?? CUSTOMER_PORTAL_MILESTONES[DEFAULT_PROJECT_ID],
    deliverables: CUSTOMER_PORTAL_DELIVERABLES[projectId] ?? CUSTOMER_PORTAL_DELIVERABLES[DEFAULT_PROJECT_ID],
    updates: CUSTOMER_PORTAL_UPDATES[projectId] ?? CUSTOMER_PORTAL_UPDATES[DEFAULT_PROJECT_ID],
  }
}

export const customerPortalService = {
  getProjectView,
}
