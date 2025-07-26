"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ProjectAnalyticsView,
  AssessmentMetrics,
  FieldCompletionHeatmap,
} from "@/components/analytics";
import {
  useProjectAnalytics,
  useAssessmentAnalytics,
  useFieldCompletionHeatmap,
  useExportAnalytics,
} from "@/hooks/use-analytics";

export default function AnalyticsPage() {
  const [selectedTab, setSelectedTab] = useState("projects");

  const { data: projectData, isLoading: projectLoading } =
    useProjectAnalytics();
  const { data: assessmentData, isLoading: assessmentLoading } =
    useAssessmentAnalytics();
  const { data: heatmapData, isLoading: heatmapLoading } =
    useFieldCompletionHeatmap();
  const { exportData } = useExportAnalytics();

  const handleExport = async (format: "csv" | "pdf") => {
    try {
      await exportData(format, selectedTab as "projects" | "assessments");
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const handleFieldClick = (field: {
    id: string;
    name: string;
    section: string;
    completionRate: number;
    attemptCount: number;
    averageTime: number;
  }) => {
    // Handle field click - could open a detailed view
    // For now, we'll just track the field name for potential future use
    void field;
  };

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-muted-foreground">
          Comprehensive insights into your projects and assessments
        </p>
      </div>

      <Tabs
        value={selectedTab}
        onValueChange={setSelectedTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="assessments">Assessments</TabsTrigger>
          <TabsTrigger value="heatmap">Field Completion</TabsTrigger>
        </TabsList>

        <TabsContent value="projects" className="space-y-4">
          <ProjectAnalyticsView
            stats={projectData}
            onExport={handleExport}
            isLoading={projectLoading}
          />
        </TabsContent>

        <TabsContent value="assessments" className="space-y-4">
          <AssessmentMetrics
            categories={assessmentData?.categories}
            overallScore={assessmentData?.overallScore}
            completionRate={assessmentData?.completionRate}
            averageTime={assessmentData?.averageTime}
            isLoading={assessmentLoading}
          />
        </TabsContent>

        <TabsContent value="heatmap" className="space-y-4">
          <FieldCompletionHeatmap
            data={heatmapData}
            onFieldClick={handleFieldClick}
            isLoading={heatmapLoading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
