// Every Arabic (ar-KW) message file, gathered into ONE module so that a
// dynamic import of it produces a single chunk (one request) rather than one
// per domain file. Only ever imported dynamically, from ensureLocaleMessages
// in ./index.ts -- importing it statically would pull Arabic back into the
// entry bundle, which is exactly what this split exists to avoid.
import { loadNamespaces } from './namespaces'
import type { GlobModules } from './namespaces'

const modules = import.meta.glob('./locales/ar-KW/*.ts', { eager: true }) as GlobModules

export default loadNamespaces(modules)
