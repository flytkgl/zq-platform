export type RowSelectionAction = 'range' | 'replace' | 'toggle';

export interface RowSelectionModifiers {
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
}

/**
 * Resolve the selection operation for a row click.
 *
 * Shift takes precedence when a valid anchor exists, matching the usual
 * desktop file-list behavior. If there is no anchor, Shift falls back to a
 * normal single-row selection.
 */
export function getRowSelectionAction(
  modifiers: RowSelectionModifiers,
  hasAnchor: boolean,
): RowSelectionAction {
  if (modifiers.shiftKey && hasAnchor) {
    return 'range';
  }

  if (modifiers.ctrlKey || modifiers.metaKey) {
    return 'toggle';
  }

  return 'replace';
}

/**
 * Return the inclusive indexes between an anchor and the clicked row.
 * Invalid indexes are handled by falling back to the clicked row only.
 */
export function getSelectionRange(
  anchorIndex: number,
  currentIndex: number,
  rowCount: number,
): number[] {
  if (
    currentIndex < 0 ||
    currentIndex >= rowCount ||
    rowCount <= 0 ||
    !Number.isInteger(currentIndex)
  ) {
    return [];
  }

  if (
    anchorIndex < 0 ||
    anchorIndex >= rowCount ||
    !Number.isInteger(anchorIndex)
  ) {
    return [currentIndex];
  }

  const start = Math.min(anchorIndex, currentIndex);
  const end = Math.max(anchorIndex, currentIndex);

  return Array.from({ length: end - start + 1 }, (_, offset) => start + offset);
}
