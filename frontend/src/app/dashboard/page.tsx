"use client";

import { useAuthStore } from "@/store/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart3,
  FolderOpen,
  FileSearch,
  Clock,
  Database,
  FileUp,
  FileText,
  Plus,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuthStore();

  const stats = [
    {
      title: "Active Discoveries",
      value: "3",
      icon: Database,
      description: "In progress",
      color: "text-blue-600",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
    },
    {
      title: "Total Applications",
      value: "47",
      icon: FolderOpen,
      description: "Discovered so far",
      color: "text-purple-600",
      bgColor: "bg-purple-100 dark:bg-purple-900/20",
    },
    {
      title: "Assessment Progress",
      value: "78%",
      icon: FileSearch,
      description: "37 of 47 assessed",
      color: "text-green-600",
      bgColor: "bg-green-100 dark:bg-green-900/20",
    },
    {
      title: "Avg. Processing Time",
      value: "2.4h",
      icon: Clock,
      description: "Per assessment",
      color: "text-orange-600",
      bgColor: "bg-orange-100 dark:bg-orange-900/20",
    },
  ];

  const quickActions = [
    {
      title: "Start Smart Discovery",
      description: "Automatically discover applications",
      icon: Database,
      href: "/discovery/new",
    },
    {
      title: "Manual Data Entry",
      description: "Add application details manually",
      icon: FileText,
      href: "/applications/new",
    },
    {
      title: "Import from File",
      description: "Upload CSV or Excel files",
      icon: FileUp,
      href: "/import",
    },
    {
      title: "View Reports",
      description: "Access generated reports",
      icon: BarChart3,
      href: "/reports",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Application Discovery Dashboard
        </h1>
        <p className="text-muted-foreground mt-2">
          Welcome back, {user?.name || "User"}. Here's your discovery overview.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon
                    className={`h-4 w-4 ${stat.color}`}
                    aria-hidden="true"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Card
                key={action.title}
                className="relative hover:shadow-lg transition-shadow"
              >
                <Link href={action.href} className="absolute inset-0 z-10">
                  <span className="sr-only">{action.title}</span>
                </Link>
                <CardHeader>
                  <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-primary/10 mb-4">
                    <Icon className="h-6 w-6 text-primary" aria-hidden="true" />
                  </div>
                  <CardTitle className="text-base">{action.title}</CardTitle>
                  <CardDescription className="text-sm">
                    {action.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="ghost"
                    className="p-0 h-auto font-medium text-primary hover:text-primary/80"
                    asChild
                  >
                    <span className="flex items-center">
                      Get started
                      <Plus className="ml-1 h-3 w-3" aria-hidden="true" />
                    </span>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Your latest discoveries and assessments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-3 w-[200px]" />
                </div>
                <Skeleton className="h-8 w-[80px]" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
