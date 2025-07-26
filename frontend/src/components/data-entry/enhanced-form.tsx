"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, History, Users, Save, Send } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { FormFieldSuggestion } from "@/components/ai-assistance/form-field-suggestion";
import { ValidationFeedback } from "@/components/ai-assistance/validation-feedback";
import { cn } from "@/lib/utils";

interface FormField {
  name: string;
  label: string;
  type: "text" | "email" | "number" | "date";
  required?: boolean;
  placeholder?: string;
  validation?: z.ZodType<unknown>;
}

interface EnhancedFormProps {
  fields: FormField[];
  // eslint-disable-next-line no-unused-vars
  onSubmit: (data: Record<string, unknown>) => void;
  // eslint-disable-next-line no-unused-vars
  onSaveDraft?: (data: Record<string, unknown>) => void;
  aiSuggestions?: Record<string, { value: string; confidence: number }>;
  isLoading?: boolean;
  className?: string;
}

export function EnhancedForm({
  fields,
  onSubmit,
  onSaveDraft,
  aiSuggestions = {},
  isLoading = false,
  className,
}: EnhancedFormProps) {
  const [completedFields, setCompletedFields] = React.useState<Set<string>>(
    new Set(),
  );
  const [showHistory, setShowHistory] = React.useState<string | null>(null);
  const [activeCollaborators] = React.useState(2);
  const [validationErrors, setValidationErrors] = React.useState<
    Array<{ field: string; message: string; suggestion?: string }>
  >([]);

  // Create dynamic schema based on fields
  const schema = z.object(
    fields.reduce(
      (acc, field) => {
        if (field.validation) {
          acc[field.name] = field.validation;
        } else if (field.required) {
          acc[field.name] = z.string().min(1, `${field.label} is required`);
        } else {
          acc[field.name] = z.string().optional();
        }
        return acc;
      },
      {} as Record<string, z.ZodType<unknown>>,
    ),
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    resolver: zodResolver(schema),
  });

  const formValues = watch();

  React.useEffect(() => {
    const completed = new Set<string>();
    fields.forEach((field) => {
      if (formValues[field.name]) {
        completed.add(field.name);
      }
    });
    setCompletedFields(completed);
  }, [formValues, fields]);

  const completionPercentage = Math.round(
    (completedFields.size / fields.length) * 100,
  );

  const handleAISuggestionAccept = (fieldName: string, value: string) => {
    setValue(fieldName, value);
  };

  const handleFormSubmit = (data: Record<string, unknown>) => {
    setValidationErrors([]);
    onSubmit(data);
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle>Enhanced Data Entry</CardTitle>
            <Badge variant="outline" className="gap-1">
              <Sparkles className="h-3 w-3" />
              AI-Powered
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            {activeCollaborators > 0 && (
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {activeCollaborators} editing
                </span>
              </div>
            )}
            <div className="text-right">
              <p className="text-sm font-medium">{completionPercentage}%</p>
              <Progress value={completionPercentage} className="h-2 w-24" />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {fields.map((field, index) => (
            <motion.div
              key={field.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="space-y-2"
            >
              <div className="flex items-center justify-between">
                <Label htmlFor={field.name}>
                  {field.label}
                  {field.required && (
                    <span className="ml-1 text-destructive">*</span>
                  )}
                </Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 px-2"
                  onClick={() =>
                    setShowHistory(
                      showHistory === field.name ? null : field.name,
                    )
                  }
                >
                  <History className="h-3 w-3" />
                </Button>
              </div>

              <div className="relative">
                <Input
                  id={field.name}
                  type={field.type}
                  placeholder={field.placeholder}
                  {...register(field.name)}
                  className={cn(
                    errors[field.name] && "border-destructive",
                    completedFields.has(field.name) &&
                      "border-green-500 focus:ring-green-500",
                  )}
                />
                {completedFields.has(field.name) && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                  >
                    <div className="h-5 w-5 rounded-full bg-green-500 p-1">
                      <svg
                        className="h-3 w-3 text-white"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="3"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </motion.div>
                )}
              </div>

              {errors[field.name] && (
                <p className="text-sm text-destructive">
                  {errors[field.name]?.message as string}
                </p>
              )}

              {/* AI Suggestion */}
              {aiSuggestions[field.name] && (
                <FormFieldSuggestion
                  fieldName={field.label}
                  suggestion={aiSuggestions[field.name].value}
                  confidence={aiSuggestions[field.name].confidence}
                  onAccept={(value) =>
                    handleAISuggestionAccept(field.name, value)
                  }
                />
              )}

              {/* Field History */}
              <AnimatePresence>
                {showHistory === field.name && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden rounded-md border bg-muted/50 p-3"
                  >
                    <p className="mb-2 text-sm font-medium">Recent values:</p>
                    <div className="space-y-1">
                      {["Previous value 1", "Previous value 2"].map(
                        (value, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setValue(field.name, value)}
                            className="block w-full rounded px-2 py-1 text-left text-sm hover:bg-background"
                          >
                            {value}
                          </button>
                        ),
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}

          {/* Validation Feedback */}
          {validationErrors.length > 0 && (
            <ValidationFeedback errors={validationErrors} />
          )}

          {/* Form Actions */}
          <div className="flex gap-3 pt-4">
            <Button type="submit" disabled={isLoading}>
              <Send className="mr-2 h-4 w-4" />
              Submit
            </Button>
            {onSaveDraft && (
              <Button
                type="button"
                variant="outline"
                onClick={() => onSaveDraft(formValues)}
                disabled={isLoading}
              >
                <Save className="mr-2 h-4 w-4" />
                Save Draft
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
