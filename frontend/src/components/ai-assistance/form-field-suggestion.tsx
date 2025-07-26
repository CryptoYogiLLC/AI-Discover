"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Check, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface FormFieldSuggestionProps {
  fieldName: string;
  suggestion?: string;
  confidence?: number;
  isLoading?: boolean;
  // eslint-disable-next-line no-unused-vars
  onAccept?: (value: string) => void;
  onReject?: () => void;
  className?: string;
}

export function FormFieldSuggestion({
  fieldName,
  suggestion,
  confidence = 0,
  isLoading = false,
  onAccept,
  onReject,
  className,
}: FormFieldSuggestionProps) {
  const [isAccepted, setIsAccepted] = React.useState(false);
  const [isRejected, setIsRejected] = React.useState(false);

  const handleAccept = () => {
    if (suggestion && onAccept) {
      setIsAccepted(true);
      onAccept(suggestion);
      setTimeout(() => setIsAccepted(false), 2000);
    }
  };

  const handleReject = () => {
    setIsRejected(true);
    if (onReject) onReject();
    setTimeout(() => setIsRejected(false), 2000);
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return "success";
    if (conf >= 0.6) return "warning";
    return "secondary";
  };

  return (
    <AnimatePresence mode="wait">
      {(isLoading || suggestion) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "relative rounded-lg border bg-gradient-to-r from-primary/5 to-primary/10 p-3",
            className,
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">AI Suggestion</span>
                {confidence > 0 && !isLoading && (
                  <Badge variant={getConfidenceColor(confidence)}>
                    {Math.round(confidence * 100)}% confidence
                  </Badge>
                )}
              </div>

              {isLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Generating suggestion...</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    For <span className="font-medium">{fieldName}</span>:
                  </p>
                  <div className="rounded-md bg-background/50 p-2">
                    <code className="text-sm">{suggestion}</code>
                  </div>
                </div>
              )}
            </div>

            {!isLoading && suggestion && (
              <div className="flex gap-1">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8"
                        onClick={handleAccept}
                        disabled={isAccepted || isRejected}
                      >
                        {isAccepted ? (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 500 }}
                          >
                            <Check className="h-4 w-4 text-green-500" />
                          </motion.div>
                        ) : (
                          <Check className="h-4 w-4" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Accept suggestion</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8"
                        onClick={handleReject}
                        disabled={isAccepted || isRejected}
                      >
                        {isRejected ? (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 500 }}
                          >
                            <X className="h-4 w-4 text-red-500" />
                          </motion.div>
                        ) : (
                          <X className="h-4 w-4" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Reject suggestion</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            )}
          </div>

          {/* Animated feedback */}
          <AnimatePresence>
            {(isAccepted || isRejected) && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className={cn(
                  "absolute inset-0 flex items-center justify-center rounded-lg",
                  isAccepted ? "bg-green-500/10" : "bg-red-500/10",
                )}
              >
                <span
                  className={cn(
                    "font-medium",
                    isAccepted ? "text-green-600" : "text-red-600",
                  )}
                >
                  {isAccepted ? "Accepted!" : "Rejected"}
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
