export const retry_limit = 4;

// TODO: add jitter to the backoff
export function backoff(attempt: number): number {
  return Math.min(1000 * 2 ** attempt, 30000);
}
