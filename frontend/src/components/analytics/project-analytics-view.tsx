"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  FileText,
  Calendar,
  Download,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ProjectStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  averageCompletionTime: number;
  totalAssessments: number;
  projectsByMonth: Array<{ month: string; count: number }>;
  projectsByStatus: Array<{ status: string; count: number; color: string }>;
}

interface ProjectAnalyticsViewProps {
  stats?: ProjectStats;
  // eslint-disable-next-line no-unused-vars
  onExport?: (format: "csv" | "pdf") => void;
  isLoading?: boolean;
  className?: string;
}

export function ProjectAnalyticsView({
  stats,
  onExport,
  className,
}: ProjectAnalyticsViewProps) {
  const defaultStats: ProjectStats = {
    totalProjects: 0,
    activeProjects: 0,
    completedProjects: 0,
    averageCompletionTime: 0,
    totalAssessments: 0,
    projectsByMonth: [],
    projectsByStatus: [],
  };

  const data = stats || defaultStats;

  const summaryCards = [
    {
      title: "Total Projects",
      value: data.totalProjects,
      icon: FileText,
      trend: "+12%",
      color: "text-blue-500",
    },
    {
      title: "Active Projects",
      value: data.activeProjects,
      icon: TrendingUp,
      trend: "+5%",
      color: "text-green-500",
    },
    {
      title: "Completed",
      value: data.completedProjects,
      icon: BarChart3,
      trend: "+18%",
      color: "text-purple-500",
    },
    {
      title: "Avg. Completion",
      value: `${data.averageCompletionTime}d`,
      icon: Calendar,
      trend: "-3d",
      color: "text-orange-500",
    },
  ];

  const maxMonthCount = Math.max(
    ...data.projectsByMonth.map((m) => m.count),
    1,
  );

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Project Analytics</h2>
          <p className="text-sm text-muted-foreground">
            Track project progress and performance metrics
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => onExport?.("csv")} variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Button onClick={() => onExport?.("pdf")} variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {card.title}
                  </CardTitle>
                  <Icon className={cn("h-4 w-4", card.color)} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{card.value}</div>
                  <p className="text-xs text-muted-foreground">
                    <span className="text-green-500">{card.trend}</span> from
                    last month
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Charts */}
      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="status">Status Distribution</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Projects Over Time</CardTitle>
              <CardDescription>Monthly project creation trends</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.projectsByMonth.map((month, index) => (
                  <motion.div
                    key={month.month}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center gap-4"
                  >
                    <div className="w-16 text-sm font-medium">
                      {month.month}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-6 bg-primary transition-all duration-500"
                          style={{
                            width: `${(month.count / maxMonthCount) * 100}%`,
                          }}
                        />
                        <span className="text-sm font-medium">
                          {month.count}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="status" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Project Status Breakdown</CardTitle>
              <CardDescription>
                Distribution of projects by current status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.projectsByStatus.map((status, index) => (
                  <motion.div
                    key={status.status}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: status.color }}
                        />
                        <span className="font-medium">{status.status}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">
                          {status.count}
                        </span>
                        <Badge variant="secondary">
                          {((status.count / data.totalProjects) * 100).toFixed(
                            1,
                          )}
                          %
                        </Badge>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Key performance indicators for project completion
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">
                      On-Time Completion Rate
                    </span>
                    <span className="text-sm font-bold text-green-500">
                      85%
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-secondary">
                    <div
                      className="h-2 rounded-full bg-green-500"
                      style={{ width: "85%" }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">
                      Resource Utilization
                    </span>
                    <span className="text-sm font-bold text-blue-500">72%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-secondary">
                    <div
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: "72%" }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-medium">
                      Assessment Completion
                    </span>
                    <span className="text-sm font-bold text-purple-500">
                      91%
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-secondary">
                    <div
                      className="h-2 rounded-full bg-purple-500"
                      style={{ width: "91%" }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
