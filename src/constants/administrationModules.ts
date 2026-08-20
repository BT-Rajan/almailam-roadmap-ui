import { ROUTE_NAMES } from '@/constants/routeNames'
import type { RouteNameValue } from '@/types/Route'

export interface AdministrationModule {
  label: string
  description: string
  icon: string
  routeName: RouteNameValue
}

export interface AdministrationModuleGroup {
  label: string
  description: string
  modules: AdministrationModule[]
}

export const ADMINISTRATION_MODULE_GROUPS: AdministrationModuleGroup[] = [
  {
    label: 'People & Access',
    description: 'Who can sign in and what they can do once they are in.',
    modules: [
      {
        label: 'User Management',
        description: 'Manage users, roles, and permissions across the firm.',
        icon: 'Users',
        routeName: ROUTE_NAMES.ADMIN_USERS,
      },
    ],
  },
  {
    label: 'Project Configuration',
    description: 'The building blocks every project is set up from.',
    modules: [
      {
        label: 'Workflow Configuration',
        description: 'Define and adjust the project workflow stages.',
        icon: 'Workflow',
        routeName: ROUTE_NAMES.ADMIN_WORKFLOWS,
      },
      {
        label: 'Execution Steps',
        description: 'Define the linear, weighted checklist every project follows.',
        icon: 'ListOrdered',
        routeName: ROUTE_NAMES.ADMIN_EXECUTION_STEPS,
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
    ],
  },
  {
    label: 'System Configuration',
    description: 'Firm-wide settings and integrations.',
    modules: [
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
    ],
  },
  {
    label: 'Monitoring & History',
    description: 'Track what changed across the system and when.',
    modules: [
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
    ],
  },
]

// Flat list of every module across all groups -- kept for anything that
// needs to search/filter/count modules without caring about grouping.
export const ADMINISTRATION_MODULES: AdministrationModule[] = ADMINISTRATION_MODULE_GROUPS.flatMap(
  (group) => group.modules,
)
