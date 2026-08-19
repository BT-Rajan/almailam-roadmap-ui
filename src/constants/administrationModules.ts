import { ROUTE_NAMES } from '@/constants/routeNames'
import type { RouteNameValue } from '@/types/Route'

export interface AdministrationModule {
  label: string
  description: string
  icon: string
  routeName: RouteNameValue
}

export const ADMINISTRATION_MODULES: AdministrationModule[] = [
  {
    label: 'User Management',
    description: 'Manage users, roles, and permissions across the firm.',
    icon: 'Users',
    routeName: ROUTE_NAMES.ADMIN_USERS,
  },
  {
    label: 'Workflow Configuration',
    description: 'Define and adjust the project workflow stages.',
    icon: 'Workflow',
    routeName: ROUTE_NAMES.ADMIN_WORKFLOWS,
  },
  {
    label: 'Service Catalog',
    description: 'Configure services and their activities, each with a fixed cost.',
    icon: 'ListChecks',
    routeName: ROUTE_NAMES.ADMIN_SERVICE_CATALOG,
  },
  {
    label: 'Government Forms Management',
    description: 'Maintain government forms, authorities, and document requirements.',
    icon: 'Landmark',
    routeName: ROUTE_NAMES.ADMIN_FORMS,
  },
  {
    label: 'AI Configuration',
    description: 'Configure AI providers, prompt templates, and cache settings.',
    icon: 'Bot',
    routeName: ROUTE_NAMES.ADMIN_AI,
  },
  {
    label: 'Company Settings',
    description: 'Update company profile, branding, and application preferences.',
    icon: 'Building2',
    routeName: ROUTE_NAMES.ADMIN_COMPANY,
  },
  {
    label: 'Audit Log',
    description: 'Review every tracked change across the system, who made it, and when.',
    icon: 'History',
    routeName: ROUTE_NAMES.ADMIN_AUDIT_LOG,
  },
  {
    label: 'Activity Calendar',
    description: 'View team activities, updates, and changes across projects in calendar view.',
    icon: 'Calendar',
    routeName: ROUTE_NAMES.ADMIN_ACTIVITY_CALENDAR,
  },
]
