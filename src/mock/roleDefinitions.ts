import type { RoleDefinition } from '@/types/Role'

export const ROLE_DEFINITIONS: RoleDefinition[] = [
  {
    role: 'Administrator',
    description: 'Full access to every module, including administration and system configuration.',
    permissions: [
      { module: 'Projects', view: true, edit: true, delete: true },
      { module: 'Documents', view: true, edit: true, delete: true },
      { module: 'Government', view: true, edit: true, delete: true },
      { module: 'Reports', view: true, edit: true, delete: true },
      { module: 'Administration', view: true, edit: true, delete: true },
    ],
  },
  {
    role: 'Project Manager',
    description: 'Manages project delivery, documents, government submissions, and reporting.',
    permissions: [
      { module: 'Projects', view: true, edit: true, delete: false },
      { module: 'Documents', view: true, edit: true, delete: false },
      { module: 'Government', view: true, edit: true, delete: false },
      { module: 'Reports', view: true, edit: true, delete: false },
      { module: 'Administration', view: false, edit: false, delete: false },
    ],
  },
  {
    role: 'Engineer',
    description: 'Works on assigned projects and documents, with read access to government tracking.',
    permissions: [
      { module: 'Projects', view: true, edit: true, delete: false },
      { module: 'Documents', view: true, edit: true, delete: false },
      { module: 'Government', view: true, edit: false, delete: false },
      { module: 'Reports', view: true, edit: false, delete: false },
      { module: 'Administration', view: false, edit: false, delete: false },
    ],
  },
  {
    role: 'Document Controller',
    description: 'Maintains the document repository and revision history across projects.',
    permissions: [
      { module: 'Projects', view: true, edit: false, delete: false },
      { module: 'Documents', view: true, edit: true, delete: true },
      { module: 'Government', view: true, edit: false, delete: false },
      { module: 'Reports', view: false, edit: false, delete: false },
      { module: 'Administration', view: false, edit: false, delete: false },
    ],
  },
  {
    role: 'Viewer',
    description: 'Read-only access for stakeholders who need visibility without edit rights.',
    permissions: [
      { module: 'Projects', view: true, edit: false, delete: false },
      { module: 'Documents', view: true, edit: false, delete: false },
      { module: 'Government', view: true, edit: false, delete: false },
      { module: 'Reports', view: true, edit: false, delete: false },
      { module: 'Administration', view: false, edit: false, delete: false },
    ],
  },
]
