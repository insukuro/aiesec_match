import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { errorMessage } from "../../shared/lib/errors";
import { Button } from "../../shared/ui/Button";
import { PasswordField } from "../../shared/ui/PasswordField";
import { TextField } from "../../shared/ui/TextField";
import { useToast } from "../../shared/ui/Toast";

export function AccountSecurityForm({
  email,
  emailVerified,
  refreshMe,
}: {
  email: string;
  emailVerified: boolean;
  refreshMe: () => Promise<void>;
}) {
  const toast = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [nextEmail, setNextEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);
  const [emailCode, setEmailCode] = useState("");
  const [devCode, setDevCode] = useState<string | null>(null);

  const changePassword = useMutation({
    mutationFn: () => api.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.show("Пароль изменён", "success");
    },
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  const requestEmailChange = useMutation({
    mutationFn: () => api.changeEmail(nextEmail.trim(), emailPassword),
    onSuccess: (result) => {
      setPendingEmail(nextEmail.trim());
      setEmailPassword("");
      setEmailCode(result.dev_code ?? "");
      setDevCode(result.dev_code ?? null);
      toast.show("Запрос на смену email создан", "success");
    },
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  const verifyEmail = useMutation({
    mutationFn: async () => {
      if (!pendingEmail) return;
      await api.verifyEmail(pendingEmail, emailCode.trim());
      await refreshMe();
    },
    onSuccess: () => {
      setPendingEmail(null);
      setEmailCode("");
      setDevCode(null);
      setNextEmail("");
      toast.show("Email изменён", "success");
    },
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  const submitPassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.show("Новые пароли не совпадают", "error");
      return;
    }
    changePassword.mutate();
  };

  const submitEmail = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    requestEmailChange.mutate();
  };

  return (
    <div className="stack">
      <div className="ui-card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted">Email</span>
          <strong>{email}</strong>
        </div>
        <p className="muted">
          Статус: {emailVerified ? "подтверждён" : "не подтверждён"}
        </p>
        <form className="stack" onSubmit={submitEmail}>
          <label className="field">
            <span className="field__label">Новый email</span>
            <TextField
              type="email"
              value={nextEmail}
              onChange={setNextEmail}
              autoComplete="email"
              required
            />
          </label>
          <label className="field">
            <span className="field__label">Текущий пароль</span>
            <PasswordField
              value={emailPassword}
              onChange={setEmailPassword}
              autoComplete="current-password"
            />
          </label>
          <Button type="submit" disabled={requestEmailChange.isPending}>
            {requestEmailChange.isPending ? "Отправляем…" : "Изменить email"}
          </Button>
        </form>

        {pendingEmail && (
          <form className="stack section" onSubmit={(event) => {
            event.preventDefault();
            verifyEmail.mutate();
          }}>
            <p>
              Подтвердите адрес <strong>{pendingEmail}</strong>.
            </p>
            {devCode && (
              <p className="muted" role="status">
                Код для локального режима: <strong>{devCode}</strong>
              </p>
            )}
            <label className="field">
              <span className="field__label">Код подтверждения</span>
              <TextField
                value={emailCode}
                onChange={setEmailCode}
                autoComplete="one-time-code"
                required
              />
            </label>
            <Button type="submit" disabled={verifyEmail.isPending}>
              Подтвердить email
            </Button>
          </form>
        )}
      </div>

      <form className="ui-card stack" onSubmit={submitPassword}>
        <h3>Смена пароля</h3>
        <label className="field">
          <span className="field__label">Текущий пароль</span>
          <PasswordField value={currentPassword} onChange={setCurrentPassword} />
        </label>
        <label className="field">
          <span className="field__label">Новый пароль</span>
          <PasswordField
            value={newPassword}
            onChange={setNewPassword}
            autoComplete="new-password"
            minLength={8}
            showStrength
          />
        </label>
        <label className="field">
          <span className="field__label">Повторите новый пароль</span>
          <PasswordField
            value={confirmPassword}
            onChange={setConfirmPassword}
            autoComplete="new-password"
            minLength={8}
          />
        </label>
        <Button type="submit" disabled={changePassword.isPending}>
          {changePassword.isPending ? "Сохраняем…" : "Сменить пароль"}
        </Button>
      </form>
    </div>
  );
}
