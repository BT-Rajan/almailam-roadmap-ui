// A contract revision beyond R0 -- one row per actual scope change,
// see backend/app/models/contract.py's ContractRevision.
export interface ScopeDeviation {
  revision: string
  date: string
  changedBy: string
  summary: string
}

// Backs the Completion summary shown on a project's Overview tab.
// Budget is derived server-side from the existing financial agreement +
// payments received (see backend/app/services/project_service.py's
// get_completion_summary) -- never a second, hand-typed number that
// could drift from what Payments actually shows. scopeDeviations is
// likewise derived live from contract revisions, never hand-typed;
// deviationNotes is the PM's own annotation layered on top of that
// auto-derived read, distinct from the general handover/lessons-
// learned `notes` field.
export interface ProjectCompletionSummary {
  plannedBudget: number | null
  actualBudget: number | null
  plannedDurationDays: number
  actualDurationDays: number | null
  completedAt: string | null
  notes: string | null
  scopeDeviations: ScopeDeviation[]
  deviationNotes: string | null
}

export interface CompletionChecklistItem {
  complete: boolean
  detail: string
}

// Mirrors backend project_service.get_completion_checklist exactly --
// contract/payments/design/governmentApproval/fieldWork, each with a
// pass/fail flag and a short human-readable reason. Deliberately a
// separate type from ProjectCompletionSummary above (budget/duration),
// a genuinely different question, not a replacement for it.
export interface ProjectCompletionChecklist {
  contract: CompletionChecklistItem
  payments: CompletionChecklistItem
  design: CompletionChecklistItem
  governmentApproval: CompletionChecklistItem
  fieldWork: CompletionChecklistItem
}
