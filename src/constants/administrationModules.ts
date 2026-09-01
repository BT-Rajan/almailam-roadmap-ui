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
    label: 'Catalogs',
    description: 'The priced building blocks every project is set up from.',
    modules: [
      {
        label: 'Catalogs',
        description: 'Configure the Services catalog (Design and Supervision branches) and the permit catalog -- each in its own tab.',
        icon: 'ListChecks',
        routeName: ROUTE_NAMES.ADMIN_CATALOGS,
      },
    ],
  },
  {
    label: 'Documents',
    description: 'Government forms, authorities, and how they map to services.',
    modules: [
      {
        label: 'Documents',
        description: 'Manage government forms and authorities, and the service document map -- each in its own tab.',
        icon: 'Landmark',
        routeName: ROUTE_NAMES.ADMIN_DOCUMENTS,
      },
    ],
  },
  {
    label: 'System Configuration',
    description: 'Firm-wide settings and integrations.',
    modules: [
      {
        label: 'Knowledgebase AI',
        description: 'Configure the knowledgebase Q&A provider, grounding prompt, and cache settings.',
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
