import { ROLE_DEFINITIONS } from '@/mock/roleDefinitions'
import { USERS } from '@/mock/users'
import type { RoleDefinition } from '@/types/Role'
import type { AppUser } from '@/types/User'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getUsers(): Promise<AppUser[]> {
  await simulateNetworkDelay()
  return [...USERS]
}

async function getRoleDefinitions(): Promise<RoleDefinition[]> {
  await simulateNetworkDelay()
  return [...ROLE_DEFINITIONS]
}

async function createUser(user: AppUser): Promise<AppUser> {
  await simulateNetworkDelay(200)
  USERS.unshift(user)
  return user
}

async function updateUser(user: AppUser): Promise<AppUser> {
  await simulateNetworkDelay(200)
  const index = USERS.findIndex((existing) => existing.id === user.id)
  if (index !== -1) USERS[index] = user
  return user
}

async function setUserStatus(userId: string, status: AppUser['status']): Promise<void> {
  await simulateNetworkDelay(150)
  const user = USERS.find((existing) => existing.id === userId)
  if (user) user.status = status
}

export const userService = {
  getUsers,
  getRoleDefinitions,
  createUser,
  updateUser,
  setUserStatus,
}
