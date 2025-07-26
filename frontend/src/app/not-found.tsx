import Link from "next/link";
import { Home, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center space-y-6 px-4">
        <div className="space-y-2">
          <h1 className="text-9xl font-bold text-gray-300 dark:text-gray-700">
            404
          </h1>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Page not found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            Sorry, we couldn't find the page you're looking for. It might have
            been moved or deleted.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild>
            <Link href="/dashboard">
              <Home className="mr-2 h-4 w-4" />
              Go to Dashboard
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/search">
              <Search className="mr-2 h-4 w-4" />
              Search
            </Link>
          </Button>
        </div>

        <div className="pt-8">
          <p className="text-sm text-gray-500 dark:text-gray-500">
            Need help?{" "}
            <Link
              href="/support"
              className="text-primary hover:underline font-medium focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
            >
              Contact Support
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
