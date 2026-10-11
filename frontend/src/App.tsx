import { useState, useEffect } from "react"
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
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
import { Separator } from "@/components/ui/separator"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
  SidebarFooter,
} from "@/components/ui/sidebar"
import {
  LayoutDashboard,
  Send,
  ShieldCheck,
  Network,
  Inbox,
  Sun,
  Moon,
  Sparkles,
  Shield,
} from "lucide-react"

import Overview from "@/pages/Overview"
import Submit from "@/pages/Submit"
import Privacy from "@/pages/Privacy"
import RootCauses from "@/pages/RootCauses"
import ReviewQueue from "@/pages/ReviewQueue"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 10,
    },
  },
})

const NAV_ITEMS = [
  { title: "Overview", path: "/", icon: LayoutDashboard },
  { title: "Submit Complaint", path: "/submit", icon: Send },
  { title: "Privacy", path: "/privacy", icon: ShieldCheck },
  { title: "Root Causes", path: "/root-causes", icon: Network },
  { title: "Review Queue", path: "/review", icon: Inbox },
]

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
        <span className="group-data-[collapsible=icon]:hidden truncate">API offline</span>
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
        <span className="group-data-[collapsible=icon]:hidden truncate">Checking...</span>
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
        <span className="group-data-[collapsible=icon]:hidden truncate">Models ready</span>
      </Badge>
    )
  }

  return (
    <Badge
      variant="outline"
      className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1.5 font-medium px-2.5 py-1 text-xs overflow-hidden"
    >
      <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse shrink-0" />
      <span className="group-data-[collapsible=icon]:hidden truncate">Models loading</span>
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

function AppSidebar() {
  const location = useLocation()

  return (
    <Sidebar collapsible="icon" className="overflow-hidden">
      <SidebarHeader className="border-b px-4 py-3 overflow-hidden">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Shield className="h-4 w-4" />
          </div>
          <div className="flex flex-col min-w-0 overflow-hidden group-data-[collapsible=icon]:hidden">
            <span className="text-sm font-semibold truncate leading-none">Privacy Intelligence</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 truncate">CFPB ML Engine</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="overflow-hidden">
        <SidebarGroup>
          <SidebarGroupLabel className="group-data-[collapsible=icon]:hidden truncate">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <SidebarMenuItem key={item.path}>
                    <SidebarMenuButton
                      render={
                        <Link
                          to={item.path}
                          className={`flex items-center gap-2.5 px-3 py-2 rounded-md transition-colors overflow-hidden ${
                            isActive
                              ? "bg-accent text-accent-foreground font-medium"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        />
                      }
                      isActive={isActive}
                      tooltip={item.title}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="group-data-[collapsible=icon]:hidden truncate">{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-3 overflow-hidden space-y-2">
        <div className="flex items-center overflow-hidden group-data-[collapsible=icon]:justify-center">
          <HealthBadge />
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground overflow-hidden">
          <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="group-data-[collapsible=icon]:hidden truncate">k-Anonymity Verified</span>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

function AppLayout() {
  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      <AppSidebar />
      <SidebarInset className="flex flex-col flex-1 min-w-0">
        <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b bg-background/95 backdrop-blur px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <SidebarTrigger />
            <Separator orientation="vertical" className="h-4" />
            <span className="font-semibold text-base sm:text-lg tracking-tight">
              PII Complaint Intelligence Platform
            </span>
          </div>
          <div className="flex items-center gap-3">
            <HealthBadge />
            <ThemeToggle />
          </div>
        </header>

        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/submit" element={<Submit />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/root-causes" element={<RootCauses />} />
            <Route path="/review" element={<ReviewQueue />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </SidebarInset>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <SidebarProvider>
            <AppLayout />
          </SidebarProvider>
          <Toaster />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  )
}
