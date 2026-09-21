export type LocaleMessages = Record<string, unknown>
export type GlobModules = Record<string, { default: LocaleMessages }>

// Each domain (common, navigation, dashboard, client, ...) lives in its own
// file under locales/<locale>/, named after its top-level message namespace
// (e.g. locales/en/client.ts -> messages.en.client). Loaded via import.meta.glob
// instead of a hand-maintained barrel file so adding a new domain file is
// enough on its own -- no index to keep in sync, and no merge conflicts
// between domains being translated at the same time.
export function loadNamespaces(modules: GlobModules): LocaleMessages {
  const messages: LocaleMessages = {}
  for (const path in modules) {
    const namespace = path.split('/').pop()?.replace(/\.ts$/, '')
    if (!namespace) continue
    messages[namespace] = modules[path].default
  }
  return messages
}
