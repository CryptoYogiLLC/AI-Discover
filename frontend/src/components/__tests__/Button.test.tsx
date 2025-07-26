import React from "react";
import { render, screen } from "@/test-utils";
import { Button } from "@/components/ui/button";

describe("Button Component", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("handles click events", async () => {
    const handleClick = jest.fn();
    const { user } = render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole("button", { name: /click me/i });
    await user.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("can be disabled", () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByRole("button", { name: /disabled button/i });
    expect(button).toBeDisabled();
  });

  it("applies variant styles", () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-blue-600");
    
    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-gray-600");
    
    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-red-600");
  });

  it("applies size styles", () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button")).toHaveClass("text-sm");
    
    rerender(<Button size="md">Medium</Button>);
    expect(screen.getByRole("button")).toHaveClass("text-base");
    
    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button")).toHaveClass("text-lg");
  });

  it("shows loading state", () => {
    render(<Button loading>Loading</Button>);
    
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renders as a link when href is provided", () => {
    render(<Button href="/dashboard">Go to Dashboard</Button>);
    
    const link = screen.getByRole("link", { name: /go to dashboard/i });
    expect(link).toHaveAttribute("href", "/dashboard");
  });

  it("supports full width", () => {
    render(<Button fullWidth>Full Width Button</Button>);
    
    const button = screen.getByRole("button");
    expect(button).toHaveClass("w-full");
  });

  it("forwards ref", () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Button with ref</Button>);
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("accepts additional className", () => {
    render(<Button className="custom-class">Custom Button</Button>);
    
    const button = screen.getByRole("button");
    expect(button).toHaveClass("custom-class");
  });

  it("supports keyboard interaction", async () => {
    const handleClick = jest.fn();
    const { user } = render(<Button onClick={handleClick}>Keyboard Button</Button>);
    
    const button = screen.getByRole("button");
    button.focus();
    
    await user.keyboard("{Enter}");
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    await user.keyboard(" ");
    expect(handleClick).toHaveBeenCalledTimes(2);
  });
});