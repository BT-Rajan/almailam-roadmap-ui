// Admin-defined, reusable, informational-only document reference list
// per Design/Permit/Supervision catalog activity -- see
// document_requirement_service.py. Nothing here is enforced against
// task/activity closure; it only surfaces as a reference checklist.
export interface DocumentRequirement {
  id: string
  name: string
  description?: string | null
}

export type DocumentRequirementTargetType = 'Design' | 'Permit' | 'Supervision'

export interface DocumentRequirementLink {
  id: string
  requirementId: string
  requirementName: string
  requirementDescription?: string | null
  targetType: DocumentRequirementTargetType
  // The target's own catalog display id -- "ACT-004" for Design/
  // Supervision, "PER-003" for Permit.
  targetCatalogId: string
}
