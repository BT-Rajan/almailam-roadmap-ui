import type { GovernmentAuthority } from '@/types/Government'

export const GOVERNMENT_AUTHORITIES: GovernmentAuthority[] = [
  {
    id: 'AUTH-001',
    name: 'Kuwait Municipality',
    category: 'Municipality',
    website: 'https://www.baladia.gov.kw',
    description: 'Responsible for building permits, land use approvals and urban planning across Kuwait.',
  },
  {
    id: 'AUTH-002',
    name: 'Kuwait Fire Force',
    category: 'Fire Department',
    website: 'https://www.kfsd.gov.kw',
    description: 'Reviews and approves fire safety systems, evacuation plans and life safety compliance.',
  },
  {
    id: 'AUTH-003',
    name: 'Ministry of Electricity, Water and Renewable Energy',
    category: 'Electricity',
    website: 'https://www.mew.gov.kw',
    description: 'Manages electricity connection approvals and power load clearances for new developments.',
  },
  {
    id: 'AUTH-004',
    name: 'MEW Water Directorate',
    category: 'Water',
    website: 'https://www.mew.gov.kw',
    description: 'Handles potable water connection requests and network capacity approvals.',
  },
  {
    id: 'AUTH-005',
    name: 'Environment Public Authority',
    category: 'Environment',
    website: 'https://www.epa.org.kw',
    description: 'Issues environmental clearances and monitors compliance for construction and industrial projects.',
  },
]
