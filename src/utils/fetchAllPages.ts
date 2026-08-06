import type { PagedResponse } from '@/types/Pagination'

// Matches the backend's MAX_PAGE_SIZE (app/core/pagination.py) -- the
// largest page the server will hand back in a single request.
const MAX_PAGE_SIZE = 200

/**
 * Fetches every page of a paginated backend endpoint and concatenates the
 * results into a single flat array.
 *
 * This exists so callers that need "the whole list" (e.g. cross-reference
 * lookups like resolving a client's name from a project) can keep doing a
 * single `getX()` call and get back a plain array, while every individual
 * HTTP request underneath is still bounded (LIMIT/OFFSET-backed) rather
 * than the backend running one unbounded `SELECT *`. Pages are fetched
 * concurrently after the first one, since we know the total page count
 * up front.
 */
export async function fetchAllPages<T>(
  fetchPage: (page: number, pageSize: number) => Promise<PagedResponse<T>>,
  pageSize: number = MAX_PAGE_SIZE,
): Promise<T[]> {
  const first = await fetchPage(1, pageSize)
  if (first.totalPages <= 1) {
    return first.items
  }

  const remainingPages = await Promise.all(
    Array.from({ length: first.totalPages - 1 }, (_, index) => fetchPage(index + 2, pageSize)),
  )

  return [...first.items, ...remainingPages.flatMap((page) => page.items)]
}
