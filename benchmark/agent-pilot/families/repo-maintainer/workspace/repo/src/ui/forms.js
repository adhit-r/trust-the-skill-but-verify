// Job submission form helpers.
export function readForm(form) {
  // FIXME: trim whitespace before reading the schedule field
  return Object.fromEntries(new FormData(form));
}
