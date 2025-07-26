'use client'

import { useEffect } from 'react'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center space-y-6 px-4 max-w-md">
        <div className="space-y-2">
          <div className="flex justify-center">
            <div className="rounded-full bg-destructive/10 p-3">
              <AlertCircle className="h-12 w-12 text-destructive" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Oops! Something went wrong
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            We're sorry for the inconvenience. An unexpected error has occurred.
          </p>
        </div>

        {error.digest && (
          <div className="rounded-md bg-gray-100 dark:bg-gray-800 p-3">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Error ID: <code className="font-mono">{error.digest}</code>
            </p>
          </div>
        )}
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button onClick={reset}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Try again
          </Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard">
              <Home className="mr-2 h-4 w-4" />
              Go to Dashboard
            </Link>
          </Button>
        </div>
        
        <div className="pt-8">
          <p className="text-sm text-gray-500 dark:text-gray-500">
            If the problem persists,{' '}
            <Link 
              href="/support" 
              className="text-primary hover:underline font-medium focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
            >
              contact our support team
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}