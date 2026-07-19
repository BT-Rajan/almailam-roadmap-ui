import { ROUTE_NAMES } from '@/constants/routeNames'
import type { AppNotification } from '@/types/Notification'

function daysAgoIso(days: number, hour = 9, minute = 0): string {
  const date = new Date()
  date.setDate(date.getDate() - days)
  date.setHours(hour, minute, 0, 0)
  return date.toISOString()
}

export const NOTIFICATIONS: AppNotification[] = [
  {
    id: 'NTF-2026-001',
    title: 'Contract approved',
    message: 'The MEP Design Services Agreement for Warehouse Expansion was approved by the client.',
    category: 'Project',
    date: daysAgoIso(0, 8, 45),
    read: false,
    link: { routeName: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: 'PRJ-2026-002' } },
  },
  {
    id: 'NTF-2026-002',
    title: 'AI review completed',
    message: 'The Soil Investigation Report has been reviewed with a 92% confidence extraction.',
    category: 'AI',
    date: daysAgoIso(0, 10, 15),
    read: false,
    link: { routeName: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId: 'DOC-2026-002' } },
  },
  {
    id: 'NTF-2026-003',
    title: 'Submission requires attention',
    message: 'Municipality feedback was received on the Tower A structural submission.',
    category: 'Government',
    date: daysAgoIso(0, 13, 30),
    read: false,
    link: { routeName: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS },
  },
  {
    id: 'NTF-2026-004',
    title: 'Task assigned to you',
    message: 'Layla Haddad assigned you a review task on the Tower A structural drawings.',
    category: 'Task',
    date: daysAgoIso(1, 16, 0),
    read: false,
    link: { routeName: ROUTE_NAMES.MY_TASKS },
  },
  {
    id: 'NTF-2026-005',
    title: 'Quotation sent to client',
    message: 'A revised quotation for the Warehouse Expansion project was sent for approval.',
    category: 'Project',
    date: daysAgoIso(1, 11, 20),
    read: true,
    link: { routeName: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: 'PRJ-2026-002' } },
  },
  {
    id: 'NTF-2026-006',
    title: 'Scheduled maintenance',
    message: 'ServiceOS will undergo brief maintenance this weekend between 1:00 AM and 3:00 AM.',
    category: 'System',
    date: daysAgoIso(3, 9, 0),
    read: true,
  },
  {
    id: 'NTF-2026-007',
    title: 'New government form published',
    message: 'The Municipality updated its Building Permit Application form to the latest revision.',
    category: 'Government',
    date: daysAgoIso(4, 14, 10),
    read: true,
    link: { routeName: ROUTE_NAMES.GOVERNMENT_FORMS },
  },
  {
    id: 'NTF-2026-008',
    title: 'AI summary ready',
    message: 'An AI-generated summary is ready for the MEP Design Services Agreement contract.',
    category: 'AI',
    date: daysAgoIso(6, 17, 40),
    read: true,
    link: { routeName: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId: 'DOC-2026-003' } },
  },
]
