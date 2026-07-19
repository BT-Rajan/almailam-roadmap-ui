import type { BadgeVariant } from '@/types/Ui'
import type { Contract, ContractStatus } from '@/types/Contract'

const STATUS_VARIANTS: Record<ContractStatus, BadgeVariant> = {
  Draft: 'primary',
  Sent: 'info',
  Signed: 'success',
  Active: 'success',
  Expired: 'neutral',
  Terminated: 'danger',
}

export function getContractStatusVariant(status: ContractStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function isContractExpiringSoon(contract: Contract, withinDays = 30): boolean {
  const expiry = new Date(contract.expiryDate).getTime()
  const now = Date.now()
  const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)
  return daysUntilExpiry >= 0 && daysUntilExpiry <= withinDays
}
