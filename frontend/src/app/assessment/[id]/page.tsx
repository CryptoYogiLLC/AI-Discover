"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import {
  EnhancedForm,
  ProgressIndicator,
  CollaborativeIndicator,
} from "@/components/data-entry";
import { CacheMetricsDashboard } from "@/components/ai-assistance";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAISuggestions } from "@/hooks/use-ai-suggestions";
import { useCollaborativeEditing } from "@/hooks/use-collaborative-editing";
import toast from "react-hot-toast";

// Mock data for demo
const mockFormFields = [
  {
    name: "application_name",
    label: "Application Name",
    type: "text" as const,
    required: true,
    placeholder: "Enter application name",
  },
  {
    name: "business_criticality",
    label: "Business Criticality",
    type: "text" as const,
    required: true,
    placeholder: "High, Medium, or Low",
  },
  {
    name: "user_count",
    label: "User Count",
    type: "number" as const,
    required: true,
    placeholder: "Number of users",
  },
  {
    name: "deployment_date",
    label: "Deployment Date",
    type: "date" as const,
    required: false,
  },
];

const mockSteps = [
  {
    id: "basic-info",
    name: "Basic Information",
    description: "Application details and metadata",
    status: "current" as const,
    completedFields: 2,
    totalFields: 4,
  },
  {
    id: "technical",
    name: "Technical Assessment",
    description: "Architecture and technology stack",
    status: "upcoming" as const,
    completedFields: 0,
    totalFields: 8,
  },
  {
    id: "migration",
    name: "Migration Readiness",
    description: "6R recommendation and planning",
    status: "upcoming" as const,
    completedFields: 0,
    totalFields: 6,
  },
  {
    id: "review",
    name: "Review & Submit",
    description: "Final review and submission",
    status: "locked" as const,
  },
];

const mockCollaborators = [
  {
    id: "user1",
    name: "John Doe",
    email: "john@example.com",
    color: "#3B82F6",
    isOnline: true,
    currentField: "application_name",
  },
  {
    id: "user2",
    name: "Jane Smith",
    email: "jane@example.com",
    color: "#8B5CF6",
    isOnline: true,
    currentField: "business_criticality",
  },
  {
    id: "user3",
    name: "Bob Johnson",
    email: "bob@example.com",
    color: "#EF4444",
    isOnline: false,
    lastActive: new Date(Date.now() - 3600000),
  },
];

const mockCacheMetrics = {
  hitRate: 85,
  missRate: 15,
  totalRequests: 1234,
  avgResponseTime: 45,
  cacheSize: 75,
  maxCacheSize: 100,
  evictionCount: 23,
  lastUpdated: new Date(),
};

export default function AssessmentPage() {
  const params = useParams();
  const assessmentId = params.id as string;
  const [currentUserId] = useState("user1");

  const { suggestions } = useAISuggestions({
    projectId: assessmentId,
    formType: "assessment",
  });

  useCollaborativeEditing({
    projectId: assessmentId,
    userId: currentUserId,
    onFieldUpdate: (update) => {
      toast.success(`${update.field} updated by collaborator`);
    },
  });

  const handleFormSubmit = (data: Record<string, unknown>) => {
    console.error("Form submitted:", data);
    toast.success("Assessment saved successfully!");
  };

  const handleSaveDraft = (data: Record<string, unknown>) => {
    console.error("Draft saved:", data);
    toast.success("Draft saved!");
  };

  const handleStepClick = (stepId: string) => {
    // Step navigation logic would go here
    toast.success(`Navigating to step: ${stepId}`);
  };

  const handleCacheRefresh = () => {
    // Cache refresh logic would go here
    toast.success("Cache metrics refreshed");
  };

  // Transform suggestions for the form
  const formSuggestions = Object.entries(suggestions || {}).reduce(
    (acc, [field, suggestion]) => {
      acc[field] = {
        value: suggestion.value,
        confidence: suggestion.confidence,
      };
      return acc;
    },
    {} as Record<string, { value: string; confidence: number }>,
  );

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Application Assessment</h1>
          <p className="text-muted-foreground">
            AI-powered assessment with real-time collaboration
          </p>
        </div>
        <CollaborativeIndicator
          collaborators={mockCollaborators}
          currentUserId={currentUserId}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Tabs defaultValue="form" className="space-y-4">
            <TabsList>
              <TabsTrigger value="form">Assessment Form</TabsTrigger>
              <TabsTrigger value="cache">Cache Performance</TabsTrigger>
            </TabsList>

            <TabsContent value="form">
              <EnhancedForm
                fields={mockFormFields}
                onSubmit={handleFormSubmit}
                onSaveDraft={handleSaveDraft}
                aiSuggestions={formSuggestions}
              />
            </TabsContent>

            <TabsContent value="cache">
              <CacheMetricsDashboard
                data={mockCacheMetrics}
                onRefresh={handleCacheRefresh}
              />
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Assessment Progress</h3>
            <ProgressIndicator
              steps={mockSteps}
              currentStep="basic-info"
              onStepClick={handleStepClick}
            />
          </Card>
        </div>
      </div>
    </div>
  );
}
