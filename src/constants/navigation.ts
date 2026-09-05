import { ROUTE_NAMES } from '@/constants/routeNames'
import type { NavItem } from '@/types/Navigation'

// Government Center, Knowledge Base, and Documents (Document Repository) are
// hidden here deliberately, not removed -- their routes/pages/data stay
// fully intact (still directly reachable by URL, and reusable later), just
// no longer offered as a top-level destination. Government Center's own
// workflow sent staff out of a project (Stage 5, Approvals & Permits) into a
// standalone section with no way back to the project they came from;
// document prep is moving into the project workflow itself instead of
// living here. Re-add the entries below to restore them to the sidebar.
export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { labelKey: 'navigation.dashboard', routeName: ROUTE_NAMES.DASHBOARD, icon: 'LayoutDashboard', matchPath: '/dashboard' },
  { labelKey: 'navigation.clients', routeName: ROUTE_NAMES.CLIENTS, icon: 'Users', matchPath: '/clients' },
  { labelKey: 'navigation.projects', routeName: ROUTE_NAMES.PROJECTS, icon: 'FolderKanban', matchPath: '/projects' },
  { labelKey: 'navigation.payments', routeName: ROUTE_NAMES.PAYMENTS, icon: 'Wallet', matchPath: '/payments' },
  // { labelKey: 'navigation.documents', routeName: ROUTE_NAMES.DOCUMENTS, icon: 'FileText', matchPath: '/documents' },
  { labelKey: 'navigation.tasks', routeName: ROUTE_NAMES.TASKS, icon: 'ListChecks', matchPath: '/tasks' },
  { labelKey: 'navigation.reports', routeName: ROUTE_NAMES.REPORTS, icon: 'BarChart3', matchPath: '/reports' },
  {
    labelKey: 'navigation.administration',
    routeName: ROUTE_NAMES.ADMIN,
    icon: 'Settings',
    matchPath: '/admin',
    adminOnly: true,
  },
]
