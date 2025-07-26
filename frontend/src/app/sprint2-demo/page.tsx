"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  FormFieldSuggestion,
  ValidationFeedback,
  CacheMetricsDashboard,
} from "@/components/ai-assistance";
import {
  ProjectAnalyticsView,
  AssessmentMetrics,
  FieldCompletionHeatmap,
} from "@/components/analytics";
import {
  EnhancedForm,
  ProgressIndicator,
  CollaborativeIndicator,
} from "@/components/data-entry";

// Demo data
const demoFormFields = [
  {
    name: "project_name",
    label: "Project Name",
    type: "text" as const,
    required: true,
    placeholder: "Enter project name",
  },
  {
    name: "description",
    label: "Description",
    type: "text" as const,
    required: true,
    placeholder: "Project description",
  },
  {
    name: "start_date",
    label: "Start Date",
    type: "date" as const,
    required: true,
  },
  {
    name: "team_size",
    label: "Team Size",
    type: "number" as const,
    required: true,
    placeholder: "Number of team members",
  },
];

const demoSteps = [
  {
    id: "project-info",
    name: "Project Information",
    description: "Basic project details",
    status: "completed" as const,
    completedFields: 4,
    totalFields: 4,
  },
  {
    id: "resources",
    name: "Resource Planning",
    description: "Team and budget allocation",
    status: "current" as const,
    completedFields: 2,
    totalFields: 6,
  },
  {
    id: "timeline",
    name: "Timeline",
    description: "Milestones and deadlines",
    status: "upcoming" as const,
    completedFields: 0,
    totalFields: 5,
  },
  {
    id: "approval",
    name: "Approval",
    description: "Review and sign-off",
    status: "locked" as const,
  },
];

const demoProjectStats = {
  totalProjects: 156,
  activeProjects: 42,
  completedProjects: 98,
  averageCompletionTime: 28,
  totalAssessments: 312,
  projectsByMonth: [
    { month: "Jan", count: 12 },
    { month: "Feb", count: 18 },
    { month: "Mar", count: 24 },
    { month: "Apr", count: 20 },
    { month: "May", count: 28 },
    { month: "Jun", count: 35 },
  ],
  projectsByStatus: [
    { status: "Planning", count: 15, color: "#3B82F6" },
    { status: "In Progress", count: 42, color: "#10B981" },
    { status: "Review", count: 16, color: "#F59E0B" },
    { status: "Completed", count: 98, color: "#8B5CF6" },
  ],
};

const demoAssessmentCategories = [
  {
    name: "Technical Readiness",
    score: 85,
    maxScore: 100,
    metrics: [
      {
        name: "Code Quality",
        value: 87,
        target: 90,
        unit: "%",
        status: "warning" as const,
        trend: "up" as const,
        trendValue: 5,
      },
      {
        name: "Test Coverage",
        value: 92,
        target: 80,
        unit: "%",
        status: "success" as const,
        trend: "up" as const,
        trendValue: 8,
      },
      {
        name: "Documentation",
        value: 75,
        target: 85,
        unit: "%",
        status: "warning" as const,
        trend: "stable" as const,
        trendValue: 0,
      },
    ],
  },
  {
    name: "Business Alignment",
    score: 78,
    maxScore: 100,
    metrics: [
      {
        name: "Stakeholder Satisfaction",
        value: 82,
        target: 85,
        unit: "%",
        status: "warning" as const,
        trend: "up" as const,
        trendValue: 3,
      },
      {
        name: "ROI Achievement",
        value: 74,
        target: 80,
        unit: "%",
        status: "error" as const,
        trend: "down" as const,
        trendValue: -2,
      },
    ],
  },
];

const demoHeatmapData = {
  fields: Array.from({ length: 40 }, (_, i) => ({
    id: `field-${i}`,
    name: `Field ${i + 1}`,
    section: `Section ${Math.floor(i / 10) + 1}`,
    completionRate: Math.floor(Math.random() * 100),
    attemptCount: Math.floor(Math.random() * 50) + 1,
    averageTime: Math.floor(Math.random() * 120) + 10,
  })),
  sections: ["Section 1", "Section 2", "Section 3", "Section 4"],
  overallCompletion: 72,
};

