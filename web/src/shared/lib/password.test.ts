import { describe, it, expect } from "vitest";
import { checkPassword, passwordStrengthLabel } from "./password";

describe("checkPassword", () => {
  it("слишком короткий", () => {
    expect(checkPassword("abc1").ok).toBe(false);
    expect(checkPassword("abc1").errors).toContain("Минимум 8 символов");
  });
  it("без цифры", () => {
    expect(checkPassword("abcdefgh").errors).toContain("Хотя бы одна цифра");
  });
  it("без буквы", () => {
    expect(checkPassword("12345678").errors).toContain("Хотя бы одна буква");
  });
  it("не должен содержать email целиком", () => {
    const r = checkPassword("user@example.com1", "user@example.com");
    expect(r.errors.some((e) => e.includes("email"))).toBe(true);
  });
  it("валидный — ok, score ≥ 1", () => {
    const r = checkPassword("password1");
    expect(r.ok).toBe(true);
    expect(r.score).toBeGreaterThanOrEqual(1);
  });
  it("надёжный — score 3", () => {
    expect(checkPassword("Password1!").score).toBe(3);
  });
});

describe("passwordStrengthLabel", () => {
  it.each([[3, "Надёжный"], [2, "Средний"], [1, "Слабый"], [0, ""]])("%i → %s", (s, label) => {
    expect(passwordStrengthLabel(s)).toBe(label);
  });
});