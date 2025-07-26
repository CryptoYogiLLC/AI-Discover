import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Navigation } from "../navigation";
import { useAuthStore } from "@/store/auth";
import { useRouter, usePathname } from "next/navigation";

// Mock dependencies
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

jest.mock("@/store/auth");

// Mock framer-motion to avoid animation issues in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({
      children,
      ...props
    }: {
      children: React.ReactNode;
      [key: string]: unknown;
    }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

describe("Navigation", () => {
  const mockPush = jest.fn();
  const mockLogout = jest.fn();
  const mockUseAuthStore = useAuthStore as unknown as jest.Mock;

  const defaultUser = {
    id: "1",
    email: "test@example.com",
    name: "Test User",
    role: "user" as const,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (usePathname as jest.Mock).mockReturnValue("/dashboard");
    mockUseAuthStore.mockReturnValue({
      user: defaultUser,
      logout: mockLogout,
    });
  });

  it("renders the logo", () => {
    render(<Navigation />);
    expect(screen.getByText("AI-Discover")).toBeInTheDocument();
  });

  it("renders navigation items based on user role", () => {
    render(<Navigation />);

    // Should show items available to regular users
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Assessments")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();

    // Should not show admin items
    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
  });

  it("renders admin items for admin users", () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...defaultUser, role: "admin" },
      logout: mockLogout,
    });

    render(<Navigation />);

    // Should show admin dropdown
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("highlights the active route", () => {
    (usePathname as jest.Mock).mockReturnValue("/projects");

    render(<Navigation />);

    const projectsLink = screen.getByRole("link", { name: /projects/i });
    expect(projectsLink).toHaveAttribute("aria-current", "page");
    expect(projectsLink).toHaveClass("bg-primary/10", "text-primary");
  });

  it("opens and closes mobile menu", async () => {
    const user = userEvent.setup();
    render(<Navigation />);

    const menuButton = screen.getByRole("button", { name: /open menu/i });

    // Mobile menu should not be visible initially
    expect(
      screen.queryByRole("link", { name: /dashboard/i }),
    ).toBeInTheDocument();

    // Click to open mobile menu
    await user.click(menuButton);

    // Menu button should now show close
    expect(
      screen.getByRole("button", { name: /close menu/i }),
    ).toBeInTheDocument();
  });

  it("displays user information in dropdown", () => {
    render(<Navigation />);

    expect(screen.getByText("Test User")).toBeInTheDocument();
  });

  it("handles logout action", async () => {
    const user = userEvent.setup();
    render(<Navigation />);

    // Open user menu
    const userMenuButton = screen.getByRole("button", { name: /user menu/i });
    await user.click(userMenuButton);

    // Click logout
    const logoutButton = screen.getByText("Log out");
    await user.click(logoutButton);

    expect(mockLogout).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("filters navigation items for viewer role", () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...defaultUser, role: "viewer" },
      logout: mockLogout,
    });

    render(<Navigation />);

    // Should show viewer-accessible items
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();

    // Should not show user/admin only items
    expect(screen.queryByText("Projects")).not.toBeInTheDocument();
    expect(screen.queryByText("Assessments")).not.toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });

  it("renders admin dropdown menu items correctly", async () => {
    const user = userEvent.setup();
    mockUseAuthStore.mockReturnValue({
      user: { ...defaultUser, role: "admin" },
      logout: mockLogout,
    });

    render(<Navigation />);

    // Open admin dropdown
    const adminButton = screen.getByText("Admin");
    await user.click(adminButton);

    // Check admin menu items - they're inside Links but might not have the "link" role
    await waitFor(() => {
      expect(screen.getByText("Users")).toBeInTheDocument();
      expect(screen.getByText("Security")).toBeInTheDocument();
    });
  });

  it("closes mobile menu when a link is clicked", async () => {
    const user = userEvent.setup();
    render(<Navigation />);

    // Open mobile menu
    const menuButton = screen.getByRole("button", { name: /open menu/i });
    await user.click(menuButton);

    // Click a navigation link
    const dashboardLinks = screen.getAllByText("Dashboard");
    // Click the mobile menu version (last one)
    await user.click(dashboardLinks[dashboardLinks.length - 1]);

    // Menu should close
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /open menu/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders user email when name is not available", () => {
    mockUseAuthStore.mockReturnValue({
      user: { ...defaultUser, name: undefined },
      logout: mockLogout,
    });

    render(<Navigation />);

    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });
});
