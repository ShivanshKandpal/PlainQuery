import { SchemaColumn } from "@/pages/Index";

interface SchemaSectionProps {
  schema: SchemaColumn[];
}

const getTypeBadgeClass = (type: SchemaColumn["type"]) => {
  switch (type) {
    case "string":
      return "badge-string";
    case "number":
      return "badge-number";
    case "date":
      return "badge-date";
    case "boolean":
      return "badge-boolean";
    default:
      return "badge-string";
  }
};

export const SchemaSection = ({ schema }: SchemaSectionProps) => {
  const shouldShowStats = (stats: string) => {
    const hideStatsMessages = [
      "stats unavailable", 
      "no stats available", 
      "stats unavailable",
      "(could not compute stats)",
      "could not compute stats"
    ];
    return !hideStatsMessages.some(message => 
      stats.toLowerCase().includes(message.toLowerCase())
    );
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="p-6">
        <h3 className="text-sm font-medium text-foreground mb-4">Schema</h3>
        
        <div className="space-y-3">
          {schema.map((column) => (
            <div key={column.name} className="p-3 bg-background rounded border border-border">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-sm text-foreground font-medium">
                  {column.name}
                </span>
                <span className={getTypeBadgeClass(column.type)}>
                  {column.type}
                </span>
              </div>
              {shouldShowStats(column.stats) && (
                <p className="text-xs text-muted">
                  {column.stats}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};