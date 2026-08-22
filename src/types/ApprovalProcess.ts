// One of the 5 Project Approval Process stage gates -- complete the
// moment its review document is uploaded (hasDocument), not via a
// separate manual action.
export interface ProjectApprovalStep {
  id: string
  name: string
  stageKey: string
  sequenceNumber: number
  hasDocument: boolean
  originalFilename: string | null
  fileSizeBytes: number | null
  uploadedAt: string | null
  uploadedByName: string | null
}
