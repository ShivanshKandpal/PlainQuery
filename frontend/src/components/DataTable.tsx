interface DataTableProps {
  data: Record<string, any>[];
}

export const DataTable = ({ data }: DataTableProps) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-muted">
        No data to display
      </div>
    );
  }

  const columns = Object.keys(data[0]);

  const formatValue = (value: any) => {
    if (typeof value === "number") {
      return value.toLocaleString();
    }
    if (value === null || value === undefined) {
      return "—";
    }
    return String(value);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((column) => (
              <th
                key={column}
                className="text-left p-3 font-medium text-foreground bg-background"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={index}
              className="border-b border-border hover:bg-background/50"
            >
              {columns.map((column) => (
                <td
                  key={column}
                  className="p-3 text-muted"
                >
                  {formatValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};