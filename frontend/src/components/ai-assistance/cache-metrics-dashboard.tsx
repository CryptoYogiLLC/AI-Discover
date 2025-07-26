"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  Activity,
  TrendingUp,
  Clock,
  Database,
  RefreshCw,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface CacheMetric {
  label: string;
  value: number;
  unit: string;
  trend?: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

interface CacheMetricsData {
  hitRate: number;
  missRate: number;
  totalRequests: number;
  avgResponseTime: number;
  cacheSize: number;
  maxCacheSize: number;
  evictionCount: number;
  lastUpdated: Date;
}

interface CacheMetricsDashboardProps {
  data?: CacheMetricsData;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function CacheMetricsDashboard({
  data,
  onRefresh,
  isLoading = false,
  className,
}: CacheMetricsDashboardProps) {
  const defaultData: CacheMetricsData = {
    hitRate: 0,
    missRate: 0,
    totalRequests: 0,
    avgResponseTime: 0,
    cacheSize: 0,
    maxCacheSize: 100,
    evictionCount: 0,
    lastUpdated: new Date(),
  };

  const metricsData = data || defaultData;

  const metrics: CacheMetric[] = [
    {
      label: "Hit Rate",
      value: metricsData.hitRate,
      unit: "%",
      trend: 5.2,
      icon: TrendingUp,
      color: "text-green-500",
    },
    {
      label: "Response Time",
      value: metricsData.avgResponseTime,
      unit: "ms",
      trend: -12.3,
      icon: Clock,
      color: "text-blue-500",
    },
    {
      label: "Total Requests",
      value: metricsData.totalRequests,
      unit: "",
      icon: Activity,
      color: "text-purple-500",
    },
    {
      label: "Evictions",
      value: metricsData.evictionCount,
      unit: "",
      trend: 2.1,
      icon: Zap,
      color: "text-orange-500",
    },
  ];

  const formatValue = (value: number, unit: string) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M${unit}`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K${unit}`;
    }
    return `${value}${unit}`;
  };

  const cacheUsagePercentage =
    (metricsData.cacheSize / metricsData.maxCacheSize) * 100;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Cache Performance</h2>
          <p className="text-sm text-muted-foreground">
            Real-time cache metrics and performance indicators
          </p>
        </div>
        <Button
          onClick={onRefresh}
          disabled={isLoading}
          size="sm"
          variant="outline"
        >
          <RefreshCw
            className={cn("mr-2 h-4 w-4", isLoading && "animate-spin")}
          />
          Refresh
        </Button>
      </div>

      {/* Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {metric.label}
                  </CardTitle>
                  <Icon className={cn("h-4 w-4", metric.color)} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatValue(metric.value, metric.unit)}
                  </div>
                  {metric.trend && (
                    <div className="flex items-center gap-1 text-xs">
                      <span
                        className={cn(
                          metric.trend > 0 ? "text-green-500" : "text-red-500",
                        )}
                      >
                        {metric.trend > 0 ? "↑" : "↓"} {Math.abs(metric.trend)}%
                      </span>
                      <span className="text-muted-foreground">
                        from last hour
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Cache Usage */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Cache Storage</CardTitle>
            </div>
            <Badge variant={cacheUsagePercentage > 80 ? "warning" : "default"}>
              {cacheUsagePercentage.toFixed(1)}% Used
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={cacheUsagePercentage} className="h-3" />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{formatValue(metricsData.cacheSize, " MB")} used</span>
            <span>{formatValue(metricsData.maxCacheSize, " MB")} total</span>
          </div>
        </CardContent>
      </Card>

      {/* Performance Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Hit/Miss Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span>Cache Hits</span>
                  <span className="font-medium">{metricsData.hitRate}%</span>
                </div>
                <Progress value={metricsData.hitRate} className="h-2" />
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span>Cache Misses</span>
                  <span className="font-medium">{metricsData.missRate}%</span>
                </div>
                <Progress
                  value={metricsData.missRate}
                  className="h-2 [&>div]:bg-destructive"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Performance Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <div
                  className={cn(
                    "mt-1 h-2 w-2 rounded-full",
                    metricsData.hitRate > 80 ? "bg-green-500" : "bg-yellow-500",
                  )}
                />
                <p className="text-muted-foreground">
                  {metricsData.hitRate > 80
                    ? "Excellent cache performance with high hit rate"
                    : "Consider optimizing cache strategy for better hit rate"}
                </p>
              </div>
              <div className="flex items-start gap-2">
                <div
                  className={cn(
                    "mt-1 h-2 w-2 rounded-full",
                    metricsData.avgResponseTime < 50
                      ? "bg-green-500"
                      : "bg-yellow-500",
                  )}
                />
                <p className="text-muted-foreground">
                  {metricsData.avgResponseTime < 50
                    ? "Fast response times indicate healthy cache"
                    : "Response times could be improved"}
                </p>
              </div>
              <div className="flex items-start gap-2">
                <div
                  className={cn(
                    "mt-1 h-2 w-2 rounded-full",
                    cacheUsagePercentage < 80
                      ? "bg-green-500"
                      : "bg-orange-500",
                  )}
                />
                <p className="text-muted-foreground">
                  {cacheUsagePercentage < 80
                    ? "Cache has sufficient storage capacity"
                    : "Consider increasing cache size or implementing eviction policies"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-muted-foreground">
        Last updated: {metricsData.lastUpdated.toLocaleTimeString()}
      </div>
    </div>
  );
}
