import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface ProjectAnalytics {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  averageCompletionTime: number;
  totalAssessments: number;
  projectsByMonth: Array<{ month: string; count: number }>;
  projectsByStatus: Array<{ status: string; count: number; color: string }>;
}

interface AssessmentAnalytics {
  categories: Array<{
    name: string;
    score: number;
    maxScore: number;
    metrics: Array<{
      name: string;
      value: number;
      target: number;
      unit: string;
      status: "success" | "warning" | "error";
      trend: "up" | "down" | "stable";
      trendValue: number;
    }>;
  }>;
  overallScore: number;
  completionRate: number;
  averageTime: number;
}

interface FieldCompletionData {
  fields: Array<{
    id: string;
    name: string;
    section: string;
    completionRate: number;
    attemptCount: number;
    averageTime: number;
  }>;
  sections: string[];
  overallCompletion: number;
}

export function useProjectAnalytics(filters?: {
  startDate?: string;
  endDate?: string;
  status?: string;
}) {
  return useQuery({
    queryKey: ["project-analytics", filters],
    queryFn: async () => {
      const response = await axios.get<ProjectAnalytics>(
        "/api/v1/analytics/projects",
        { params: filters },
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAssessmentAnalytics(projectId?: string) {
  return useQuery({
    queryKey: ["assessment-analytics", projectId],
    queryFn: async () => {
      const url = projectId
        ? `/api/v1/analytics/assessments/${projectId}`
        : "/api/v1/analytics/assessments";
      const response = await axios.get<AssessmentAnalytics>(url);
      return response.data;
    },
    enabled: !!projectId || projectId === undefined,
    staleTime: 5 * 60 * 1000,
  });
}

export function useFieldCompletionHeatmap(assessmentId?: string) {
  return useQuery({
    queryKey: ["field-completion-heatmap", assessmentId],
    queryFn: async () => {
      const url = assessmentId
        ? `/api/v1/analytics/field-completion/${assessmentId}`
        : "/api/v1/analytics/field-completion";
      const response = await axios.get<FieldCompletionData>(url);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useExportAnalytics() {
  const exportData = async (
    format: "csv" | "pdf",
    type: "projects" | "assessments",
  ) => {
    try {
      const response = await axios.get(`/api/v1/analytics/export`, {
        params: { format, type },
        responseType: "blob",
      });

      const blob = new Blob([response.data], {
        type: format === "csv" ? "text/csv" : "application/pdf",
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${type}-analytics-${new Date().toISOString()}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      throw error;
    }
  };

  return { exportData };
}
