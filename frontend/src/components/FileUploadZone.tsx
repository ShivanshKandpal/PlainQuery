import { useState, useRef } from "react";
import { Upload } from "lucide-react";

interface FileUploadZoneProps {
  onFileUpload: (file: File) => void;
}

export const FileUploadZone = ({ onFileUpload }: FileUploadZoneProps) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const csvFile = files.find(file => file.name.toLowerCase().endsWith('.csv'));
    
    if (csvFile) {
      onFileUpload(csvFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.csv')) {
      onFileUpload(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
        isDragOver 
          ? "border-primary bg-primary/5" 
          : "border-border hover:border-primary/50"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <Upload className="mx-auto h-6 w-6 text-muted mb-2" />
      <p className="text-foreground font-medium mb-1 text-sm">
        Upload CSV file
      </p>
      <p className="text-muted text-xs">
        Drag & drop or click to browse
      </p>
      
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};