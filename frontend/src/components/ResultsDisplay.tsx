import { useState } from "react";
import { QueryResult } from "@/pages/Index";
import { CheckCircle, XCircle, AlertTriangle, MessageSquare } from "lucide-react";
import { DataTable } from "@/components/DataTable";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ResultsDisplayProps {
  result: QueryResult;
  onFeedback: (feedback: string) => Promise<void>;
}

export const ResultsDisplay = ({ result, onFeedback }: ResultsDisplayProps) => {
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
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

  const handleFeedbackSubmit = async () => {
    if (!feedback.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onFeedback(feedback);
      setFeedback("");
      setShowFeedback(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      // You could add a toast notification here
    } finally {
      setIsSubmitting(false);
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
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-foreground">Generated SQL</h3>
          {result.feedback_applied && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
              ✅ Feedback Applied
            </span>
          )}
        </div>
        <div className="bg-background rounded border border-border p-3 font-mono text-sm text-foreground overflow-x-auto">
          <code>{result.sql}</code>
        </div>
      </div>

      {/* Feedback Section - Only show for verified queries with request_id */}
      {result.status === "verified" && result.request_id && (
        <div className="bg-surface rounded-lg border border-border p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Improve Results
            </h3>
            {!showFeedback && (
              <Button
                onClick={() => setShowFeedback(true)}
                variant="outline"
                size="sm"
              >
                Provide Feedback
              </Button>
            )}
          </div>
          
          {showFeedback && (
            <div className="space-y-3">
              <p className="text-sm text-muted">
                Not quite what you were looking for? Provide additional context or clarification to regenerate the query.
              </p>
              <Textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Example: 'I want to see only customers from the last 30 days' or 'Include the customer names in the results'"
                className="min-h-[80px]"
                disabled={isSubmitting}
              />
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleFeedbackSubmit}
                  disabled={!feedback.trim() || isSubmitting}
                  size="sm"
                >
                  {isSubmitting ? "Regenerating..." : "Regenerate Query"}
                </Button>
                <Button
                  onClick={() => {
                    setShowFeedback(false);
                    setFeedback("");
                  }}
                  variant="outline"
                  size="sm"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Data Preview */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-foreground mb-3">Data Preview</h3>
        <DataTable data={result.data} />
      </div>
    </div>
  );
};