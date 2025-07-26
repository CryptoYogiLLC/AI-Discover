import { NextResponse } from "next/server";

export async function GET() {
  const healthStatus = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
    checks: {
      frontend: {
        status: "healthy",
        version: process.env.npm_package_version || "unknown",
      },
    },
  };

  // Check backend connectivity
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8800";
  try {
    const backendResponse = await fetch(`${apiUrl}/health`, {
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    if (backendResponse.ok) {
      const backendHealth = await backendResponse.json();
      healthStatus.checks.backend = {
        status: "healthy",
        version: backendHealth.version,
        environment: backendHealth.environment,
      };
    } else {
      healthStatus.status = "degraded";
      healthStatus.checks.backend = {
        status: "unhealthy",
        error: `Backend returned ${backendResponse.status}`,
      };
    }
  } catch (error) {
    healthStatus.status = "degraded";
    healthStatus.checks.backend = {
      status: "unhealthy",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }

  const statusCode = healthStatus.status === "healthy" ? 200 : 503;

  return NextResponse.json(healthStatus, { status: statusCode });
}
