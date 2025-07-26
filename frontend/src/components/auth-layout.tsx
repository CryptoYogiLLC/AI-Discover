"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Navigation } from "@/components/navigation";
import { useAuthStore } from "@/store/auth";

const publicRoutes = ["/login", "/register", "/forgot-password"];

export function AuthLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading) {
      const isPublicRoute = publicRoutes.includes(pathname);

      if (!isAuthenticated && !isPublicRoute) {
        router.push("/login");
      } else if (isAuthenticated && isPublicRoute) {
        router.push("/dashboard");
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Show nothing while checking auth status
  if (isLoading) {
    return null;
  }

  // For public routes, render without navigation
  if (publicRoutes.includes(pathname)) {
    return <>{children}</>;
  }

  // For authenticated routes, render with navigation
  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main id="main-content" className="py-6" role="main">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    );
  }

  // Fallback (should not reach here due to useEffect redirect)
  return null;
}
