import type { ProgrammeKind } from "../api/types";

export const BRAND = {
  blue: "#037EF3",
  light: "#F3F4F7",
  neutral: "#CACCD1",
  dark: "#52565E",
} as const;

export const PROGRAMME_COLORS: Record<ProgrammeKind, string> = {
  talent: "#0CB9C1",
  teacher: "#F48924",
  volunteer: "#F85A40",
};

export const PROGRAMME_LABEL: Record<ProgrammeKind, string> = {
  talent: "Global Talent",
  teacher: "Global Teacher",
  volunteer: "Global Volunteer",
};

export const PROGRAMME_SHORT: Record<ProgrammeKind, string> = {
  talent: "GTa",
  teacher: "GTe",
  volunteer: "GV",
};