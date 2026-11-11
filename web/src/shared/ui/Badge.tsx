import type { PropsWithChildren } from "react";

type Tone = "neutral" | "blue" | "success" | "warning" | "danger" | "programme";

export function Badge({ tone = "neutral", children, style }: PropsWithChildren<{ tone?: Tone; style?: React.CSSProperties }>) {
  return <span data-tone={tone} className="ui-badge" style={style}>{children}</span>;
}