interface SummarySectionProps {
  summary: string;
}

export const SummarySection = ({ summary }: SummarySectionProps) => {
  return (
    <div className="p-6 border-b border-border">
      <h3 className="text-sm font-medium text-foreground mb-3">Summary</h3>
      <p className="text-sm text-muted leading-relaxed">
        {summary}
      </p>
    </div>
  );
};