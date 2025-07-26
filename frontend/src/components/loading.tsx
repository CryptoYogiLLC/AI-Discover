import { Spinner } from '@/components/ui/spinner'

interface LoadingProps {
  message?: string
}

export function Loading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
      <Spinner size="lg" />
      <p className="text-muted-foreground animate-pulse">{message}</p>
    </div>
  )
}

export function FullPageLoading({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="flex flex-col items-center space-y-4">
        <Spinner size="lg" />
        <p className="text-lg text-muted-foreground animate-pulse">{message}</p>
      </div>
    </div>
  )
}