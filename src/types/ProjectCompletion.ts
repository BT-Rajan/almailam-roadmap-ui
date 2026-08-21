// Backs the Completion summary shown on a project's Overview tab.
// Budget is derived server-side from the existing financial agreement +
// payments received (see backend/app/services/project_service.py's
// get_completion_summary) -- never a second, hand-typed number that
// could drift from what Payments actually shows.
export interface ProjectCompletionSummary {
  plannedBudget: number | null
  actualBudget: number | null
  plannedDurationDays: number
  actualDurationDays: number | null
  completedAt: string | null
  notes: string | null
}
