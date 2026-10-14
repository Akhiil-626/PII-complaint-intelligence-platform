import { useState, useEffect } from "react"
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
  Navigate,
} from "react-router-dom"
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query"
import { getHealth, type HealthResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"
import { Sun, Moon } from "lucide-react"

import TopNav from "@/components/TopNav"
import Overview from "@/pages/Overview"
import Submit from "@/pages/Submit"
import Privacy from "@/pages/Privacy"
import RootCauses from "@/pages/RootCauses"
import ReviewQueue from "@/pages/ReviewQueue"
import LandingPage from "@/pages/LandingPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 10,
    },
  },
})

function HealthBadge() {
  const { data, isError, isLoading } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 5000,
    retry: false,
  })

  if (isError) {
    return (
      <Badge
        variant="outline"
        className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 gap-1.5 font-medium px-2.5 py-1 text-xs overflow-hidden"
      >
        <span className="h-2 w-2 rounded-full bg-rose-500 shrink-0" />
        <span className="truncate">API offline</span>
      </Badge>
    )
  }

  if (isLoading || !data) {
    return (
      <Badge
        variant="outline"
        className="bg-muted text-muted-foreground border-border gap-1.5 font-medium px-2.5 py-1 text-xs overflow-hidden"
      >
        <span className="h-2 w-2 rounded-full bg-muted-foreground animate-ping shrink-0" />
        <span className="truncate">Checking...</span>
      </Badge>
    )
  }

  if (data.models_loaded) {
    return (
      <Badge
        variant="outline"
        className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1.5 font-medium px-2.5 py-1 text-xs overflow-hidden"
      >
        <span className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
        <span className="truncate">Models ready</span>
      </Badge>
    )
  }

  return (
    <Badge
      variant="outline"
      className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1.5 font-medium px-2.5 py-1 text-xs overflow-hidden"
    >
      <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse shrink-0" />
      <span className="truncate">Models loading</span>
    </Badge>
  )
}

function ThemeToggle() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("theme")
    if (saved) return saved === "dark"
    return window.matchMedia("(prefers-color-scheme: dark)").matches
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      document.documentElement.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
  }, [isDark])

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setIsDark(!isDark)}
      aria-label="Toggle dark mode"
      className="h-8 w-8 rounded-md"
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  )
}

function AppLayout() {
  return (
    <div className="min-h-screen w-full bg-background text-foreground flex flex-col">
      <TopNav
        rightControls={
          <div className="flex items-center gap-3">
            <HealthBadge />
            <ThemeToggle />
          </div>
        }
      />
      {/* Layout-level padding-top using calc(var(--nav-h) + 24px) ensures full header visibility */}
      <main
        className="flex-1 px-4 pb-4 md:px-6 md:pb-6 lg:px-8 lg:pb-8 max-w-7xl w-full mx-auto"
        style={{ paddingTop: "calc(var(--nav-h, 48px) + 24px)" }}
      >
        <Routes>
          <Route path="/overview" element={<Overview />} />
          <Route path="/submit" element={<Submit />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/root-causes" element={<RootCauses />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </main>
    </div>
  )
}

function MainRoutes() {
  const location = useLocation()

  if (location.pathname === "/") {
    return <LandingPage />
  }

  return <AppLayout />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <MainRoutes />
          <Toaster />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  )
}
