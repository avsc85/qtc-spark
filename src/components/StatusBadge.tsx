interface StatusBadgeProps {
  status: string;
}

const StatusBadge = ({ status }: StatusBadgeProps) => {
  const className = `status-badge status-${status}`;
  const dotColor: Record<string, string> = {
    lead: "bg-primary",
    proposal: "bg-accent",
    active: "bg-success",
    done: "bg-muted-foreground",
    draft: "bg-muted-foreground",
    sent: "bg-primary",
    signed: "bg-success",
    paid: "bg-success",
  };

  return (
    <span className={className}>
      <span className={`glow-dot ${dotColor[status] || "bg-muted-foreground"}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

export default StatusBadge;
