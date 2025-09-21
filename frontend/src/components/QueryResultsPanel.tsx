import { useState } from "react";
import { QueryInput } from "@/components/QueryInput";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { DatasetInfo, QueryResult } from "@/pages/Index";

interface QueryResultsPanelProps {
  dataset: DatasetInfo | null;
  queryResult: QueryResult | null;
  onQuery: (question: string) => Promise<void>;
  onFeedback: (feedback: string) => Promise<void>;
}

export const QueryResultsPanel = ({ dataset, queryResult, onQuery, onFeedback }: QueryResultsPanelProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleQuery = async (question: string) => {
    setIsLoading(true);
    try {
      await onQuery(question);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full bg-background flex flex-col">
      <div className="p-6 border-b border-border">
        <QueryInput 
          onQuery={handleQuery}
          disabled={!dataset}
          isLoading={isLoading}
        />
      </div>
      
      <div className="flex-1 overflow-auto">
        {queryResult && (
          <div className="p-6">
            <ResultsDisplay result={queryResult} onFeedback={onFeedback} />
          </div>
        )}
        
        {!dataset && (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted text-center">
              Upload a CSV file to start querying your data
            </p>
          </div>
        )}
        
        {dataset && !queryResult && !isLoading && (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted text-center">
              Ask a question about your data to see results
            </p>
          </div>
        )}
      </div>
    </div>
  );
};