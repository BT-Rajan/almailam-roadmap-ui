import type { Contract } from '@/types/Contract'

export const CONTRACTS: Contract[] = [
  {
    id: 'CON-2026-011',
    projectId: 'PRJ-2026-002',
    contractNo: 'CON-2026-011',
    templateName: 'Standard Engineering Consultancy Agreement',
    revision: 'R1',
    currency: 'KWD',
    contractValue: 10867.5,
    issueDate: '2026-05-29',
    signedDate: '2026-06-02',
    expiryDate: '2027-06-01',
    status: 'Active',
    preparedBy: 'Ahmed Rashid',
    clientRepresentative: 'Omar Al Farsi',
    scopeSummary:
      'MEP design consultancy covering HVAC, electrical, and firefighting systems for the Falcon Heights Warehouse Expansion, including government authority coordination.',
    clauses: [
      {
        id: 'CL-001',
        title: 'Scope of Services',
        content:
          'The Consultant shall provide MEP design services including concept design, detailed drawings, load calculations, and authority submission support as defined in the approved quotation QUO-2026-015.',
      },
      {
        id: 'CL-002',
        title: 'Payment Terms',
        content:
          'Payment shall be made in three installments: 40% advance upon signing, 40% upon submission of design drawings, and 20% upon final authority approval.',
      },
      {
        id: 'CL-003',
        title: 'Project Timeline',
        content:
          'The Consultant shall complete all deliverables within 12 weeks from the effective date, subject to timely client feedback and authority processing times.',
      },
      {
        id: 'CL-004',
        title: 'Confidentiality',
        content:
          'Both parties agree to keep all project information, drawings, and commercial terms confidential and shall not disclose them to third parties without written consent.',
      },
      {
        id: 'CL-005',
        title: 'Termination',
        content:
          'Either party may terminate this agreement with 30 days written notice. Fees for work completed up to the termination date remain payable.',
      },
    ],
    revisions: [
      {
        id: 'REV-001',
        revision: 'R0',
        date: '2026-05-29',
        changedBy: 'Ahmed Rashid',
        summary: 'Initial contract drafted from the Standard Engineering Consultancy Agreement template.',
      },
      {
        id: 'REV-002',
        revision: 'R1',
        date: '2026-06-01',
        changedBy: 'Layla Haddad',
        summary: 'Updated payment terms clause to reflect the revised quotation amount after client negotiation.',
      },
    ],
  },
  {
    id: 'CON-2026-007',
    projectId: 'PRJ-2026-003',
    contractNo: 'CON-2026-007',
    templateName: 'Architectural Renovation Agreement',
    revision: 'R0',
    currency: 'KWD',
    contractValue: 14962.5,
    issueDate: '2026-03-18',
    signedDate: '2026-03-22',
    expiryDate: '2027-03-21',
    status: 'Signed',
    preparedBy: 'Layla Haddad',
    clientRepresentative: 'Nadia Suleiman',
    scopeSummary:
      'Full architectural renovation design consultancy for the Marina Bay Hotel Renovation, covering concept design through authority coordination, excluding interior fit-out execution.',
    clauses: [
      {
        id: 'CL-006',
        title: 'Scope of Services',
        content:
          'The Consultant shall provide architectural concept design, interior renovation drawings, 3D visualization, and authority coordination services as approved in quotation QUO-2026-009.',
      },
      {
        id: 'CL-007',
        title: 'Payment Terms',
        content:
          'Payment shall be made in three installments: 50% advance upon signing, 30% upon submission of design drawings, and 20% upon final authority approval.',
      },
      {
        id: 'CL-008',
        title: 'Intellectual Property',
        content:
          'All design drawings and documents remain the intellectual property of the Consultant until full payment is received, after which usage rights transfer to the Client.',
      },
      {
        id: 'CL-009',
        title: 'Termination',
        content:
          'Either party may terminate this agreement with 30 days written notice. Fees for work completed up to the termination date remain payable.',
      },
    ],
    revisions: [
      {
        id: 'REV-003',
        revision: 'R0',
        date: '2026-03-18',
        changedBy: 'Layla Haddad',
        summary: 'Initial contract drafted and issued for client signature.',
      },
    ],
  },
  {
    id: 'CON-2025-042',
    projectId: 'PRJ-2026-005',
    contractNo: 'CON-2025-042',
    templateName: 'Standard Engineering Consultancy Agreement',
    revision: 'R2',
    currency: 'KWD',
    contractValue: 6400,
    issueDate: '2025-11-10',
    signedDate: '2025-11-16',
    expiryDate: '2026-06-30',
    status: 'Expired',
    preparedBy: 'Ahmed Rashid',
    clientRepresentative: 'Fatima Al Zahra',
    scopeSummary:
      'Final handover consultancy services for the Desert Rose Retail Plaza, covering as-built documentation and completion certificate coordination.',
    clauses: [
      {
        id: 'CL-010',
        title: 'Scope of Services',
        content:
          'The Consultant shall prepare as-built drawings and coordinate with relevant authorities to secure the completion certificate for the retail plaza.',
      },
      {
        id: 'CL-011',
        title: 'Payment Terms',
        content: 'Payment of the full contract value is due within 15 days of completion certificate issuance.',
      },
      {
        id: 'CL-012',
        title: 'Warranty',
        content:
          'The Consultant warrants that all documentation provided is accurate and complete to the best of its professional knowledge at the time of handover.',
      },
    ],
    revisions: [
      {
        id: 'REV-004',
        revision: 'R0',
        date: '2025-11-10',
        changedBy: 'Ahmed Rashid',
        summary: 'Initial contract drafted from the Standard Engineering Consultancy Agreement template.',
      },
      {
        id: 'REV-005',
        revision: 'R1',
        date: '2025-11-14',
        changedBy: 'Ahmed Rashid',
        summary: 'Adjusted warranty clause language following client legal review.',
      },
      {
        id: 'REV-006',
        revision: 'R2',
        date: '2025-11-16',
        changedBy: 'Fatima Al Zahra',
        summary: 'Final revision incorporating agreed handover date before signature.',
      },
    ],
  },
]
