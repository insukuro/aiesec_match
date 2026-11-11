export interface AvatarProps {
  name: string;
  size?: number;
}

export function Avatar({ name, size = 40 }: AvatarProps) {
  const initial = name.trim().charAt(0).toUpperCase() || "?";
  return (
    <span className="ui-avatar" style={{ width: size, height: size, fontSize: size * 0.45 }} aria-hidden>
      {initial}
    </span>
  );
}