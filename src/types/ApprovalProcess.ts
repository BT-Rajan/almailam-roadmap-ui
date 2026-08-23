// One of the 5 Project Approval Process stage gates. Two independent
// ways to close it: uploading its review document (hasDocument), or
// confirming completion once its tagged documents (Documents tab,
// ProjectDocument.stageKey) are reviewed (completedAt/completedByName).
// Use isComplete, not hasDocument, to check whether the stage is done.
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
  isComplete: boolean
  completedAt: string | null
  completedByName: string | null
}
