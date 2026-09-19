import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import type { GovernmentSubmission, SubmissionFollowup } from '@/types/Submission'
import { openBlobInWindow, triggerBlobDownload } from '@/utils/fileDownload'

// Every file uploaded against a permit application -- the required
// documents checklist, the acknowledgement uploaded when it was filed,
// documents attached to follow-ups, and the authority's response
// uploaded at Close -- flattened into one list, so the application's
// Overview and the project's Scope > Documents tab can show them all
// with view/download links, without each knowing how each kind is
// stored or fetched.

export type SubmissionFileSource =
  | { kind: 'required'; documentId: number }
  | { kind: 'acknowledgement' }
  | { kind: 'followup'; followupId: string }
  | { kind: 'response' }

export interface SubmissionFile {
  key: string
  submissionNo: string
  source: SubmissionFileSource
  // What the file is (the required document's name, "Application
  // acknowledgement", ...) -- not its filename.
  label: string
  filename: string
  sizeLabel?: string | null
  uploadDate?: string | null
  uploadedBy?: string | null
}

export interface SubmissionFileLabels {
  acknowledgement: string
  followup: string
  response: string
}

export function buildSubmissionFiles(
  submission: GovernmentSubmission,
  followups: SubmissionFollowup[],
  labels: SubmissionFileLabels,
): SubmissionFile[] {
  const files: SubmissionFile[] = []
  const { submissionNo } = submission

  for (const document of submission.documents) {
    if (!document.originalFilename) continue
    files.push({
      key: `${submissionNo}:required:${document.id}`,
      submissionNo,
      source: { kind: 'required', documentId: document.id },
      label: document.name,
      filename: document.originalFilename,
      sizeLabel: document.fileSizeLabel,
      uploadDate: document.uploadDate,
      uploadedBy: document.uploadedBy,
    })
  }

  if (submission.proofOfSubmission) {
    files.push({
      key: `${submissionNo}:acknowledgement`,
      submissionNo,
      source: { kind: 'acknowledgement' },
      label: labels.acknowledgement,
      filename: submission.proofOfSubmission.originalFilename,
      sizeLabel: submission.proofOfSubmission.fileSizeLabel,
      uploadDate: submission.proofOfSubmission.uploadDate,
      uploadedBy: submission.proofOfSubmission.uploadedBy,
    })
  }

  // Oldest first, so the list reads in the order things happened.
  const followupsWithFiles = followups.filter((followup) => followup.document)
  for (const followup of [...followupsWithFiles].reverse()) {
    if (!followup.document) continue
    files.push({
      key: `${submissionNo}:followup:${followup.id}`,
      submissionNo,
      source: { kind: 'followup', followupId: followup.id },
      label: labels.followup,
      filename: followup.document.originalFilename,
      sizeLabel: followup.document.fileSizeLabel,
      uploadDate: followup.document.uploadDate,
      uploadedBy: followup.document.uploadedBy,
    })
  }

  if (submission.proofOfResponse) {
    files.push({
      key: `${submissionNo}:response`,
      submissionNo,
      source: { kind: 'response' },
      label: labels.response,
      filename: submission.proofOfResponse.originalFilename,
      sizeLabel: submission.proofOfResponse.fileSizeLabel,
      uploadDate: submission.proofOfResponse.uploadDate,
      uploadedBy: submission.proofOfResponse.uploadedBy,
    })
  }

  return files
}

function fetchSubmissionFileBlob(file: SubmissionFile): Promise<Blob> {
  const { source, submissionNo } = file
  switch (source.kind) {
    case 'required':
      return governmentSubmissionService.downloadDocument(submissionNo, source.documentId)
    case 'acknowledgement':
      return governmentSubmissionService.downloadAcknowledgement(submissionNo)
    case 'followup':
      return governmentSubmissionService.downloadFollowupDocument(submissionNo, source.followupId)
    case 'response':
      return governmentSubmissionService.downloadPermitDocument(submissionNo)
  }
}

// Opens the file in a browser tab. The blank tab is opened synchronously,
// before the fetch -- see openBlobInWindow's docstring for why.
export async function viewSubmissionFile(file: SubmissionFile): Promise<void> {
  const viewWindow = window.open('', '_blank')
  try {
    openBlobInWindow(await fetchSubmissionFileBlob(file), viewWindow)
  } catch (error) {
    viewWindow?.close()
    throw error
  }
}

export async function downloadSubmissionFile(file: SubmissionFile): Promise<void> {
  triggerBlobDownload(await fetchSubmissionFileBlob(file), file.filename)
}
