import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// Create a custom render function that includes providers
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => {
  const user = userEvent.setup();

  return {
    user,
    ...render(ui, { wrapper: AllTheProviders, ...options }),
  };
};

// Re-export everything
export * from "@testing-library/react";
export { customRender as render, createTestQueryClient };

// Test data generators
export const generateMockUser = (overrides = {}) => ({
  id: "test-user-id",
  email: "test@example.com",
  username: "testuser",
  full_name: "Test User",
  is_active: true,
  is_superuser: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

export const generateMockDiscovery = (overrides = {}) => ({
  id: "discovery-123",
  name: "Test Discovery",
  description: "Test discovery description",
  status: "pending",
  target_platform: "aws",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

export const generateMockApplication = (overrides = {}) => ({
  id: "app-123",
  name: "Test Application",
  type: "web",
  runtime: "python3.9",
  framework: "fastapi",
  resources: {
    cpu: "2 vCPU",
    memory: "4 GB",
    storage: "20 GB",
  },
  recommendation: "rehost",
  confidence: 0.85,
  ...overrides,
});

// Mock API responses
export const mockApiResponse = <T,>(data: T, delay = 0) => {
  return new Promise<{ data: T }>((resolve) => {
    setTimeout(() => {
      resolve({ data });
    }, delay);
  });
};

export const mockApiError = (message: string, status = 400, delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject({
        response: {
          status,
          data: {
            detail: message,
          },
        },
      });
    }, delay);
  });
};

// Custom matchers
export const expectToBeInDocument = (element: HTMLElement) => {
  // eslint-disable-next-line no-undef
  expect(document.body).toContainElement(element);
};

// Form helpers
export const fillForm = async (
  user: ReturnType<typeof userEvent.setup>,
  formData: Record<string, string>,
) => {
  for (const [name, value] of Object.entries(formData)) {
    const input = document.querySelector(`[name="${name}"]`) as HTMLElement;
    if (input) {
      await user.clear(input);
      await user.type(input, value);
    }
  }
};

// Wait helpers
export const waitForLoadingToFinish = async () => {
  const { waitFor } = await import("@testing-library/react");
  await waitFor(() => {
    const loadingElements = document.querySelectorAll(
      '[data-testid="loading"]',
    );
    // eslint-disable-next-line no-undef
    expect(loadingElements).toHaveLength(0);
  });
};
