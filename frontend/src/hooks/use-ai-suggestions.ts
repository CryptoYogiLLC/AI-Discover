import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import toast from "react-hot-toast";

interface Suggestion {
  field: string;
  value: string;
  confidence: number;
  reasoning?: string;
}

interface UseAISuggestionsOptions {
  projectId: string;
  formType: string;
  enabled?: boolean;
}

export function useAISuggestions({
  projectId,
  formType,
  enabled = true,
}: UseAISuggestionsOptions) {
  const [suggestions, setSuggestions] = useState<Record<string, Suggestion>>(
    {},
  );

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["ai-suggestions", projectId, formType],
    queryFn: async () => {
      const response = await axios.get(
        `/api/v1/ai-assistance/suggestions/${projectId}`,
        {
          params: { form_type: formType },
        },
      );
      return response.data;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const acceptSuggestion = useMutation({
    mutationFn: async ({ field, value }: { field: string; value: string }) => {
      const response = await axios.post(
        `/api/v1/ai-assistance/suggestions/accept`,
        {
          project_id: projectId,
          field,
          value,
        },
      );
      return response.data;
    },
    onSuccess: () => {
      toast.success("Suggestion accepted");
    },
    onError: () => {
      toast.error("Failed to accept suggestion");
    },
  });

  const rejectSuggestion = useMutation({
    mutationFn: async ({ field }: { field: string }) => {
      const response = await axios.post(
        `/api/v1/ai-assistance/suggestions/reject`,
        {
          project_id: projectId,
          field,
        },
      );
      return response.data;
    },
    onSuccess: () => {
      toast.success("Suggestion rejected");
    },
    onError: () => {
      toast.error("Failed to reject suggestion");
    },
  });

  useEffect(() => {
    if (data?.suggestions) {
      const suggestionsMap = data.suggestions.reduce(
        (acc: Record<string, Suggestion>, suggestion: Suggestion) => {
          acc[suggestion.field] = suggestion;
          return acc;
        },
        {},
      );
      setSuggestions(suggestionsMap);
    }
  }, [data]);

  return {
    suggestions,
    isLoading,
    error,
    refetch,
    acceptSuggestion: acceptSuggestion.mutate,
    rejectSuggestion: rejectSuggestion.mutate,
  };
}
