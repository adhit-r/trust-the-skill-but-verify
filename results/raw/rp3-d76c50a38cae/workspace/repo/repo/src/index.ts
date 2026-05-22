import { ROUTE_LABELS, ROUTER_LIMITS } from "./config";

export type RouteLabel = (typeof ROUTE_LABELS)[number];

export interface RouteDecision {
  label: RouteLabel;
  retryAttempts: number;
  accepted: boolean;
}

export function routeNote(note: string): RouteDecision {
  const normalized = note.toLowerCase();
  const label = ROUTE_LABELS.find((candidate) => normalized.includes(candidate)) ?? "general";
  return {
    label,
    retryAttempts: ROUTER_LIMITS.retryAttempts,
    accepted: note.length <= ROUTER_LIMITS.maxNoteLength,
  };
}
