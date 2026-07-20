import type { ClientIdentification } from '@/types/Client'

export const CLIENT_IDENTIFICATIONS: ClientIdentification[] = [
  {
    id: 'IDN-001',
    clientId: 'CLT-006',
    documentType: 'Emirates ID',
    documentNumber: '784-1985-1234567-1',
    issueDate: '2022-01-15',
    expiryDate: '2027-01-14',
    issuingCountry: 'United Arab Emirates',
  },
  {
    id: 'IDN-002',
    clientId: 'CLT-007',
    documentType: 'Passport',
    documentNumber: 'N4471829',
    issueDate: '2019-07-02',
    expiryDate: '2029-07-01',
    issuingCountry: 'India',
  },
  {
    id: 'IDN-003',
    clientId: 'CLT-001',
    documentType: 'Trade Licence',
    documentNumber: 'TL-778210',
    issueDate: '2024-01-01',
    expiryDate: '2026-12-31',
    issuingCountry: 'United Arab Emirates',
  },
]
