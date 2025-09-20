import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { DataContextPanel } from "@/components/DataContextPanel";
import { QueryResultsPanel } from "@/components/QueryResultsPanel";
import { MonitoringPanel } from "@/components/MonitoringPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";

export interface DatasetInfo {
  filename: string;
  summary: string;
  schema: SchemaColumn[];
}

export interface SchemaColumn {
  name: string;
  type: "string" | "number" | "date" | "boolean";
  stats: string;
}

export interface QueryResult {
  explanation: string;
  sql: string;
  status: "verified" | "error" | "rejected";
  latency: number;
  cost?: number;
  total_cost?: number;
  data: Record<string, any>[];
}

const Index = () => {
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);

  // Don't auto-load database - let users choose their data source
  // useEffect(() => {
  //   const loadSchema = async () => {
  //     try {
  //       const schemaResult = await api.getSchema();
  //       setDataset({
  //         filename: "database.db (existing)",
  //         summary: "Existing database with sample data. You can upload a CSV file to work with your own data, or query the existing database.",
  //         schema: [
  //           { name: "Database Schema", type: "string", stats: "Ready for queries" }
  //         ]
  //       });
  //     } catch (error) {
  //       console.error('Failed to load schema:', error);
  //     }
  //   };
  //   loadSchema();
  // }, []);

  const handleFileUpload = async (file: File) => {
    try {
      const result = await api.uploadCSV(file);
      
      // Convert backend schema info to frontend format
      const frontendSchema = result.schema_info.columns.map(col => ({
        name: col.name,
        type: col.type as "string" | "number" | "date" | "boolean",
        stats: col.stats
      }));

      setDataset({
        filename: file.name,
        summary: `Uploaded dataset: ${file.name}. Contains ${result.schema_info.row_count} rows with ${result.schema_info.columns.length} columns. Ready for queries.`,
        schema: frontendSchema
      });
    } catch (error) {
      console.error('File upload failed:', error);
      alert('File upload failed: ' + error);
    }
  };

  const handleUseExistingDB = async () => {
    try {
      const schemaResult = await api.getSchema();
      
      // Use structured schema data if available
      let frontendSchema: SchemaColumn[] = [];
      let summary = "Using existing database with sample data. This database contains customer and order information that you can query.";
      
      if (schemaResult.schema_info && schemaResult.schema_info.columns.length > 0) {
        frontendSchema = schemaResult.schema_info.columns.map(col => ({
          name: col.name,
          type: col.type as "string" | "number" | "date" | "boolean",
          stats: col.stats
        }));
        
        summary = `Using existing database: ${schemaResult.schema_info.table_name}. Contains ${schemaResult.schema_info.row_count} rows with ${schemaResult.schema_info.columns.length} columns. Ready for queries.`;
      } else {
        // Fallback for when structured data is not available
        frontendSchema = [
          { name: "Database Schema", type: "string", stats: "Ready for queries" }
        ];
      }
      
      setDataset({
        filename: "database.db (existing)",
        summary: summary,
        schema: frontendSchema
      });
    } catch (error) {
      console.error('Failed to load schema:', error);
      alert('Failed to load existing database: ' + error);
    }
  };

  const handleQuery = async (question: string) => {
    const startTime = Date.now();
    
    try {
      const result = await api.generateSQL(question);
      const latency = result.latency || (Date.now() - startTime) / 1000;
      
      // Convert the array of arrays result to array of objects
      const data = result.result.map(row => {
        const obj: Record<string, any> = {};
        result.columns.forEach((col, index) => {
          obj[col] = row[index];
        });
        return obj;
      });
      
      setQueryResult({
        explanation: `Generated SQL query for: "${question}"`,
        sql: result.sql_query,
        status: "verified",
        latency,
        cost: result.cost,
        total_cost: result.total_cost,
        data
      });
    } catch (error: any) {
      const latency = (Date.now() - startTime) / 1000;
      
      // Extract dynamic error message from API response
      let errorMessage = `Error processing query: "${question}"`;
      if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      setQueryResult({
        explanation: errorMessage,
        sql: "",
        status: "error",
        latency,
        data: []
      });
      console.error('Query failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="flex h-[calc(100vh-4rem)]">
        {/* Left Column - Data Context Panel */}
        <div className="w-[35%] border-r border-border">
          <DataContextPanel 
            dataset={dataset}
            onFileUpload={handleFileUpload}
            onUseExistingDB={handleUseExistingDB}
          />
        </div>
        
        {/* Right Column - Tabbed Interface */}
        <div className="flex-1">
          <Tabs defaultValue="query" className="h-full">
            <div className="border-b border-border px-6 py-2">
              <TabsList>
                <TabsTrigger value="query">Query & Results</TabsTrigger>
                <TabsTrigger value="monitoring">API Monitoring</TabsTrigger>
              </TabsList>
            </div>
            
            <TabsContent value="query" className="h-[calc(100%-3rem)] m-0">
              <QueryResultsPanel 
                dataset={dataset}
                queryResult={queryResult}
                onQuery={handleQuery}
              />
            </TabsContent>
            
            <TabsContent value="monitoring" className="h-[calc(100%-3rem)] m-0 p-6">
              <MonitoringPanel />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Index;