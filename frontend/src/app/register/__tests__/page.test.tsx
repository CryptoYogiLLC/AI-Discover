import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RegisterPage from "../page";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import toast from "react-hot-toast";

// Mock dependencies
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

jest.mock("@/store/auth");

jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock framer-motion
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
}));

// Mock fetch
global.fetch = jest.fn();

describe("RegisterPage", () => {
  const mockPush = jest.fn();
  const mockLogin = jest.fn();
  const mockUseAuthStore = useAuthStore as unknown as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    mockUseAuthStore.mockReturnValue({ login: mockLogin });
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "test-token" }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders registration form with all required fields", () => {
    render(<RegisterPage />);

    expect(screen.getByText("Create an account")).toBeInTheDocument();
    expect(
      screen.getByText("Join AI-Discover to start your journey"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Full Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Already have an account?")).toBeInTheDocument();
  });

  it("validates name length", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    // Try to submit with short name
    await user.type(nameInput, "J");
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("Name must be at least 2 characters"),
      ).toBeInTheDocument();
    });
  });

  it("validates email format", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const emailInput = screen.getByLabelText("Email");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    // Try to submit with invalid email
    await user.type(emailInput, "invalidemail");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Invalid email address")).toBeInTheDocument();
    });
  });

  it("validates password requirements", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const passwordInput = screen.getByLabelText("Password");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    // Test various invalid passwords
    await user.type(passwordInput, "short");
    await user.click(submitButton);
    await waitFor(() => {
      expect(
        screen.getByText("Password must be at least 8 characters"),
      ).toBeInTheDocument();
    });

    await user.clear(passwordInput);
    await user.type(passwordInput, "alllowercase");
    await user.click(submitButton);
    await waitFor(() => {
      expect(
        screen.getByText("Password must contain at least one uppercase letter"),
      ).toBeInTheDocument();
    });

    await user.clear(passwordInput);
    await user.type(passwordInput, "ALLUPPERCASE");
    await user.click(submitButton);
    await waitFor(() => {
      expect(
        screen.getByText("Password must contain at least one lowercase letter"),
      ).toBeInTheDocument();
    });

    await user.clear(passwordInput);
    await user.type(passwordInput, "NoNumbers");
    await user.click(submitButton);
    await waitFor(() => {
      expect(
        screen.getByText("Password must contain at least one number"),
      ).toBeInTheDocument();
    });
  });

  it("validates password confirmation match", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    await user.type(nameInput, "John Doe");
    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "Password123");
    await user.type(confirmPasswordInput, "Password456");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Passwords don't match")).toBeInTheDocument();
    });
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");
    const togglePasswordButton = screen.getByRole("button", {
      name: /show password/i,
    });
    const toggleConfirmButton = screen.getByRole("button", {
      name: /show confirm password/i,
    });

    // Test password field
    expect(passwordInput).toHaveAttribute("type", "password");
    await user.click(togglePasswordButton);
    expect(passwordInput).toHaveAttribute("type", "text");
    expect(
      screen.getByRole("button", { name: /hide password/i }),
    ).toBeInTheDocument();

    // Test confirm password field
    expect(confirmPasswordInput).toHaveAttribute("type", "password");
    await user.click(toggleConfirmButton);
    expect(confirmPasswordInput).toHaveAttribute("type", "text");
    expect(
      screen.getByRole("button", { name: /hide confirm password/i }),
    ).toBeInTheDocument();
  });

  it("handles successful registration", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    await user.type(nameInput, "John Doe");
    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "Password123");
    await user.type(confirmPasswordInput, "Password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/auth/register"),
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: "John Doe",
            email: "test@example.com",
            password: "Password123", // pragma: allowlist secret
          }),
          credentials: "include",
        }),
      );
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "1",
          email: "test@example.com",
          name: "John Doe",
          role: "user",
        }),
        "test-token",
      );
      expect(toast.success).toHaveBeenCalledWith(
        "Account created successfully!",
      );
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("handles registration failure with error message", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Email already exists" }),
    });

    const user = userEvent.setup();
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    await user.type(nameInput, "John Doe");
    await user.type(emailInput, "existing@example.com");
    await user.type(passwordInput, "Password123");
    await user.type(confirmPasswordInput, "Password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Email already exists");
      expect(mockLogin).not.toHaveBeenCalled();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it("shows loading state during submission", async () => {
    // Mock a slow API response
    (global.fetch as jest.Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ access_token: "test-token" }),
              }),
            100,
          ),
        ),
    );

    const user = userEvent.setup();
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");
    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });

    await user.type(nameInput, "John Doe");
    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "Password123");
    await user.type(confirmPasswordInput, "Password123");
    await user.click(submitButton);

    // Check loading state
    expect(screen.getByText("Creating account...")).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveAttribute("aria-busy", "true");

    // Wait for completion
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /create account/i }),
      ).not.toBeDisabled();
    });
  });

  it("has accessible form fields with proper ARIA attributes", () => {
    render(<RegisterPage />);

    const nameInput = screen.getByLabelText("Full Name");
    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");
    const confirmPasswordInput = screen.getByLabelText("Confirm Password");

    expect(nameInput).toHaveAttribute("type", "text");
    expect(nameInput).toHaveAttribute("autoComplete", "name");
    expect(nameInput).toHaveAttribute("aria-label", "Full name");

    expect(emailInput).toHaveAttribute("type", "email");
    expect(emailInput).toHaveAttribute("autoComplete", "email");
    expect(emailInput).toHaveAttribute("aria-label", "Email address");

    expect(passwordInput).toHaveAttribute("type", "password");
    expect(passwordInput).toHaveAttribute("autoComplete", "new-password");
    expect(passwordInput).toHaveAttribute("aria-label", "Password");

    expect(confirmPasswordInput).toHaveAttribute("type", "password");
    expect(confirmPasswordInput).toHaveAttribute(
      "autoComplete",
      "new-password",
    );
    expect(confirmPasswordInput).toHaveAttribute(
      "aria-label",
      "Confirm password",
    );
  });

  it("displays password requirements help text", () => {
    render(<RegisterPage />);

    expect(
      screen.getByText(
        "Must be at least 8 characters with uppercase, lowercase, and numbers",
      ),
    ).toBeInTheDocument();
  });

  it("navigates to login page when sign in link is clicked", () => {
    render(<RegisterPage />);

    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toHaveAttribute("href", "/login");
  });
});
