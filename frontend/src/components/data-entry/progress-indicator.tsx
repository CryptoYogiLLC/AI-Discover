"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Check, Circle, Lock } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface Step {
  id: string;
  name: string;
  description?: string;
  status: "completed" | "current" | "upcoming" | "locked";
  completedFields?: number;
  totalFields?: number;
}

interface ProgressIndicatorProps {
  steps: Step[];
  currentStep?: string;
  // eslint-disable-next-line no-unused-vars
  onStepClick?: (stepId: string) => void;
  className?: string;
  variant?: "linear" | "circular";
}

export function ProgressIndicator({
  steps,
  currentStep,
  onStepClick,
  className,
  variant = "linear",
}: ProgressIndicatorProps) {
  const currentStepIndex = steps.findIndex(
    (step) => step.id === currentStep || step.status === "current",
  );
  const overallProgress =
    (steps.filter((s) => s.status === "completed").length / steps.length) *
      100 || 0;

  const getStepIcon = (step: Step) => {
    switch (step.status) {
      case "completed":
        return Check;
      case "locked":
        return Lock;
      default:
        return Circle;
    }
  };

  const getStepColor = (step: Step) => {
    switch (step.status) {
      case "completed":
        return "bg-green-500 text-white";
      case "current":
        return "bg-primary text-primary-foreground";
      case "locked":
        return "bg-gray-300 text-gray-500";
      default:
        return "bg-gray-200 text-gray-600";
    }
  };

  if (variant === "circular") {
    return (
      <div className={cn("relative", className)}>
        <div className="flex items-center justify-center">
          <div className="relative h-48 w-48">
            {/* Background circle */}
            <svg className="h-48 w-48 -rotate-90 transform">
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-gray-200"
              />
              <circle
                cx="96"
                cy="96"
                r="80"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${(overallProgress / 100) * 502.65} 502.65`}
                className="text-primary transition-all duration-500"
              />
            </svg>
            {/* Center content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold">
                {Math.round(overallProgress)}%
              </span>
              <span className="text-sm text-muted-foreground">Complete</span>
            </div>
          </div>
        </div>
        {/* Step indicators */}
        <div className="mt-6 space-y-2">
          {steps.map((step) => {
            const Icon = getStepIcon(step);
            return (
              <div
                key={step.id}
                className={cn(
                  "flex items-center gap-3 rounded-lg p-2 transition-colors",
                  step.status === "current" && "bg-primary/10",
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    getStepColor(step),
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{step.name}</p>
                  {step.completedFields !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      {step.completedFields}/{step.totalFields} fields
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Overall progress */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Overall Progress</p>
          <p className="text-xs text-muted-foreground">
            {steps.filter((s) => s.status === "completed").length} of{" "}
            {steps.length} steps completed
          </p>
        </div>
        <Badge variant="outline">{Math.round(overallProgress)}%</Badge>
      </div>
      <Progress value={overallProgress} className="h-2" />

      {/* Steps */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-4 top-8 h-[calc(100%-4rem)] w-0.5 bg-gray-200" />
        <div
          className="absolute left-4 top-8 w-0.5 bg-primary transition-all duration-500"
          style={{
            height: `${(currentStepIndex / (steps.length - 1)) * 100}%`,
            maxHeight: "calc(100% - 4rem)",
          }}
        />

        {/* Step items */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = getStepIcon(step);
            const isClickable =
              step.status !== "locked" && onStepClick !== undefined;

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "relative flex items-start gap-4",
                  isClickable && "cursor-pointer",
                )}
                onClick={() => isClickable && onStepClick(step.id)}
              >
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div
                        className={cn(
                          "relative z-10 flex h-8 w-8 items-center justify-center rounded-full transition-all",
                          getStepColor(step),
                          isClickable && "hover:scale-110",
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{step.status}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-2">
                    <h4
                      className={cn(
                        "font-medium",
                        step.status === "current" && "text-primary",
                        step.status === "locked" && "text-muted-foreground",
                      )}
                    >
                      {step.name}
                    </h4>
                    {step.status === "current" && (
                      <Badge variant="default" className="h-5">
                        Current
                      </Badge>
                    )}
                  </div>
                  {step.description && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {step.description}
                    </p>
                  )}
                  {step.completedFields !== undefined &&
                    step.totalFields !== undefined && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">
                            {step.completedFields} of {step.totalFields} fields
                          </span>
                          <span className="font-medium">
                            {Math.round(
                              (step.completedFields / step.totalFields) * 100,
                            )}
                            %
                          </span>
                        </div>
                        <Progress
                          value={
                            (step.completedFields / step.totalFields) * 100
                          }
                          className="mt-1 h-1.5"
                        />
                      </div>
                    )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
