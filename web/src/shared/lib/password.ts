export interface PasswordCheck {
  ok: boolean;
  score: number; // 0..3
  errors: string[];
}

export function checkPassword(pwd: string, email?: string): PasswordCheck {
  const errors: string[] = [];
  if (pwd.length < 8) errors.push("Минимум 8 символов");
  if (pwd.length > 128) errors.push("Не более 128 символов");
  if (!/[A-Za-z]/.test(pwd)) errors.push("Хотя бы одна буква");
  if (!/\d/.test(pwd)) errors.push("Хотя бы одна цифра");
  if (email && pwd.toLowerCase().includes(email.toLowerCase())) {
    errors.push("Пароль не должен содержать email");
  }
  let score = 0;
  if (pwd.length >= 8) score++;
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++;
  if (/\d/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) score++;
  return { ok: errors.length === 0, score, errors };
}

export function passwordStrengthLabel(score: number): string {
  if (score >= 3) return "Надёжный";
  if (score === 2) return "Средний";
  if (score === 1) return "Слабый";
  return "";
}