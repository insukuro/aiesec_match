import { formatMoney } from "../../shared/lib/format";

export function CostLabel({ cost }: { cost: { amount: number; currency: string } | null }) {
  if (!cost) return null;
  return <span>Взнос {formatMoney(cost.amount, cost.currency)}</span>;
}