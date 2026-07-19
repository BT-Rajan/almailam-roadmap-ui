import { ROUTE_NAMES } from '@/constants/routeNames'
import type { NavItem } from '@/types/Navigation'

export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD, icon: 'LayoutDashboard' },
  { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS, icon: 'FolderKanban' },
  { label: 'Government Center', routeName: ROUTE_NAMES.GOVERNMENT_FORMS, icon: 'Landmark' },
  { label: 'Documents', routeName: ROUTE_NAMES.DOCUMENTS, icon: 'FileText' },
  { label: 'Tasks', routeName: ROUTE_NAMES.TASKS, icon: 'ListChecks' },
  { label: 'Reports', routeName: ROUTE_NAMES.REPORTS, icon: 'BarChart3' },
  { label: 'Administration', routeName: ROUTE_NAMES.ADMIN_USERS, icon: 'Settings' },
]
