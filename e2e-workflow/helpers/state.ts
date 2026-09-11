// Each spec file in this stream runs in its own Playwright worker
// process, so they can't share in-memory state directly. This is the
// one small file all of them read/write to hand IDs forward -- client
// ID from 01 to 02, project number from 02 to 03/04, and so on -- and
// it's also exactly what global-teardown.ts reads to know what to
// delete at the end, regardless of which specs passed or failed.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'

const STATE_DIR = path.join(__dirname, '..', '.artifacts')
export const STATE_PATH = path.join(STATE_DIR, 'state.json')

export interface WorkflowState {
  runTag: string
  createdAt: string
  clientId?: string
  clientCode?: string
  projectNo?: string
  quotationNo?: string
  agreementId?: string
  contractNo?: string
  paymentIds?: string[]
  refundIds?: string[]
  adjustmentIds?: string[]
  [key: string]: unknown
}

export function readState(): WorkflowState {
  if (!existsSync(STATE_PATH)) {
    throw new Error(
      `No run state at ${STATE_PATH} -- run the workflow suite from 01-client-creation.spec.ts onward ` +
        `(global-setup.ts creates this file; it should not be missing mid-run).`,
    )
  }
  return JSON.parse(readFileSync(STATE_PATH, 'utf-8')) as WorkflowState
}

export function writeState(patch: Partial<WorkflowState>): WorkflowState {
  mkdirSync(STATE_DIR, { recursive: true })
  const current = existsSync(STATE_PATH) ? readState() : ({} as WorkflowState)
  const next = { ...current, ...patch }
  writeFileSync(STATE_PATH, JSON.stringify(next, null, 2))
  return next
}

export function appendToArray(key: 'paymentIds' | 'refundIds' | 'adjustmentIds', value: string): void {
  const current = readState()
  const arr = (current[key] as string[] | undefined) ?? []
  arr.push(value)
  writeState({ [key]: arr } as Partial<WorkflowState>)
}
