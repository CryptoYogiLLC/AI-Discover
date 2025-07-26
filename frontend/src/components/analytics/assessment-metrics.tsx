"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  Target,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface AssessmentMetric {
  name: string;
  value: number;
  target: number;
  unit: string;
  status: "success" | "warning" | "error";
  trend: "up" | "down" | "stable";
  trendValue: number;
}

interface AssessmentCategory {
  name: string;
  score: number;
  maxScore: number;
  metrics: AssessmentMetric[];
}

interface AssessmentMetricsProps {
  categories?: AssessmentCategory[];
  overallScore?: number;
  completionRate?: number;
  averageTime?: number;
  isLoading?: boolean;
  className?: string;
}

export function AssessmentMetrics({
  categories = [],
  overallScore = 0,
  completionRate = 0,
  averageTime = 0,
  className,
}: AssessmentMetricsProps) {
  const getStatusColor = (status: AssessmentMetric["status"]) => {
    switch (status) {
      case "success":
        return "text-green-500";
      case "warning":
        return "text-yellow-500";
      case "error":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  const getStatusIcon = (status: AssessmentMetric["status"]) => {
    switch (status) {
      case "success":
        return CheckCircle;
      case "warning":
        return AlertCircle;
      case "error":
        return XCircle;
      default:
        return Target;
    }
  };

  const getTrendIcon = (trend: AssessmentMetric["trend"]) => {
    switch (trend) {
      case "up":
        return TrendingUp;
      case "down":
        return TrendingDown;
      default:
        return null;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Overall Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Overall Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span
                  className={cn(
                    "text-3xl font-bold",
                    getScoreColor(overallScore),
                  )}
                >
                  {overallScore}%
                </span>
                <Badge
                  variant={overallScore >= 80 ? "success" : "secondary"}
                  className="mb-1"
                >
                  {overallScore >= 80
                    ? "Excellent"
                    : overallScore >= 60
                      ? "Good"
                      : "Needs Improvement"}
                </Badge>
              </div>
              <Progress value={overallScore} className="mt-3 h-2" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Completion Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">{completionRate}%</span>
                <Badge variant="outline" className="mb-1">
                  <CheckCircle className="mr-1 h-3 w-3" />
                  Completed
                </Badge>
              </div>
              <Progress value={completionRate} className="mt-3 h-2" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Average Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">{averageTime}</span>
                <span className="text-sm text-muted-foreground">minutes</span>
              </div>
              <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Per assessment</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Category Breakdown */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Assessment Categories</h3>
        {categories.map((category, categoryIndex) => (
          <motion.div
            key={category.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: categoryIndex * 0.1 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">{category.name}</CardTitle>
                    <CardDescription>
                      {category.metrics.length} metrics tracked
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {category.score}/{category.maxScore}
                    </div>
                    <Badge
                      variant={
                        (category.score / category.maxScore) * 100 >= 80
                          ? "success"
                          : "secondary"
                      }
                    >
                      {Math.round((category.score / category.maxScore) * 100)}%
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {category.metrics.map((metric, metricIndex) => {
                    const StatusIcon = getStatusIcon(metric.status);
                    const TrendIcon = getTrendIcon(metric.trend);

                    return (
                      <motion.div
                        key={metric.name}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{
                          delay: categoryIndex * 0.1 + metricIndex * 0.05,
                        }}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="flex items-center gap-3">
                          <StatusIcon
                            className={cn(
                              "h-4 w-4",
                              getStatusColor(metric.status),
                            )}
                          />
                          <div>
                            <p className="text-sm font-medium">{metric.name}</p>
                            <p className="text-xs text-muted-foreground">
                              Target: {metric.target}
                              {metric.unit}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <p className="text-sm font-bold">
                              {metric.value}
                              {metric.unit}
                            </p>
                            {TrendIcon && (
                              <div className="flex items-center gap-1 text-xs">
                                <TrendIcon
                                  className={cn(
                                    "h-3 w-3",
                                    metric.trend === "up"
                                      ? "text-green-500"
                                      : "text-red-500",
                                  )}
                                />
                                <span
                                  className={
                                    metric.trend === "up"
                                      ? "text-green-500"
                                      : "text-red-500"
                                  }
                                >
                                  {metric.trendValue}%
                                </span>
                              </div>
                            )}
                          </div>
                          <Progress
                            value={(metric.value / metric.target) * 100}
                            className="h-1.5 w-20"
                          />
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
