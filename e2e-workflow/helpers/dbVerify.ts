import { execFileSync } from 'node:child_process'
import path from 'node:path'

const BACKEND_DIR = path.join(__dirname, '..', '..', 'backend')
const PYTHON = process.env.E2E_PYTHON ?? 'python'

export type Entity = 'client' | 'project' | 'quotation' | 'contract' | 'agreement'

/** Reads a row straight out of the DB via backend/scripts/e2e_verify.py --
 * this is deliberately not the same code path as the API that wrote it,
 * so a passing comparison means the data really made it to the table,
 * not just that two layers of the same service agree with each other. */
export function dumpFromDb(entity: Entity, identifier: string): Record<string, unknown> {
  const output = execFileSync(PYTHON, ['-m', 'scripts.e2e_verify', 'dump', entity, identifier], {
    cwd: BACKEND_DIR,
    encoding: 'utf-8',
  })
  return JSON.parse(output)
}
