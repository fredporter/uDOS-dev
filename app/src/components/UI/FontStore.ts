// Global font and size store
import { writable } from "svelte/store";

export type FontFamily = "OldStyle" | "SansRounded" | "Humanist";

export const fontFamilies: FontFamily[] = [
  "OldStyle",
  "SansRounded",
  "Humanist",
];

export const fontFamily = writable<FontFamily>("OldStyle");
export const fontSize = writable<number>(1); // 1 = 100%, 0.9 = 90%, etc.
