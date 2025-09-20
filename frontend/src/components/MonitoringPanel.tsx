import { useState, useEffect } from "react";
import { api, ApiMonitoringResult } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DollarSign, Clock, Activity, AlertTriangle } from "lucide-react";

export const MonitoringPanel = () => {
  const [monitoring, setMonitoring] = useState<ApiMonitoringResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMonitoring = async () => {
    try {
      setLoading(true);
      const data = await api.getMonitoring();
      setMonitoring(data);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetMonitoring = async () => {
    try {
      await api.resetMonitoring();
      await fetchMonitoring(); // Refresh data
    } catch (error) {
      console.error('Failed to reset monitoring:', error);
    }
  };

  useEffect(() => {
    fetchMonitoring();
  }, []);

  if (!monitoring) {
    return (
      <div className="p-4">
        <Button onClick={fetchMonitoring} disabled={loading}>
          {loading ? 'Loading...' : 'Load Monitoring Data'}
        </Button>
      </div>
    );
  }

  const budgetPercentage = (monitoring.total_cost / monitoring.cost_cap) * 100;
  const isNearLimit = budgetPercentage > 80;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">API Monitoring</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchMonitoring}>
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={resetMonitoring}>
            Reset
          </Button>
        </div>
      </div>

      {/* Cost Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${monitoring.total_cost.toFixed(6)}</div>
            <p className="text-xs text-muted-foreground">
              of ${monitoring.cost_cap} daily cap
            </p>
            <div className={`text-xs mt-1 ${isNearLimit ? 'text-red-600' : 'text-green-600'}`}>
              {budgetPercentage.toFixed(1)}% used
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{monitoring.total_requests}</div>
            <p className="text-xs text-muted-foreground">
              API calls made today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Latency</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{monitoring.average_latency}s</div>
            <p className="text-xs text-muted-foreground">
              Response time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Budget Warning */}
      {isNearLimit && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <CardTitle className="text-sm text-yellow-800">Budget Warning</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-yellow-700">
              You've used {budgetPercentage.toFixed(1)}% of your daily API budget. 
              Remaining: ${monitoring.remaining_budget.toFixed(6)}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recent Requests */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Recent Requests</CardTitle>
          <CardDescription>Last 10 API calls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {monitoring.recent_requests.length === 0 ? (
              <p className="text-sm text-muted-foreground">No requests yet</p>
            ) : (
              monitoring.recent_requests.map((request, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-background rounded border">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{request.question}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(request.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-2">
                    <Badge variant="outline" className="text-xs">
                      {request.latency.toFixed(2)}s
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      ${request.cost.toFixed(6)}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};