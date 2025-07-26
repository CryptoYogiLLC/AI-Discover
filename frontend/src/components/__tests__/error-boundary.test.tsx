import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary } from "../error-boundary";

// Mock console.error to prevent error logs in tests
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error message");
  }
  return <div>No error content</div>;
};

// Custom error fallback component
const CustomErrorFallback = ({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) => {
  return (
    <div>
      <h1>Custom Error</h1>
      <p>{error.message}</p>
      <button onClick={reset}>Custom Reset</button>
    </div>
  );
};

describe("ErrorBoundary", () => {
  it("renders children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div data-testid="child-content">Child content</div>
      </ErrorBoundary>,
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("renders default error fallback when an error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(
      screen.getByText(
        "An unexpected error occurred. Please try again or contact support if the problem persists.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();
  });

  it("displays error details in collapsible section", async () => {
    const user = userEvent.setup();

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Error details should be in a details element
    const detailsElement = screen.getByText("Error details");
    expect(detailsElement.tagName).toBe("SUMMARY");

    // Click to expand error details
    await user.click(detailsElement);

    // Should show the error message
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("renders custom error fallback when provided", () => {
    render(
      <ErrorBoundary fallback={CustomErrorFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Custom Error")).toBeInTheDocument();
    expect(screen.getByText("Test error message")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Custom Reset" }),
    ).toBeInTheDocument();

    // Default fallback should not be rendered
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("resets error state when reset button is clicked", async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Error fallback should be shown
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Click reset button
    const resetButton = screen.getByRole("button", { name: /try again/i });
    await user.click(resetButton);

    // Rerender with non-throwing component
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>,
    );

    // Should show normal content
    expect(screen.getByText("No error content")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("logs error information to console", () => {
    const consoleErrorSpy = jest.spyOn(console, "error");

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Error caught by boundary:",
      expect.any(Error),
      expect.any(Object),
    );
  });

  it("handles errors without messages gracefully", () => {
    const ErrorWithoutMessage = () => {
      throw new Error("");
    };

    render(
      <ErrorBoundary>
        <ErrorWithoutMessage />
      </ErrorBoundary>,
    );

    // Should show "Unknown error" when error has no message
    screen.getByText("Error details");
    expect(screen.getByText("Unknown error")).toBeInTheDocument();
  });

  it("updates error state when new error occurs", () => {
    const { rerender } = render(
      <ErrorBoundary>
        <div>Initial content</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Initial content")).toBeInTheDocument();

    // Trigger an error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("applies correct styling to default error fallback", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Check card structure
    const card = screen.getByText("Something went wrong").closest(".max-w-md");
    expect(card).toHaveClass("max-w-md", "w-full");

    // Check icon
    const icon = screen
      .getByText("Something went wrong")
      .parentElement?.querySelector(".text-destructive");
    expect(icon).toBeInTheDocument();

    // Check button styling
    const button = screen.getByRole("button", { name: /try again/i });
    expect(button).toHaveClass("w-full");
  });

  it("maintains error boundary state across multiple errors", async () => {
    const user = userEvent.setup();

    let errorMessage = "First error";
    const DynamicError = () => {
      throw new Error(errorMessage);
    };

    const { rerender } = render(
      <ErrorBoundary>
        <DynamicError />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Expand details to see first error
    await user.click(screen.getByText("Error details"));
    expect(screen.getByText("First error")).toBeInTheDocument();

    // Reset and trigger new error
    await user.click(screen.getByRole("button", { name: /try again/i }));

    errorMessage = "Second error";
    rerender(
      <ErrorBoundary>
        <DynamicError />
      </ErrorBoundary>,
    );

    // Should show new error
    await user.click(screen.getByText("Error details"));
    expect(screen.getByText("Second error")).toBeInTheDocument();
  });

  it("handles asynchronous errors", async () => {
    const AsyncError = () => {
      React.useEffect(() => {
        throw new Error("Async error");
      }, []);
      return <div>Loading...</div>;
    };

    // Note: React ErrorBoundary doesn't catch errors in event handlers,
    // async code, or during SSR. This test documents this limitation.
    render(
      <ErrorBoundary>
        <AsyncError />
      </ErrorBoundary>,
    );

    // The error boundary won't catch this async error
    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });
});
