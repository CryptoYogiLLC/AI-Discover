"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Info } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface FieldData {
  id: string;
  name: string;
  section: string;
  completionRate: number;
  attemptCount: number;
  averageTime: number;
}

interface HeatmapData {
  fields: FieldData[];
  sections: string[];
  overallCompletion: number;
}

interface FieldCompletionHeatmapProps {
  data?: HeatmapData;
  // eslint-disable-next-line no-unused-vars
  onFieldClick?: (field: FieldData) => void;
  isLoading?: boolean;
  className?: string;
}

export function FieldCompletionHeatmap({
  data,
  onFieldClick,
  className,
}: FieldCompletionHeatmapProps) {
  const defaultData: HeatmapData = {
    fields: [],
    sections: [],
    overallCompletion: 0,
  };

  const heatmapData = data || defaultData;

  const getHeatmapColor = (completionRate: number) => {
    if (completionRate >= 90) return "bg-green-500";
    if (completionRate >= 75) return "bg-green-400";
    if (completionRate >= 60) return "bg-yellow-400";
    if (completionRate >= 40) return "bg-orange-400";
    if (completionRate >= 20) return "bg-orange-500";
    return "bg-red-500";
  };

  const getHeatmapOpacity = (completionRate: number) => {
    return Math.max(0.2, completionRate / 100);
  };

  const groupedFields = heatmapData.sections.reduce(
    (acc, section) => {
      acc[section] = heatmapData.fields.filter(
        (field) => field.section === section,
      );
      return acc;
    },
    {} as Record<string, FieldData[]>,
  );

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Field Completion Heatmap</CardTitle>
            <CardDescription>
              Visual representation of form field completion rates
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              Overall: {heatmapData.overallCompletion}%
            </Badge>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs text-sm">
                    Darker colors indicate higher completion rates. Click on any
                    field for detailed metrics.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Legend */}
        <div className="mb-6 flex items-center justify-center gap-4">
          <span className="text-sm text-muted-foreground">Low</span>
          <div className="flex gap-1">
            {[20, 40, 60, 75, 90].map((rate) => (
              <div
                key={rate}
                className={cn("h-4 w-8 rounded", getHeatmapColor(rate))}
                style={{ opacity: getHeatmapOpacity(rate) }}
              />
            ))}
          </div>
          <span className="text-sm text-muted-foreground">High</span>
        </div>

        {/* Heatmap Grid */}
        <div className="space-y-6">
          {Object.entries(groupedFields).map(
            ([section, fields], sectionIndex) => (
              <motion.div
                key={section}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: sectionIndex * 0.1 }}
              >
                <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                  {section}
                </h4>
                <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10">
                  {fields.map((field, fieldIndex) => (
                    <TooltipProvider key={field.id}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <motion.button
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{
                              delay: sectionIndex * 0.1 + fieldIndex * 0.02,
                              type: "spring",
                              stiffness: 500,
                            }}
                            onClick={() => onFieldClick?.(field)}
                            className={cn(
                              "group relative aspect-square rounded-md transition-all hover:scale-110 hover:shadow-lg",
                              getHeatmapColor(field.completionRate),
                            )}
                            style={{
                              opacity: getHeatmapOpacity(field.completionRate),
                            }}
                          >
                            <div className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
                              <span className="text-xs font-bold text-white">
                                {field.completionRate}%
                              </span>
                            </div>
                          </motion.button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            <p className="font-medium">{field.name}</p>
                            <p className="text-xs">
                              Completion: {field.completionRate}%
                            </p>
                            <p className="text-xs">
                              Attempts: {field.attemptCount}
                            </p>
                            <p className="text-xs">
                              Avg. Time: {field.averageTime}s
                            </p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  ))}
                </div>
              </motion.div>
            ),
          )}
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4 border-t pt-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-500">
              {heatmapData.fields.filter((f) => f.completionRate >= 90).length}
            </p>
            <p className="text-xs text-muted-foreground">High Completion</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-500">
              {
                heatmapData.fields.filter(
                  (f) => f.completionRate >= 50 && f.completionRate < 90,
                ).length
              }
            </p>
            <p className="text-xs text-muted-foreground">Medium Completion</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-500">
              {heatmapData.fields.filter((f) => f.completionRate < 50).length}
            </p>
            <p className="text-xs text-muted-foreground">Low Completion</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
