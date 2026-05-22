# Orbit Notes

Orbit Notes is a synthetic note-routing service used by the SkillDiff docs-forge pilot.

## Overview

The service accepts short notes, classifies the note topic, and returns a deterministic routing decision for a downstream worker queue.

## Architecture

- `src/index.ts` exposes the public `routeNote` function.
- `src/config.ts` stores static routing labels and retry limits.
- The package intentionally has no network dependency in this fixture.