const demoCollaborators = [
  {
    id: "demo1",
    name: "Alice Johnson",
    email: "alice@example.com",
    color: "#3B82F6",
    isOnline: true,
    currentField: "project_name",
  },
  {
    id: "demo2",
    name: "Bob Smith",
    email: "bob@example.com",
    color: "#10B981",
    isOnline: true,
  },
  {
    id: "demo3",
    name: "Carol White",
    email: "carol@example.com",
    color: "#F59E0B",
    isOnline: false,
    lastActive: new Date(Date.now() - 7200000),
  },
];

const demoCacheMetrics = {
  hitRate: 89,
  missRate: 11,
  totalRequests: 5432,
  avgResponseTime: 32,
  cacheSize: 82,
  maxCacheSize: 100,
  evictionCount: 45,
  lastUpdated: new Date(),
};

const demoValidationErrors = [
  {
    field: "Project Budget",
    message: "Budget exceeds allocated limit",
    suggestion: "Consider reducing scope or requesting additional funding",
  },
  {
    field: "Timeline",
    message: "End date is before start date",
    suggestion: "Please ensure the end date is after the start date",
  },
];

export default function Sprint2DemoPage() {
  const [showValidation, setShowValidation] = useState(false);

  const handleFormSubmit = (data: Record<string, unknown>) => {
    // Handle form submission
    void data;
  };

  const handleExport = (format: "csv" | "pdf") => {
    // Handle export functionality
    void format;
  };

  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold">Sprint 2 Features Demo</h1>
        <p className="text-lg text-muted-foreground">
          AI Assistance, Analytics Dashboard, and Enhanced Data Entry
        </p>
      </div>

      <Tabs defaultValue="ai-assistance" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="ai-assistance">AI Assistance</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="data-entry">Data Entry</TabsTrigger>
        </TabsList>

        <TabsContent value="ai-assistance" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>AI Field Suggestions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormFieldSuggestion
                  fieldName="Project Name"
                  suggestion="Cloud Migration Initiative Q3"
                  confidence={0.92}
                  onAccept={(value) => {
                    /* Handle accept */ void value;
                  }}
                  onReject={() => {
                    /* Handle reject */
                  }}
                />
                <FormFieldSuggestion
                  fieldName="Budget Estimate"
                  suggestion="$125,000 - $150,000"
                  confidence={0.78}
                  onAccept={(value) => {
                    /* Handle accept */ void value;
                  }}
                  onReject={() => {
                    /* Handle reject */
                  }}
                />
                <FormFieldSuggestion fieldName="Team Size" isLoading />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Validation Feedback</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <button
                  onClick={() => setShowValidation(!showValidation)}
                  className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
                >
                  Toggle Validation
                </button>
                <ValidationFeedback
                  errors={showValidation ? demoValidationErrors : []}
                  isValidating={false}
                  onHelpRequest={(field) => {
                    /* Handle help request */
                    void field;
                  }}
                />
              </CardContent>
            </Card>
          </div>

          <CacheMetricsDashboard
            data={demoCacheMetrics}
            onRefresh={() => {
              /* Handle cache refresh */
            }}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <ProjectAnalyticsView
            stats={demoProjectStats}
            onExport={handleExport}
          />

          <AssessmentMetrics
            categories={demoAssessmentCategories}
            overallScore={82}
            completionRate={91}
            averageTime={23}
          />

          <FieldCompletionHeatmap
            data={demoHeatmapData}
            onFieldClick={(field) => {
              /* Handle field click */ void field;
            }}
          />
        </TabsContent>

        <TabsContent value="data-entry" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <EnhancedForm
                fields={demoFormFields}
                onSubmit={handleFormSubmit}
                onSaveDraft={(data) => {
                  /* Handle draft save */ void data;
                }}
                aiSuggestions={{
                  project_name: {
                    value: "Enterprise Digital Transformation",
                    confidence: 0.88,
                  },
                  team_size: {
                    value: "8",
                    confidence: 0.75,
                  },
                }}
              />
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Progress Tracking</CardTitle>
                    <CollaborativeIndicator
                      collaborators={demoCollaborators}
                      currentUserId="demo1"
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <ProgressIndicator
                    steps={demoSteps}
                    currentStep="resources"
                    onStepClick={(stepId) => {
                      /* Handle step click */
                      void stepId;
                    }}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Circular Progress View</CardTitle>
                </CardHeader>
                <CardContent>
                  <ProgressIndicator
                    steps={demoSteps}
                    currentStep="resources"
                    variant="circular"
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
