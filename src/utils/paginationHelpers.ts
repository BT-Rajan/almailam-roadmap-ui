/**
 * Shared pagination logic -- the one place that decides how many items
 * live on a page and how many page-number buttons show at once, so
 * every list in the app (client-side via usePagination.ts/SmartTable,
 * or server-side via a store's own page/pageSize state, e.g.
 * clientStore/projectStore/documentStore/auditLogStore feeding
 * TablePagination.vue directly) agrees on the same defaults and the
 * same "set" behaviour instead of each screen inventing its own.
 *
 * Deliberately framework-agnostic (no Vue import) -- a plain function
 * of (currentPage, totalPages, setSize) in, a PageSet out, so it works
 * equally from a composable, a component's props, or a plain store.
 */

// Items per page, when a caller doesn't ask for a specific size.
export const DEFAULT_PAGE_SIZE = 5

// How many page-number buttons are shown at once before the pager
// steps to the next "set" (1-5, then 6-10, etc.) rather than growing
// unbounded as totalPages grows.
export const DEFAULT_PAGE_SET_SIZE = 5

export interface PageSet {
  // The page numbers to render as buttons for the current set, e.g.
  // [6, 7, 8, 9, 10] -- always contiguous, always <= setSize long.
  pages: number[]
  hasPreviousSet: boolean
  hasNextSet: boolean
  // The page to land on when the caller steps a whole set backward/
  // forward (always the first page of the neighbouring set) -- equal
  // to the current page's own set boundary when there's nowhere
  // further to go, so a caller can wire a "jump a set" button straight
  // to goToPage(previousSetPage/nextSetPage) without its own bounds
  // checking.
  previousSetPage: number
  nextSetPage: number
}

/**
 * Groups 1..totalPages into fixed-size sets and returns the set that
 * currentPage falls in, plus how to step to the neighbouring set.
 * currentPage/totalPages are clamped defensively (e.g. a store whose
 * data hasn't loaded yet reporting totalPages: 0) so callers never have
 * to guard before calling this.
 */
export function getPageSet(currentPage: number, totalPages: number, setSize: number = DEFAULT_PAGE_SET_SIZE): PageSet {
  const safeTotalPages = Math.max(1, Math.floor(totalPages) || 1)
  const safeCurrentPage = Math.min(Math.max(Math.floor(currentPage) || 1, 1), safeTotalPages)

  const setIndex = Math.floor((safeCurrentPage - 1) / setSize)
  const start = setIndex * setSize + 1
  const end = Math.min(start + setSize - 1, safeTotalPages)

  const pages: number[] = []
  for (let page = start; page <= end; page += 1) pages.push(page)

  return {
    pages,
    hasPreviousSet: start > 1,
    hasNextSet: end < safeTotalPages,
    previousSetPage: Math.max(1, start - setSize),
    nextSetPage: start + setSize <= safeTotalPages ? start + setSize : start,
  }
}
