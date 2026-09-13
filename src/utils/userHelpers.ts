import type { BadgeVariant } from '@/types/Ui'
import type { AppUser, UserRole, UserStatus } from '@/types/User'

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
  Customer: 'neutral',
}

export function getUserStatusVariant(status: UserStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getUserRoleVariant(role: UserRole): BadgeVariant {
  return ROLE_VARIANTS[role]
}

/** Prefixes a user's stored Mr./Ms. (see backend migration 0096) ahead
 * of their name -- unset for most existing users until an admin fills
 * it in on each profile, so this falls back to the bare name exactly
 * like it printed before the field existed. */
export function withSalutation(user: Pick<AppUser, 'name' | 'salutation'>): string {
  return user.salutation ? `${user.salutation} ${user.name}` : user.name
}

/** Same as withSalutation, but for a project.engineer/task.assignedTo
 * plain name string with no User object at hand -- resolves it against
 * a loaded user list by name (the same name-matching convention those
 * fields already rely on elsewhere, e.g. ProjectEditDialog.vue). */
export function withSalutationByName(name: string, users: AppUser[]): string {
  const match = users.find((user) => user.name === name)
  return match ? withSalutation(match) : name
}
