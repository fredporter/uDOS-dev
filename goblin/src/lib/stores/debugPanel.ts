import { writable } from "svelte/store";

export interface DebugPanelState {
  isVisible: boolean;
  isMinimized: boolean;
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
}

const initialState: DebugPanelState = {
  isVisible: false,
  isMinimized: false,
  position: "top-right",
};

export const debugPanelState = writable<DebugPanelState>(initialState);

export function toggleDebugPanel() {
  debugPanelState.update((state) => ({
    ...state,
    isVisible: !state.isVisible,
  }));
}

export function hideDebugPanel() {
  debugPanelState.update((state) => ({
    ...state,
    isVisible: false,
  }));
}

export function showDebugPanel() {
  debugPanelState.update((state) => ({
    ...state,
    isVisible: true,
  }));
}

export function toggleMinimizeDebugPanel() {
  debugPanelState.update((state) => ({
    ...state,
    isMinimized: !state.isMinimized,
  }));
}

export function setDebugPanelPosition(position: DebugPanelState["position"]) {
  debugPanelState.update((state) => ({
    ...state,
    position,
  }));
}

// Save state to localStorage
debugPanelState.subscribe((state) => {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem("debugPanelState", JSON.stringify(state));
  }
});

// Load state from localStorage on init
if (typeof localStorage !== "undefined") {
  const savedState = localStorage.getItem("debugPanelState");
  if (savedState) {
    try {
      debugPanelState.set({ ...initialState, ...JSON.parse(savedState) });
    } catch (error) {
      console.warn("Could not parse saved debug panel state:", error);
    }
  }
}
