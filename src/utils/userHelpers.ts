import type { BadgeVariant } from '@/types/Ui'
import type { UserRole, UserStatus } from '@/types/User'

const STATUS_VARIANTS: Record<UserStatus, BadgeVariant> = {
  Active: 'success',
  Inactive: 'neutral',
}

const ROLE_VARIANTS: Record<UserRole, BadgeVariant> = {
  Administrator: 'ai',
  'Project Manager': 'primary',
  Engineer: 'info',
  'Document Controller': 'warning',
  Viewer: 'neutral',
}

export function getUserStatusVariant(status: UserStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getUserRoleVariant(role: UserRole): BadgeVariant {
  return ROLE_VARIANTS[role]
}
