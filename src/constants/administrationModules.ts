import { ROUTE_NAMES } from '@/constants/routeNames'
import type { RouteNameValue } from '@/types/Route'

export interface AdministrationModule {
  label: string
  labelKey: string
  description: string
  descriptionKey: string
  icon: string
  routeName: RouteNameValue
}

export interface AdministrationModuleGroup {
  label: string
  labelKey: string
  description: string
  descriptionKey: string
  modules: AdministrationModule[]
}

export const ADMINISTRATION_MODULE_GROUPS: AdministrationModuleGroup[] = [
  {
    label: 'People & Access',
    labelKey: 'administrationModules.groups.peopleAccess.label',
    description: 'Who can sign in and what they can do once they are in.',
    descriptionKey: 'administrationModules.groups.peopleAccess.description',
    modules: [
      {
        label: 'User Management',
        labelKey: 'administrationModules.modules.userManagement.label',
        description: 'Manage users, roles, and permissions across the firm.',
        descriptionKey: 'administrationModules.modules.userManagement.description',
        icon: 'Users',
        routeName: ROUTE_NAMES.ADMIN_USERS,
      },
    ],
  },
  {
    label: 'Catalogs',
    labelKey: 'administrationModules.groups.catalogs.label',
    description: 'The priced building blocks every project is set up from.',
    descriptionKey: 'administrationModules.groups.catalogs.description',
    modules: [
      {
        label: 'Catalogs',
        labelKey: 'administrationModules.modules.catalogs.label',
        description: 'Configure the Services catalog (Design and Supervision branches) and the permit catalog -- each in its own tab.',
        descriptionKey: 'administrationModules.modules.catalogs.description',
        icon: 'ListChecks',
        routeName: ROUTE_NAMES.ADMIN_CATALOGS,
      },
    ],
  },
  {
    label: 'Documents',
    labelKey: 'administrationModules.groups.documents.label',
    description: 'Government forms, authorities, and how they map to services.',
    descriptionKey: 'administrationModules.groups.documents.description',
    modules: [
      {
        label: 'Documents',
        labelKey: 'administrationModules.modules.documents.label',
        description: 'Manage government forms and authorities, and the service document map -- each in its own tab.',
        descriptionKey: 'administrationModules.modules.documents.description',
        icon: 'Landmark',
        routeName: ROUTE_NAMES.ADMIN_DOCUMENTS,
      },
    ],
  },
  {
    label: 'System Configuration',
    labelKey: 'administrationModules.groups.systemConfiguration.label',
    description: 'Firm-wide settings and integrations.',
    descriptionKey: 'administrationModules.groups.systemConfiguration.description',
    modules: [
      {
        label: 'Knowledgebase AI',
        labelKey: 'administrationModules.modules.knowledgebaseAi.label',
        description: 'Configure the knowledgebase Q&A provider, grounding prompt, and cache settings.',
        descriptionKey: 'administrationModules.modules.knowledgebaseAi.description',
        icon: 'Bot',
        routeName: ROUTE_NAMES.ADMIN_AI,
      },
      {
        label: 'Company Settings',
        labelKey: 'administrationModules.modules.companySettings.label',
        description: 'Update company profile, branding, and application preferences.',
        descriptionKey: 'administrationModules.modules.companySettings.description',
        icon: 'Building2',
        routeName: ROUTE_NAMES.ADMIN_COMPANY,
      },
    ],
  },
  {
    label: 'Monitoring & History',
    labelKey: 'administrationModules.groups.monitoringHistory.label',
    description: 'Track what changed across the system and when.',
    descriptionKey: 'administrationModules.groups.monitoringHistory.description',
    modules: [
      {
        label: 'Audit Log',
        labelKey: 'administrationModules.modules.auditLog.label',
        description: 'Review every tracked change across the system, who made it, and when.',
        descriptionKey: 'administrationModules.modules.auditLog.description',
        icon: 'History',
        routeName: ROUTE_NAMES.ADMIN_AUDIT_LOG,
      },
      {
        label: 'Activity Calendar',
        labelKey: 'administrationModules.modules.activityCalendar.label',
        description: 'View team activities, updates, and changes across projects in calendar view.',
        descriptionKey: 'administrationModules.modules.activityCalendar.description',
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
