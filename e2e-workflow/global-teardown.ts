import { execFileSync } from 'node:child_process'
import { existsSync, rmSync } from 'node:fs'
import path from 'node:path'
import { readState, STATE_PATH } from './helpers/state'

const BACKEND_DIR = path.join(__dirname, '..', 'backend')
const PYTHON = process.env.E2E_PYTHON ?? 'python'

// Runs unconditionally after the suite -- whether every spec passed,
// one failed partway through, or the run was interrupted -- so a test
// project stuck at some intermediate workflow stage never lingers.
// Reads e2e_verify.py's own report of what it actually deleted and
// fails loudly (rather than silently swallowing it) if anything this
// run created was left behind, since that would otherwise be exactly
// the kind of drift into "existing record" territory the whole stream
// exists to avoid.
export default async function globalTeardown(): Promise<void> {
  if (!existsSync(STATE_PATH)) {
    console.warn('[e2e-workflow] no state file found at teardown -- nothing to clean up.')
    return
  }
  const state = readState()

  const output = execFileSync(PYTHON, ['-m', 'scripts.e2e_verify', 'cleanup', STATE_PATH], {
    cwd: BACKEND_DIR,
    encoding: 'utf-8',
  })
  const report: Record<string, boolean> = JSON.parse(output)
  console.log('[e2e-workflow] cleanup report:', report)

  const expectedButMissing = Object.entries(report)
    .filter(([, wasDeleted]) => wasDeleted === false)
    .map(([label]) => label)
    // A false entry only matters if this run actually claimed to have
    // created that thing -- e.g. "contract": false is fine for a run
    // that never got past the Payment Plan stage.
    .filter((label) => {
      const idKeys: Record<string, string> = {
        client: 'clientId',
        project: 'projectNo',
        quotation: 'quotationNo',
        contract: 'contractNo',
        agreement: 'agreementId',
      }
      const key = idKeys[label]
      return key ? Boolean(state[key]) : false
    })

  rmSync(STATE_PATH, { force: true })

  if (expectedButMissing.length > 0) {
    throw new Error(
      `[e2e-workflow] cleanup did not remove: ${expectedButMissing.join(', ')} ` +
        `(run tag ${state.runTag}) -- check the DB manually before re-running the suite.`,
    )
  }
}
