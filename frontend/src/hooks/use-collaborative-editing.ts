import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";

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

interface FieldUpdate {
  field: string;
  value: string;
  userId: string;
  timestamp: Date;
}

interface UseCollaborativeEditingOptions {
  projectId: string;
  userId: string;
  // eslint-disable-next-line no-unused-vars
  onFieldUpdate?: (update: FieldUpdate) => void;
}

export function useCollaborativeEditing({
  projectId,
  userId,
  onFieldUpdate,
}: UseCollaborativeEditingOptions) {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [fieldLocks, setFieldLocks] = useState<Record<string, string>>({});

  // Fetch active collaborators
  const { data: collaboratorsData, refetch: refetchCollaborators } = useQuery({
    queryKey: ["collaborators", projectId],
    queryFn: async () => {
      const response = await axios.get(
        `/api/v1/data-entry/collaborators/${projectId}`,
      );
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Lock field when user starts editing
  const lockField = useMutation({
    mutationFn: async (field: string) => {
      const response = await axios.post("/api/v1/data-entry/lock-field", {
        project_id: projectId,
        field,
        user_id: userId,
      });
      return response.data;
    },
    onSuccess: (data, field) => {
      setFieldLocks((prev) => ({ ...prev, [field]: userId }));
    },
  });

  // Unlock field when user stops editing
  const unlockField = useMutation({
    mutationFn: async (field: string) => {
      const response = await axios.post("/api/v1/data-entry/unlock-field", {
        project_id: projectId,
        field,
        user_id: userId,
      });
      return response.data;
    },
    onSuccess: (data, field) => {
      setFieldLocks((prev) => {
        const newLocks = { ...prev };
        delete newLocks[field];
        return newLocks;
      });
    },
  });

  // Broadcast field update
  const broadcastUpdate = useMutation({
    mutationFn: async (update: Omit<FieldUpdate, "userId" | "timestamp">) => {
      const response = await axios.post("/api/v1/data-entry/broadcast", {
        project_id: projectId,
        ...update,
        user_id: userId,
      });
      return response.data;
    },
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/collaborate/${projectId}`,
    );

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "join", userId, projectId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "collaborator-joined":
        case "collaborator-left":
          refetchCollaborators();
          break;

        case "field-locked":
          setFieldLocks((prev) => ({ ...prev, [data.field]: data.userId }));
          break;

        case "field-unlocked":
          setFieldLocks((prev) => {
            const newLocks = { ...prev };
            delete newLocks[data.field];
            return newLocks;
          });
          break;

        case "field-updated":
          if (onFieldUpdate && data.userId !== userId) {
            onFieldUpdate({
              field: data.field,
              value: data.value,
              userId: data.userId,
              timestamp: new Date(data.timestamp),
            });
          }
          break;
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      ws.send(JSON.stringify({ type: "leave", userId, projectId }));
      ws.close();
    };
  }, [projectId, userId, onFieldUpdate, refetchCollaborators]);

  useEffect(() => {
    if (collaboratorsData) {
      setCollaborators(collaboratorsData.collaborators);
    }
  }, [collaboratorsData]);

  const isFieldLocked = useCallback(
    (field: string) => {
      return fieldLocks[field] && fieldLocks[field] !== userId;
    },
    [fieldLocks, userId],
  );

  const getFieldOwner = useCallback(
    (field: string) => {
      const ownerId = fieldLocks[field];
      if (!ownerId) return null;
      return collaborators.find((c) => c.id === ownerId);
    },
    [fieldLocks, collaborators],
  );

  return {
    collaborators,
    fieldLocks,
    lockField: lockField.mutate,
    unlockField: unlockField.mutate,
    broadcastUpdate: broadcastUpdate.mutate,
    isFieldLocked,
    getFieldOwner,
  };
}
