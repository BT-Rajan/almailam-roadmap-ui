import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GovernmentSubmission } from '@/types/Submission'
import { openExternalLink } from '@/utils/fileDownload'
import { buildSubmissionFiles } from '@/utils/submissionFiles'

const labels = { acknowledgement: 'Ack', followup: 'Follow-up', response: 'Response' }

function submissionWith(documents: GovernmentSubmission['documents']): GovernmentSubmission {
  return { submissionNo: 'SUB-1', documents } as GovernmentSubmission
}

describe('buildSubmissionFiles with documents on file', () => {
  it('lists a link-backed required document and carries its link', () => {
    const files = buildSubmissionFiles(
      submissionWith([
        { id: 1, name: 'Ownership Proof', status: 'Uploaded', originalFilename: 'Title deed', externalLink: 'https://drive.example/x', source: 'link' },
        { id: 2, name: 'Site Plan', status: 'Pending' },
      ]),
      [],
      labels,
    )
    expect(files).toHaveLength(1)
    expect(files[0]).toMatchObject({ label: 'Ownership Proof', externalLink: 'https://drive.example/x' })
  })
})

describe('openExternalLink', () => {
  afterEach(() => vi.restoreAllMocks())

  it('opens http(s) links without an opener', () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    expect(openExternalLink('https://drive.example/x')).toBe(true)
    expect(open).toHaveBeenCalledWith('https://drive.example/x', '_blank', 'noopener,noreferrer')
  })

  it.each(['javascript:alert(1)', 'data:text/html,hi', '\\\\server\\share\\file.pdf', 'not a url'])('refuses %s', (link) => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null)
    expect(openExternalLink(link)).toBe(false)
    expect(open).not.toHaveBeenCalled()
  })
})
