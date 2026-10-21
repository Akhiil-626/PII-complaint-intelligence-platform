import type { EntityRedacted } from "./api"

export interface TextSegment {
  text: string
  entityType?: string
}

/**
 * Builds alternating plain and highlighted text segments from input text and detected entities.
 *
 * Guarantees:
 * - Entities sorted by start ascending (ties: higher score first).
 * - Entities skipped if start/end invalid, slice doesn't match entity text, or overlaps a kept segment.
 * - Concatenating segments.map(s => s.text).join("") reproduces text exactly.
 */
export function buildSegments(
  text: string,
  entities?: EntityRedacted[]
): TextSegment[] {
  if (!text) {
    return []
  }

  if (!entities || entities.length === 0) {
    return [{ text }]
  }

  // Filter candidates for valid boundaries and text match
  const validCandidates: EntityRedacted[] = []
  for (const ent of entities) {
    if (
      ent.start == null ||
      ent.end == null ||
      typeof ent.start !== "number" ||
      typeof ent.end !== "number" ||
      isNaN(ent.start) ||
      isNaN(ent.end) ||
      ent.start < 0 ||
      ent.end > text.length ||
      ent.start >= ent.end
    ) {
      continue
    }

    if (ent.text != null && text.slice(ent.start, ent.end) !== ent.text) {
      continue
    }

    validCandidates.push(ent)
  }

  // Sort by start (ties: higher score first)
  validCandidates.sort((a, b) => {
    if (a.start! !== b.start!) {
      return a.start! - b.start!
    }
    const scoreA = a.score ?? 0
    const scoreB = b.score ?? 0
    return scoreB - scoreA
  })

  // Skip any entity that overlaps a segment already kept
  const keptEntities: EntityRedacted[] = []
  let coverageEnd = 0
  for (const ent of validCandidates) {
    if (ent.start! < coverageEnd) {
      continue
    }
    keptEntities.push(ent)
    coverageEnd = ent.end!
  }

  // Build segments in order
  const segments: TextSegment[] = []
  let cursor = 0

  for (const ent of keptEntities) {
    if (ent.start! > cursor) {
      segments.push({ text: text.slice(cursor, ent.start!) })
    }
    segments.push({
      text: text.slice(ent.start!, ent.end!),
      entityType: ent.entity_type,
    })
    cursor = ent.end!
  }

  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor) })
  }

  return segments
}
