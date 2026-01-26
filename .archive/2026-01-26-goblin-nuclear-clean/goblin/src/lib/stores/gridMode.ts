/**
 * Grid Mode Store
 * Manages grid display configuration
 */

import { writable } from "svelte/store";

export type GridSubmode = "teledesk" | "terminal" | "demo";

export interface GridModeState {
  mode: GridSubmode;
  viewportBorder: boolean;
  fixedCols: number;
  fixedRows: number;
  cellSize: number;
  mono: string;
}

export interface ViewportDims {
  cols: number;
  rows: number;
}

const initialState: GridModeState = {
  mode: "teledesk",
  viewportBorder: false,
  fixedCols: 40,
  fixedRows: 15,
  cellSize: 24,
  mono: "teletext",
};

function createGridModeStore() {
  const { subscribe, set, update } = writable<GridModeState>(initialState);

  return {
    subscribe,
    setMode: (mode: GridSubmode) => {
      update((state) => ({ ...state, mode }));
    },
    toggleBorder: () => {
      update((state) => ({ ...state, viewportBorder: !state.viewportBorder }));
    },
    setCellSize: (cellSize: number) => {
      update((state) => ({ ...state, cellSize }));
    },
    setDimensions: (cols: number, rows: number) => {
      update((state) => ({ ...state, fixedCols: cols, fixedRows: rows }));
    },
    setMono: (mono: string) => {
      update((state) => ({ ...state, mono }));
    },
    reset: () => set(initialState),
  };
}

export const gridMode = createGridModeStore();

// Viewport dimensions store
export const viewportDims = writable<ViewportDims>({
  cols: 80,
  rows: 30,
});
