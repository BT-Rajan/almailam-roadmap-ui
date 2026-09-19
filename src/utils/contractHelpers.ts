import type { BadgeVariant } from '@/types/Ui'
import type { ContractStatus } from '@/types/Contract'
import type { Project } from '@/types/Project'

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


/** A start/end pair for one of the contract's two work streams. */
export interface ContractPeriod {
  start: string
  end: string
}

/** The Design & Permit window shown on a contract -- the project's own
 * Start Date and Target Completion Date, filled in automatically (never
 * typed on the contract). undefined for a Supervision-only project,
 * which has no Design or Permit work to date. */
export function getDesignPermitPeriod(project: Pick<Project, 'startDate' | 'targetDate' | 'includesDesign' | 'includesGovernmentSubmission' | 'includesSupervision'>): ContractPeriod | undefined {
  const hasDesignOrPermit = project.includesDesign || project.includesGovernmentSubmission
  if (!hasDesignOrPermit && project.includesSupervision) return undefined
  return { start: project.startDate, end: project.targetDate }
}

/** The Supervision window shown on a contract -- the project's overall
 * Supervision start/end, falling back to the earliest start and latest
 * end across its selected Supervision activities when the overall
 * window was never captured. undefined when the project has no
 * Supervision. */
export function getSupervisionPeriod(project: Pick<Project, 'supervisionStartDate' | 'supervisionEndDate' | 'selectedSupervisionActivities' | 'includesSupervision'>): ContractPeriod | undefined {
  const activities = project.selectedSupervisionActivities ?? []
  if (!project.includesSupervision && activities.length === 0) return undefined
  const starts = activities.map((activity) => activity.startDate).filter(Boolean)
  const ends = activities.map((activity) => activity.endDate).filter(Boolean)
  const start = project.supervisionStartDate || (starts.length > 0 ? starts.reduce((a, b) => (a < b ? a : b)) : '')
  const end = project.supervisionEndDate || (ends.length > 0 ? ends.reduce((a, b) => (a > b ? a : b)) : '')
  return { start, end }
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** One paragraph per scope line. Scope Summary is rich text (rendered
 * with v-html and edited in RichTextEditor), so plain lines joined with
 * "\n" would collapse into a single run-on line -- this keeps each
 * line on its own row everywhere it's shown. */
export function scopeSummaryToHtml(lines: string[]): string {
  return lines
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => `<p>${escapeHtml(line)}</p>`)
    .join('')
}

/** True when rich-text HTML has no visible content -- an emptied
 * contenteditable still leaves markup behind (`<br>`, `<p></p>`), so a
 * plain `.trim()` isn't enough to tell whether a clause was filled in.
 * An inline image counts as content. */
export function isRichTextBlank(html: string): boolean {
  if (/<img\b/i.test(html)) return false
  return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim() === ''
}
