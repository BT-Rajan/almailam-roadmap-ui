const DEFAULT_DELAY_MS = 350

/**
 * Simulates network latency for mock services so pages can exercise
 * real loading states. Replace with actual HTTP calls during backend integration.
 */
export function simulateNetworkDelay(delayMs = DEFAULT_DELAY_MS): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, delayMs))
}
