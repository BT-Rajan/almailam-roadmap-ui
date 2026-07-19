import type { DocumentAIReview } from '@/types/AiReview'

export const AI_DOCUMENT_REVIEWS: DocumentAIReview[] = [
  {
    documentId: 'DOC-2026-001',
    summary: 'Structural framing plan for Al Reem Residential Tower, approved for permit submission.',
    details:
      'The drawing defines the column grid, beam layout and slab framing for the tower structure. Dimensions and load paths are consistent with the referenced calculation sheet. No conflicts were found between the framing plan and the architectural layout.',
    confidence: 'high',
    extractedFields: [
      { label: 'Sheet Number', value: 'S-101', confidence: 'high' },
      { label: 'Scale', value: '1:100', confidence: 'high' },
      { label: 'Discipline', value: 'Structural', confidence: 'high' },
    ],
    suggestions: ['Attach to government submission package', 'Notify project engineer of approval'],
  },
  {
    documentId: 'DOC-2026-002',
    summary: 'Soil investigation report identifies moderate bearing capacity across the site.',
    details:
      'Borehole results indicate a medium-dense sandy soil profile with a bearing capacity suitable for shallow foundations. The water table was recorded below the expected excavation depth, reducing dewatering requirements.',
    confidence: 'medium',
    extractedFields: [
      { label: 'Bearing Capacity', value: '150 kPa', confidence: 'medium' },
      { label: 'Water Table Depth', value: '6.2 m', confidence: 'medium' },
      { label: 'Soil Type', value: 'Sandy Clay', confidence: 'high' },
    ],
    suggestions: ['Review manually before finalizing foundation design', 'Confirm findings with structural engineer'],
  },
  {
    documentId: 'DOC-2026-003',
    summary: 'MEP design services agreement covers full scope with standard liability clauses.',
    details:
      'The agreement outlines design responsibilities, payment milestones and termination conditions. Liability is capped in line with standard consultancy terms. No unusual clauses were detected.',
    confidence: 'high',
    extractedFields: [
      { label: 'Contract Value', value: 'AED 185,000', confidence: 'high' },
      { label: 'Payment Terms', value: '30 days from invoice', confidence: 'high' },
      { label: 'Duration', value: '6 months', confidence: 'medium' },
    ],
    suggestions: ['Archive signed copy in project records'],
  },
  {
    documentId: 'DOC-2026-004',
    summary: 'Draft cost quotation for the warehouse expansion is awaiting internal approval.',
    details:
      'The quotation itemizes design, supervision and inspection fees. The validity period is short relative to typical client review cycles, which may require an extension before submission.',
    confidence: 'medium',
    extractedFields: [
      { label: 'Total Amount', value: 'AED 92,400', confidence: 'high' },
      { label: 'Validity', value: '15 days', confidence: 'medium' },
      { label: 'Currency', value: 'AED', confidence: 'high' },
    ],
    suggestions: ['Review manually before sending to client', 'Consider extending quotation validity'],
  },
  {
    documentId: 'DOC-2026-005',
    summary: 'Hotel renovation elevation drawings updated per municipality feedback.',
    details:
      'Facade heights and setback lines have been corrected to match the latest municipality comments. Material callouts are consistent across all elevation views.',
    confidence: 'medium',
    extractedFields: [
      { label: 'Sheet Number', value: 'A-204', confidence: 'high' },
      { label: 'Scale', value: '1:50', confidence: 'high' },
      { label: 'Discipline', value: 'Architectural', confidence: 'medium' },
    ],
    suggestions: ['Confirm revised heights with municipality reviewer', 'Update project drawing register'],
  },
  {
    documentId: 'DOC-2026-006',
    summary: 'HVAC cooling load calculation confirms system sizing for the renovated hotel.',
    details:
      'Cooling loads were calculated per zone using ASHRAE methodology. Peak load values align with the proposed chiller capacity with adequate design margin.',
    confidence: 'high',
    extractedFields: [
      { label: 'Total Cooling Load', value: '420 TR', confidence: 'high' },
      { label: 'Standard Reference', value: 'ASHRAE 90.1', confidence: 'high' },
      { label: 'Zones Covered', value: '12', confidence: 'medium' },
    ],
    suggestions: ['Attach to design package for client review'],
  },
  {
    documentId: 'DOC-2026-007',
    summary: 'Municipality submission form was rejected due to incomplete applicant details.',
    details:
      'The authority flagged missing applicant identification fields and an outdated project reference number. The corrected revision addresses the identification fields but the reference number still requires verification.',
    confidence: 'low',
    extractedFields: [
      { label: 'Application Number', value: 'FSA-88213', confidence: 'medium' },
      { label: 'Authority', value: 'Civil Defence Directorate', confidence: 'high' },
      { label: 'Submission Date', value: '11 Jul 2026', confidence: 'high' },
    ],
    suggestions: ['Review manually before resubmission', 'Verify project reference number with authority', 'Contact customer for updated documents'],
  },
  {
    documentId: 'DOC-2026-008',
    summary: 'Fire suppression system report is under review pending coverage confirmation.',
    details:
      'The report describes a sprinkler and gas suppression combination sized for the industrial facility. Coverage in the eastern storage zone appears lower than the recommended density and should be verified.',
    confidence: 'medium',
    extractedFields: [
      { label: 'Coverage Area', value: '4,200 sqm', confidence: 'medium' },
      { label: 'System Type', value: 'Wet Sprinkler + FM200', confidence: 'high' },
      { label: 'Compliance Standard', value: 'NFPA 13', confidence: 'high' },
    ],
    suggestions: ['Review manually before authority submission', 'Verify coverage density in eastern storage zone'],
  },
  {
    documentId: 'DOC-2026-009',
    summary: 'Final handover contract addendum is signed and consistent with the original agreement.',
    details:
      'The addendum extends the maintenance period and clarifies defect liability responsibilities. Terms are consistent with the original contract and no conflicting clauses were identified.',
    confidence: 'high',
    extractedFields: [
      { label: 'Effective Date', value: '28 May 2026', confidence: 'high' },
      { label: 'Parties', value: 'Almailam Engineering, Desert Rose Retail Properties', confidence: 'high' },
      { label: 'Amendment Scope', value: 'Maintenance period extension', confidence: 'medium' },
    ],
    suggestions: ['Archive signed copy in project records'],
  },
  {
    documentId: 'DOC-2026-010',
    summary: 'Structural load calculations for the retail plaza are approved for handover.',
    details:
      'Load calculations cover dead, live and wind loads with an adequate safety factor per the referenced design code. Results are consistent with the as-built structural drawings.',
    confidence: 'high',
    extractedFields: [
      { label: 'Total Load', value: '3.8 kN/sqm', confidence: 'high' },
      { label: 'Safety Factor', value: '1.5', confidence: 'high' },
      { label: 'Standard Reference', value: 'ASCE 7', confidence: 'medium' },
    ],
    suggestions: ['Attach to project handover package'],
  },
]
