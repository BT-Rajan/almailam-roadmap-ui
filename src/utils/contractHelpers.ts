import type { BadgeVariant } from '@/types/Ui'
import type { ContractStatus } from '@/types/Contract'

const STATUS_VARIANTS: Record<ContractStatus, BadgeVariant> = {
  Draft: 'primary',
  Signed: 'success',
  Active: 'success',
  Expired: 'neutral',
  Terminated: 'danger',
}

export function getContractStatusVariant(status: ContractStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

