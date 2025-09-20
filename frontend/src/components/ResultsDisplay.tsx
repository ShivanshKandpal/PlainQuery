import { QueryResult } from "@/pages/Index";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { DataTable } from "@/components/DataTable";

interface ResultsDisplayProps {
  result: QueryResult;
}

export const ResultsDisplay = ({ result }: ResultsDisplayProps) => {
  const getStatusBadge = () => {
    switch (result.status) {
      case "verified":
        return (
          <div className="badge-success flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Verified ✅
          </div>
        );
      case "error":
        return (
          <div className="badge-error flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            Error ❌
          </div>
        );
      case "rejected":
        return (
          <div className="badge-warning flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Rejected 🚫
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Explanation */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-foreground">Query Result</h3>
          <div className="flex items-center gap-3">
            {getStatusBadge()}
            <span className="text-xs text-muted">
              {result.latency}s
            </span>
            {result.cost && (
              <span className="text-xs text-muted">
                ${result.cost.toFixed(6)}
              </span>
            )}
            {result.total_cost && (
              <span className="text-xs text-muted">
                (Total: ${result.total_cost.toFixed(6)})
              </span>
            )}
          </div>
        </div>
        <p className="text-sm text-muted">
          {result.explanation}
        </p>
      </div>

      {/* Generated SQL */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-foreground mb-3">Generated SQL</h3>
        <div className="bg-background rounded border border-border p-3 font-mono text-sm text-foreground overflow-x-auto">
          <code>{result.sql}</code>
        </div>
      </div>

      {/* Data Preview */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-foreground mb-3">Data Preview</h3>
        <DataTable data={result.data} />
      </div>
    </div>
  );
};