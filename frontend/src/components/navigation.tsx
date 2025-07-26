"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  FolderOpen,
  FileSearch,
  BarChart3,
  Settings,
  Menu,
  X,
  LogOut,
  User,
  Shield,
  Users,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

type NavItem = {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: Array<"admin" | "user" | "viewer">;
};

const navItems: NavItem[] = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: Home,
    roles: ["admin", "user", "viewer"],
  },
  {
    name: "Projects",
    href: "/projects",
    icon: FolderOpen,
    roles: ["admin", "user"],
  },
  {
    name: "Assessments",
    href: "/assessments",
    icon: FileSearch,
    roles: ["admin", "user"],
  },
  {
    name: "Reports",
    href: "/reports",
    icon: BarChart3,
    roles: ["admin", "user", "viewer"],
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
    roles: ["admin", "user"],
  },
];

const adminOnlyItems: NavItem[] = [
  {
    name: "Users",
    href: "/admin/users",
    icon: Users,
    roles: ["admin"],
  },
  {
    name: "Security",
    href: "/admin/security",
    icon: Shield,
    roles: ["admin"],
  },
];

export function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const filteredNavItems = navItems.filter((item) =>
    user?.role ? item.roles.includes(user.role) : false,
  );

  const filteredAdminItems = adminOnlyItems.filter((item) =>
    user?.role ? item.roles.includes(user.role) : false,
  );

  const allItems = [...filteredNavItems, ...filteredAdminItems];

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link
                href="/dashboard"
                className="text-xl font-bold text-primary hover:text-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
              >
                AI-Discover
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:ml-6 md:flex md:space-x-1">
              {filteredNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                      isActive
                        ? "bg-primary/10 text-primary dark:bg-primary/20"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}

              {/* Admin Dropdown */}
              {filteredAdminItems.length > 0 && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="inline-flex items-center px-3 py-2 text-sm font-medium"
                    >
                      <Shield className="mr-2 h-4 w-4" />
                      Admin
                      <ChevronDown className="ml-1 h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-48">
                    {filteredAdminItems.map((item) => {
                      const Icon = item.icon;
                      return (
                        <DropdownMenuItem key={item.name} asChild>
                          <Link
                            href={item.href}
                            className="flex items-center w-full"
                          >
                            <Icon className="mr-2 h-4 w-4" />
                            {item.name}
                          </Link>
                        </DropdownMenuItem>
                      );
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative rounded-full p-1 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  aria-label="User menu"
                >
                  <div className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="h-4 w-4 text-primary" />
                    </div>
                    <span className="hidden md:block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {user?.name || user?.email}
                    </span>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/profile" className="flex items-center w-full">
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="flex items-center w-full">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="text-destructive cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
                aria-expanded={isMobileMenuOpen}
              >
                {isMobileMenuOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t border-gray-200 dark:border-gray-700"
          >
            <div className="px-2 pt-2 pb-3 space-y-1">
              {allItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center px-3 py-2 text-base font-medium rounded-md transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary dark:bg-primary/20"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
