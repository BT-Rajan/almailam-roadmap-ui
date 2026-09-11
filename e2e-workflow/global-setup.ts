import { existsSync } from 'node:fs'
import { STATE_PATH, writeState } from './helpers/state'

// One tag per run, e.g. "E2EVFY250911143022" -- short enough to fit in
// every field's max length (client mobile/email, project name, etc.)
// while staying unique across runs and immediately greppable in the DB
// or in staff-facing lists if a run's teardown ever fails to clean up.
// Deliberately NOT the word "test" alone -- that collides with real
// data far too easily; ALMAILAM's own conventions already use plain
// English words for real client/project names.
function buildRunTag(): string {
  const now = new Date()
  const stamp = now
    .toISOString()
    .replace(/[-:T.]/g, '')
    .slice(0, 14)
  return `E2EVFY${stamp}`
}

export default async function globalSetup(): Promise<void> {
  if (existsSync(STATE_PATH)) {
    // A previous run's state file surviving to here means its teardown
    // never ran (crashed suite, killed process, etc.) -- surface that
    // loudly rather than silently starting a fresh run on top of
    // possibly-still-live leftover test data. Clean up manually first:
    //   python -m scripts.e2e_verify cleanup ../e2e-workflow/.artifacts/state.json
    // then delete the state file and re-run.
    throw new Error(
      `${STATE_PATH} already exists from a previous run that didn't tear down cleanly.\n` +
        `Run the cleanup command it describes, delete the file, and re-run this suite.`,
    )
  }
  const runTag = buildRunTag()
  writeState({ runTag, createdAt: new Date().toISOString() })
  console.log(`[e2e-workflow] run tag: ${runTag}`)
}
