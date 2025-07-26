"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, CheckCircle, Info, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ValidationError {
  field: string;
  message: string;
  suggestion?: string;
}

interface ValidationFeedbackProps {
  errors?: ValidationError[];
  isValidating?: boolean;
  className?: string;
  // eslint-disable-next-line no-unused-vars
  onHelpRequest?: (field: string) => void;
}

export function ValidationFeedback({
  errors = [],
  isValidating = false,
  className,
  onHelpRequest,
}: ValidationFeedbackProps) {
  const [expandedErrors, setExpandedErrors] = React.useState<Set<string>>(
    new Set(),
  );

  const toggleError = (field: string) => {
    const newExpanded = new Set(expandedErrors);
    if (newExpanded.has(field)) {
      newExpanded.delete(field);
    } else {
      newExpanded.add(field);
    }
    setExpandedErrors(newExpanded);
  };

  if (!isValidating && errors.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      <AnimatePresence mode="wait">
        {isValidating && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-600 dark:bg-blue-950/50 dark:text-blue-400"
          >
            <Info className="h-4 w-4" />
            <span>Validating form data...</span>
          </motion.div>
        )}

        {!isValidating && errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center gap-2 text-sm font-medium text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>Please fix the following errors:</span>
            </div>

            <div className="space-y-2">
              {errors.map((error, index) => (
                <motion.div
                  key={error.field}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="rounded-lg border border-destructive/20 bg-destructive/5 p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {error.field}
                        </span>
                        {error.suggestion && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-auto p-0 text-xs"
                            onClick={() => toggleError(error.field)}
                          >
                            {expandedErrors.has(error.field)
                              ? "Hide help"
                              : "Show help"}
                          </Button>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {error.message}
                      </p>

                      <AnimatePresence>
                        {expandedErrors.has(error.field) &&
                          error.suggestion && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              className="mt-2 rounded-md bg-background/50 p-2"
                            >
                              <div className="flex items-start gap-2">
                                <HelpCircle className="mt-0.5 h-4 w-4 text-primary" />
                                <p className="text-sm">{error.suggestion}</p>
                              </div>
                            </motion.div>
                          )}
                      </AnimatePresence>
                    </div>

                    {onHelpRequest && (
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 flex-shrink-0"
                        onClick={() => onHelpRequest(error.field)}
                      >
                        <HelpCircle className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {!isValidating && errors.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-600 dark:bg-green-950/50 dark:text-green-400"
          >
            <CheckCircle className="h-4 w-4" />
            <span>All fields are valid!</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
