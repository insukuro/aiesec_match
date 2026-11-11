import { useState } from "react";
import { Dialog } from "../../shared/ui/Dialog";
import { Button } from "../../shared/ui/Button";

export interface DeleteAccountDialogProps {
  open: boolean;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DeleteAccountDialog({ open, busy, onCancel, onConfirm }: DeleteAccountDialogProps) {
  const [confirmWord, setConfirmWord] = useState("");
  return (
    <Dialog open={open} title="Удалить аккаунт?" onClose={onCancel}>
      <p>Все данные будут удалены безвозвратно. Введите слово «Удалить» для подтверждения.</p>
      <input
        className="ui-input"
        value={confirmWord}
        onChange={(e) => setConfirmWord(e.target.value)}
        placeholder="Удалить"
      />
      <div className="row" style={{ justifyContent: "flex-end", marginTop: "var(--space-3)" }}>
        <Button variant="outline" onClick={onCancel}>Отмена</Button>
        <Button variant="danger" disabled={confirmWord !== "Удалить" || busy} onClick={onConfirm}>Удалить</Button>
      </div>
    </Dialog>
  );
}