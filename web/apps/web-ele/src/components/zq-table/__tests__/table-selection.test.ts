import { describe, expect, it } from 'vitest';

import { getRowSelectionAction, getSelectionRange } from '../table-selection';

describe('table selection helpers', () => {
  describe('getRowSelectionAction', () => {
    it('replaces the selection for a normal click', () => {
      expect(getRowSelectionAction({}, false)).toBe('replace');
      expect(getRowSelectionAction({}, true)).toBe('replace');
    });

    it('toggles the current row for Ctrl or Cmd clicks', () => {
      expect(getRowSelectionAction({ ctrlKey: true }, true)).toBe('toggle');
      expect(getRowSelectionAction({ metaKey: true }, true)).toBe('toggle');
    });

    it('selects a range for Shift when an anchor exists', () => {
      expect(getRowSelectionAction({ shiftKey: true }, true)).toBe('range');
      expect(getRowSelectionAction({ shiftKey: true }, false)).toBe('replace');
    });

    it('gives Shift priority over Ctrl when extending a range', () => {
      expect(
        getRowSelectionAction({ ctrlKey: true, shiftKey: true }, true),
      ).toBe('range');
    });
  });

  describe('getSelectionRange', () => {
    it('returns an inclusive forward range', () => {
      expect(getSelectionRange(1, 4, 6)).toEqual([1, 2, 3, 4]);
    });

    it('returns an inclusive reverse range', () => {
      expect(getSelectionRange(4, 1, 6)).toEqual([1, 2, 3, 4]);
    });

    it('falls back to the current row for an invalid anchor', () => {
      expect(getSelectionRange(-1, 3, 6)).toEqual([3]);
      expect(getSelectionRange(8, 3, 6)).toEqual([3]);
    });

    it('returns no rows for an invalid current index', () => {
      expect(getSelectionRange(1, -1, 6)).toEqual([]);
      expect(getSelectionRange(1, 6, 6)).toEqual([]);
    });
  });
});
