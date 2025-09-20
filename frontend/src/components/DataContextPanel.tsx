import { FileUploadZone } from "@/components/FileUploadZone";
import { SummarySection } from "@/components/SummarySection";
import { SchemaSection } from "@/components/SchemaSection";
import { DatasetInfo } from "@/pages/Index";
import { Button } from "@/components/ui/button";

interface DataContextPanelProps {
  dataset: DatasetInfo | null;
  onFileUpload: (file: File) => void;
  onUseExistingDB?: () => void;
}

export const DataContextPanel = ({ dataset, onFileUpload, onUseExistingDB }: DataContextPanelProps) => {
  const handleUseExistingDB = () => {
    if (onUseExistingDB) {
      onUseExistingDB();
    } else {
      alert("Using existing database.db - you can now query the existing data!");
    }
  };

  return (
    <div className="h-full bg-surface">
      <div className="p-6 border-b border-border">
        <h2 className="text-lg font-medium text-foreground mb-4">Data Context</h2>
        
        {/* File upload section */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-foreground mb-2">Upload New Data</h3>
          <FileUploadZone onFileUpload={onFileUpload} />
        </div>
        
        {/* Existing database option */}
        <div className="mb-4">
          <h3 className="text-sm font-medium text-foreground mb-2">Or Use Existing Database</h3>
          <Button 
            variant="outline" 
            onClick={handleUseExistingDB}
            className="w-full"
          >
            Use database.db (Sample Data)
          </Button>
        </div>
        
        {dataset && (
          <div className="text-sm text-muted p-3 bg-background rounded border border-border">
            📁 Current: {dataset.filename}
          </div>
        )}
      </div>
      
      {dataset && (
        <div className="flex flex-col h-[calc(100%-300px)]">
          <SummarySection summary={dataset.summary} />
          <SchemaSection schema={dataset.schema} />
        </div>
      )}
    </div>
  );
};