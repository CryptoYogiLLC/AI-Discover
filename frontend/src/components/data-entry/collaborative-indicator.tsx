"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Users, Circle, Eye } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Collaborator {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  color: string;
  isOnline: boolean;
  currentField?: string;
  lastActive?: Date;
}

interface CollaborativeIndicatorProps {
  collaborators: Collaborator[];
  currentUserId?: string;
  className?: string;
  showFieldIndicators?: boolean;
}

export function CollaborativeIndicator({
  collaborators,
  currentUserId,
  className,
  showFieldIndicators = true,
}: CollaborativeIndicatorProps) {
  const [expandedView, setExpandedView] = React.useState(false);

  const onlineCollaborators = collaborators.filter((c) => c.isOnline);
  const offlineCollaborators = collaborators.filter((c) => !c.isOnline);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getTimeAgo = (date?: Date) => {
    if (!date) return "Unknown";
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  };

  return (
    <div className={cn("relative", className)}>
      {/* Compact View */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setExpandedView(!expandedView)}
          className="flex items-center gap-2 rounded-lg px-3 py-2 transition-colors hover:bg-accent"
        >
          <Users className="h-4 w-4" />
          <span className="text-sm font-medium">
            {onlineCollaborators.length} active
          </span>
          {onlineCollaborators.length > 0 && (
            <div className="flex -space-x-2">
              {onlineCollaborators.slice(0, 3).map((collaborator) => (
                <TooltipProvider key={collaborator.id}>
                  <Tooltip>
                    <TooltipTrigger>
                      <div
                        className="relative h-6 w-6 rounded-full border-2 border-background"
                        style={{ backgroundColor: collaborator.color }}
                      >
                        <span className="flex h-full w-full items-center justify-center text-xs font-medium text-white">
                          {getInitials(collaborator.name)}
                        </span>
                        <Circle className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 fill-green-500 text-green-500" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{collaborator.name}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
              {onlineCollaborators.length > 3 && (
                <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-background bg-muted text-xs font-medium">
                  +{onlineCollaborators.length - 3}
                </div>
              )}
            </div>
          )}
        </button>

        {showFieldIndicators && (
          <div className="hidden items-center gap-2 text-sm text-muted-foreground sm:flex">
            <Eye className="h-3 w-3" />
            <span>Live collaboration</span>
          </div>
        )}
      </div>

      {/* Expanded View */}
      <AnimatePresence>
        {expandedView && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-background p-4 shadow-lg"
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-medium">Collaborators</h3>
              <Badge variant="outline">{collaborators.length} total</Badge>
            </div>

            {/* Online Collaborators */}
            {onlineCollaborators.length > 0 && (
              <div className="mb-4">
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  ONLINE NOW
                </p>
                <div className="space-y-2">
                  {onlineCollaborators.map((collaborator) => (
                    <motion.div
                      key={collaborator.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between rounded-md p-2 hover:bg-accent"
                    >
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div
                            className="h-8 w-8 rounded-full"
                            style={{ backgroundColor: collaborator.color }}
                          >
                            <span className="flex h-full w-full items-center justify-center text-sm font-medium text-white">
                              {getInitials(collaborator.name)}
                            </span>
                          </div>
                          <Circle className="absolute -bottom-0.5 -right-0.5 h-3 w-3 fill-green-500 text-green-500" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">
                            {collaborator.name}
                            {collaborator.id === currentUserId && " (You)"}
                          </p>
                          {collaborator.currentField && (
                            <p className="text-xs text-muted-foreground">
                              Editing: {collaborator.currentField}
                            </p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Offline Collaborators */}
            {offlineCollaborators.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  OFFLINE
                </p>
                <div className="space-y-2">
                  {offlineCollaborators.map((collaborator) => (
                    <motion.div
                      key={collaborator.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between rounded-md p-2 opacity-60"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="h-8 w-8 rounded-full"
                          style={{ backgroundColor: collaborator.color }}
                        >
                          <span className="flex h-full w-full items-center justify-center text-sm font-medium text-white">
                            {getInitials(collaborator.name)}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm">{collaborator.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Last seen: {getTimeAgo(collaborator.lastActive)}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
