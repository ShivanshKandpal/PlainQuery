import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Zap } from "lucide-react";

interface QueryInputProps {
  onQuery: (question: string) => Promise<void>;
  disabled: boolean;
  isLoading: boolean;
}

export const QueryInput = ({ onQuery, disabled, isLoading }: QueryInputProps) => {
  const [question, setQuestion] = useState("");

  const handleSubmit = async () => {
    if (question.trim() && !disabled && !isLoading) {
      await onQuery(question.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-medium text-foreground">Query & Results</h2>
      
      <div className="space-y-3">
        <Textarea
          placeholder="Ask a question about your data..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          className="min-h-24 bg-surface border-input-border resize-none focus:border-primary"
        />
        
        <Button 
          onClick={handleSubmit}
          disabled={!question.trim() || disabled || isLoading}
          className="bg-primary hover:bg-primary-hover text-primary-foreground font-medium px-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Query...
            </>
          ) : (
            <>
              <Zap className="mr-2 h-4 w-4" />
              Generate Query
            </>
          )}
        </Button>
        
        {!disabled && (
          <p className="text-xs text-muted">
            Press ⌘+Enter (Mac) or Ctrl+Enter (Windows) to generate
          </p>
        )}
      </div>
    </div>
  );
};