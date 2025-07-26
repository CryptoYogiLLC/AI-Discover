import React from "react";
import RootLayout from "../layout";

// Mock the next/font/google module
jest.mock("next/font/google", () => ({
  Inter: () => ({
    className: "inter-font",
  }),
}));

// Mock the components that might cause issues in tests
jest.mock("@/components/skip-link", () => ({
  SkipLink: () => null,
}));

jest.mock("@/components/auth-layout", () => ({
  AuthLayout: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("../providers", () => ({
  Providers: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("RootLayout", () => {
  it("renders without crashing", () => {
    // Test that the component can be instantiated
    const TestChild = () => <div>Test Content</div>;
    const element = RootLayout({ children: <TestChild /> });

    // Check that it returns a valid React element
    expect(element).toBeTruthy();
    expect(element.type).toBe("html");
    expect(element.props.lang).toBe("en");
    expect(element.props.suppressHydrationWarning).toBe(true);
  });
});
