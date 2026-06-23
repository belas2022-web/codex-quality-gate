export default function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`severity ${severity}`}>{severity}</span>;
}
