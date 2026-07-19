import type { ContractAISummary } from '@/types/Contract'

export const CONTRACT_AI_SUMMARIES: ContractAISummary[] = [
  {
    contractId: 'CON-2026-011',
    summary:
      'Active MEP consultancy agreement worth AED 108,675 with standard three-installment payment terms and a 12-week delivery window.',
    details:
      'This contract covers HVAC, electrical, and firefighting design for the Falcon Heights Warehouse Expansion. Payment is split 40/40/20 across signing, drawing submission, and authority approval. It includes a standard 30-day termination clause and a confidentiality obligation covering all project drawings and commercial terms. Revision R1 updated the payment terms to reflect the final negotiated quotation amount.',
    confidence: 'high',
    suggestions: [
      'Confirm the 12-week timeline against the current project schedule',
      'Verify signed date is recorded in the project timeline',
      'Check expiry date ahead of renewal planning',
    ],
  },
  {
    contractId: 'CON-2026-007',
    summary:
      'Signed architectural renovation agreement worth AED 149,625, excluding interior fit-out execution, with IP rights retained until full payment.',
    details:
      'This contract governs concept design, renovation drawings, 3D visualization, and authority coordination for the Marina Bay Hotel Renovation. Payment follows a 50/30/20 split. Notably, intellectual property in the drawings remains with the Consultant until payment is complete, which should be highlighted to the finance team when invoicing milestones.',
    confidence: 'high',
    suggestions: [
      'Flag the IP transfer clause to finance before final invoicing',
      'Verify interior fit-out exclusion is reflected in the project scope',
    ],
  },
  {
    contractId: 'CON-2025-042',
    summary:
      'Expired handover consultancy contract worth AED 64,000, closed out across three revisions before signature.',
    details:
      'This contract covered as-built documentation and completion certificate coordination for the Desert Rose Retail Plaza. Full payment was due within 15 days of certificate issuance. Three revisions were required, primarily around warranty language, before the client representative signed the final version. The contract has since expired and the project is complete.',
    confidence: 'medium',
    suggestions: [
      'Archive this contract now that the project has completed',
      'Review warranty clause wording for future retail handover templates',
    ],
  },
]
