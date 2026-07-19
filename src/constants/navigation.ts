import { ROUTE_NAMES } from '@/constants/routeNames'
import type { NavItem } from '@/types/Navigation'

export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD, icon: 'LayoutDashboard', matchPath: '/dashboard' },
  { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS, icon: 'FolderKanban', matchPath: '/projects' },
  {
    label: 'Government Center',
    routeName: ROUTE_NAMES.GOVERNMENT_FORMS,
    icon: 'Landmark',
    matchPath: '/government',
  },
  { label: 'Documents', routeName: ROUTE_NAMES.DOCUMENTS, icon: 'FileText', matchPath: '/documents' },
  { label: 'Tasks', routeName: ROUTE_NAMES.TASKS, icon: 'ListChecks', matchPath: '/tasks' },
  { label: 'Reports', routeName: ROUTE_NAMES.REPORTS, icon: 'BarChart3', matchPath: '/reports' },
  {
    label: 'Administration',
    routeName: ROUTE_NAMES.ADMIN_USERS,
    icon: 'Settings',
    matchPath: '/admin',
  },
]
