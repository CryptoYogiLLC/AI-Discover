import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthLayout } from "../auth-layout";
import { useAuthStore } from "@/store/auth";
import { useRouter, usePathname } from "next/navigation";

// Mock dependencies
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

jest.mock("@/store/auth");

// Mock the Navigation component
jest.mock("@/components/navigation", () => ({
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

describe("AuthLayout", () => {
  const mockPush = jest.fn();
  const mockUseAuthStore = useAuthStore as unknown as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  });

  describe("when loading", () => {
    it("renders nothing while checking auth status", () => {
      (usePathname as jest.Mock).mockReturnValue("/dashboard");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      });

      const { container } = render(
        <AuthLayout>
          <div>Test Content</div>
        </AuthLayout>,
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe("public routes", () => {
    const publicRoutes = ["/login", "/register", "/forgot-password"];

    publicRoutes.forEach((route) => {
      it(`renders content without navigation on ${route}`, () => {
        (usePathname as jest.Mock).mockReturnValue(route);
        mockUseAuthStore.mockReturnValue({
          isAuthenticated: false,
          isLoading: false,
        });

        render(
          <AuthLayout>
            <div data-testid="test-content">Test Content</div>
          </AuthLayout>,
        );

        expect(screen.getByTestId("test-content")).toBeInTheDocument();
        expect(screen.queryByTestId("navigation")).not.toBeInTheDocument();
      });
    });

    it("redirects authenticated users to dashboard when visiting public routes", async () => {
      (usePathname as jest.Mock).mockReturnValue("/login");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      render(
        <AuthLayout>
          <div>Login Page</div>
        </AuthLayout>,
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith("/dashboard");
      });
    });
  });

  describe("protected routes", () => {
    it("renders content with navigation for authenticated users", () => {
      (usePathname as jest.Mock).mockReturnValue("/dashboard");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      render(
        <AuthLayout>
          <div data-testid="test-content">Dashboard Content</div>
        </AuthLayout>,
      );

      expect(screen.getByTestId("navigation")).toBeInTheDocument();
      expect(screen.getByTestId("test-content")).toBeInTheDocument();
      expect(screen.getByRole("main")).toBeInTheDocument();
    });

    it("redirects unauthenticated users to login when visiting protected routes", async () => {
      (usePathname as jest.Mock).mockReturnValue("/dashboard");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      });

      render(
        <AuthLayout>
          <div>Dashboard Content</div>
        </AuthLayout>,
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith("/login");
      });
    });

    it("applies correct layout structure for authenticated routes", () => {
      (usePathname as jest.Mock).mockReturnValue("/settings");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      render(
        <AuthLayout>
          <div data-testid="test-content">Settings Content</div>
        </AuthLayout>,
      );

      const main = screen.getByRole("main");
      expect(main).toHaveAttribute("id", "main-content");
      expect(main).toHaveClass("py-6");

      const contentWrapper = main.firstChild;
      expect(contentWrapper).toHaveClass(
        "max-w-7xl",
        "mx-auto",
        "px-4",
        "sm:px-6",
        "lg:px-8",
      );
    });

    it("renders nothing for unauthenticated users on protected routes (fallback)", () => {
      (usePathname as jest.Mock).mockReturnValue("/projects");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      });

      const { container } = render(
        <AuthLayout>
          <div>Projects Content</div>
        </AuthLayout>,
      );

      // The component should return null (redirect happens in useEffect)
      expect(container.firstChild).toBeNull();
    });
  });

  describe("route transitions", () => {
    it("handles authentication state changes correctly", async () => {
      const { rerender } = render(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      // Start as unauthenticated on protected route
      (usePathname as jest.Mock).mockReturnValue("/dashboard");
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      });

      rerender(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith("/login");
      });

      // Change to authenticated
      jest.clearAllMocks();
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      rerender(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      expect(screen.getByTestId("navigation")).toBeInTheDocument();
      expect(screen.getByTestId("test-content")).toBeInTheDocument();
    });

    it("does not redirect when route changes but auth status remains the same", () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      const { rerender } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>,
      );

      // Change from one protected route to another
      (usePathname as jest.Mock).mockReturnValue("/dashboard");
      rerender(
        <AuthLayout>
          <div>Dashboard</div>
        </AuthLayout>,
      );

      jest.clearAllMocks();

      (usePathname as jest.Mock).mockReturnValue("/settings");
      rerender(
        <AuthLayout>
          <div>Settings</div>
        </AuthLayout>,
      );

      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe("edge cases", () => {
    it("handles undefined pathname gracefully", () => {
      (usePathname as jest.Mock).mockReturnValue(undefined);
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      });

      render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>,
      );

      // Should redirect to login for undefined routes
      expect(mockPush).toHaveBeenCalledWith("/login");
    });

    it("renders correctly when switching from loading to authenticated", () => {
      (usePathname as jest.Mock).mockReturnValue("/dashboard");

      const { rerender } = render(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      // Start loading
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      });

      rerender(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      expect(screen.queryByTestId("test-content")).not.toBeInTheDocument();

      // Finish loading as authenticated
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      });

      rerender(
        <AuthLayout>
          <div data-testid="test-content">Content</div>
        </AuthLayout>,
      );

      expect(screen.getByTestId("test-content")).toBeInTheDocument();
      expect(screen.getByTestId("navigation")).toBeInTheDocument();
    });
  });
});
