// Admin-defined, reusable document reference list per Design/Permit/
// Supervision catalog activity -- see document_requirement_service.py.
// DocumentRequirement/DocumentRequirementLink below are still purely
// catalog-level; ChecklistItem further down is the per-project state
// that actually gates closing a Design activity/Permit/Supervision
// activity and moving a project into Handover (#4/#5).
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

// One row of a project's own Design activity/Permit/Supervision
// activity handover document checklist -- a DocumentRequirementLink
// plus this project's own fulfillment state for it (see
// ProjectDocumentRequirementFulfillment). Checking this off requires
// completing it before the activity/permit can be marked Complete
// (project_service.assert_checklist_fulfilled), unless the same
// "override, no document" checkbox close_design_activity/
// set_permit_status/set_supervision_status already offer is ticked --
// except at Handover itself, which never accepts that override (see
// _assert_stage_exit_criteria).
export interface ChecklistItem {
  id: string
  requirementId: string
  requirementName: string
  requirementDescription?: string | null
  fulfilled: boolean
  fulfilledAt?: string | null
  fulfilledByName?: string | null
  documentId?: string | null
}
