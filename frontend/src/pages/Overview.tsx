import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  getOverview,
  getCategories,
  getSubIssues,
  getTrend,
  getRecommendations,
  type OverviewResponse,
  type CategoryCount,
  type SubIssueCount,
  type TrendItem,
  type RecommendationItem,
} from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  FileText,
  FolderTree,
  ShieldCheck,
  Radio,
  Clock,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  BarChart3,
  CheckCircle2,
} from "lucide-react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Cell,
} from "recharts"

const CATEGORY_COLORS = [
  "#3b82f6", // blue
  "#8b5cf6", // violet
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#f97316", // orange
  "#6366f1", // indigo
  "#14b8a6", // teal
]

export default function Overview() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const {
    data: overview,
    isLoading: loadingOverview,
    isError: errorOverview,
    refetch: refetchOverview,
  } = useQuery<OverviewResponse>({
    queryKey: ["overview"],
    queryFn: getOverview,
  })

  const {
    data: categories,
    isLoading: loadingCategories,
    refetch: refetchCategories,
  } = useQuery<CategoryCount[]>({
    queryKey: ["categories"],
    queryFn: getCategories,
  })

  // Set default category once categories load
  const activeCategory = selectedCategory || (categories && categories.length > 0 ? categories[0].category : "")

  const {
    data: subIssues,
    isLoading: loadingSubIssues,
    refetch: refetchSubIssues,
  } = useQuery<SubIssueCount[]>({
    queryKey: ["sub-issues", activeCategory],
    queryFn: () => getSubIssues(activeCategory),
    enabled: Boolean(activeCategory),
  })

  const {
    data: trendRaw,
    isLoading: loadingTrend,
    refetch: refetchTrend,
  } = useQuery<TrendItem[]>({
    queryKey: ["trend"],
    queryFn: getTrend,
  })

  const {
    data: recommendations,
    isLoading: loadingRecommendations,
    refetch: refetchRecommendations,
  } = useQuery<RecommendationItem[]>({
    queryKey: ["recommendations"],
    queryFn: getRecommendations,
  })

  // Pivot trend data for Recharts multi-line chart
  const { trendData, allCategories } = useMemo(() => {
    if (!trendRaw || trendRaw.length === 0) return { trendData: [], allCategories: [] }
    const catSet = new Set<string>()
    const byMonth: Record<string, Record<string, any>> = {}

    for (const item of trendRaw) {
      catSet.add(item.category)
      if (!byMonth[item.month]) {
        byMonth[item.month] = { month: item.month }
      }
      byMonth[item.month][item.category] = item.count
    }

    const sortedMonths = Object.keys(byMonth).sort()
    const pivoted = sortedMonths.map((m) => byMonth[m])
    return { trendData: pivoted, allCategories: Array.from(catSet) }
  }, [trendRaw])

  const refetchAll = () => {
    refetchOverview()
    refetchCategories()
    refetchSubIssues()
    refetchTrend()
    refetchRecommendations()
  }

  if (errorOverview) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <AlertCircle className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">Failed to Load Overview Data</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            Unable to connect to backend telemetry. Ensure FastAPI server is running on port 8000.
          </p>
        </div>
        <Button onClick={refetchAll} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </div>
    )
  }

  const statCards = [
    {
      title: "Total Complaints",
      value: overview?.total_complaints.toLocaleString(),
      description: "Batch + live complaints in database",
      icon: FileText,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      title: "Categories",
      value: overview?.total_categories.toLocaleString(),
      description: "Classified financial domains",
      icon: FolderTree,
      color: "text-purple-500",
      bg: "bg-purple-500/10",
    },
    {
      title: "PII Entities Detected & Redacted",
      value: overview?.total_pii_redacted.toLocaleString(),
      description: "Strict privacy redaction count",
      icon: ShieldCheck,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Live Submissions",
      value: overview?.live_submissions.toLocaleString(),
      description: "Real-time incoming submissions",
      icon: Radio,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
    {
      title: "Pending Review",
      value: overview?.pending_review.toLocaleString(),
      description: "Model disagreement flags",
      icon: Clock,
      color: overview && overview.pending_review > 0 ? "text-rose-500" : "text-muted-foreground",
      bg: overview && overview.pending_review > 0 ? "bg-rose-500/10" : "bg-muted",
    },
  ]

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time analytics, category distributions, volume trends, and automated surge recommendations.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refetchAll} className="gap-2 self-start sm:self-auto">
          <RefreshCw className="h-4 w-4" />
          Refresh Data
        </Button>
      </div>

      {/* 5 Headline Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {loadingOverview
          ? Array.from({ length: 5 }).map((_, i) => (
              <Card key={i} className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-8 rounded-lg" />
                </div>
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-3 w-32" />
              </Card>
            ))
          : statCards.map((stat, i) => {
              const Icon = stat.icon
              return (
                <Card key={i} className="relative overflow-hidden transition-all hover:shadow-md border">
                  <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                    <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {stat.title}
                    </CardTitle>
                    <div className={`p-2 rounded-lg ${stat.bg} ${stat.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-1">
                    <div className="text-2xl font-bold tracking-tight">{stat.value ?? "—"}</div>
                    <p className="text-xs text-muted-foreground">{stat.description}</p>
                  </CardContent>
                </Card>
              )
            })}
      </div>

      {/* Charts Grid: Categories & Sub-Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown Bar Chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-primary" />
                  Complaints by Category
                </CardTitle>
                <CardDescription>Click a bar to filter sub-issues</CardDescription>
              </div>
              {activeCategory && (
                <Badge variant="secondary" className="text-xs font-medium">
                  Selected: {activeCategory}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loadingCategories ? (
              <Skeleton className="h-[300px] w-full rounded-md" />
            ) : categories && categories.length > 0 ? (
              <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={categories}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                    onClick={(e: any) => {
                      if (e && e.activePayload && e.activePayload.length > 0) {
                        setSelectedCategory(e.activePayload[0].payload.category)
                      }
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} horizontal={false} />
                    <XAxis type="number" fontSize={11} tickLine={false} />
                    <YAxis
                      dataKey="category"
                      type="category"
                      fontSize={11}
                      tickLine={false}
                      width={95}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        borderColor: "hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(val) => [`${val} complaints`, "Volume"]}
                    />
                    <Bar
                      dataKey="count"
                      radius={[0, 4, 4, 0]}
                      cursor="pointer"
                    >
                      {categories.map((entry, idx) => (
                        <Cell
                          key={`cell-${idx}`}
                          fill={
                            entry.category === activeCategory
                              ? "hsl(var(--primary))"
                              : CATEGORY_COLORS[idx % CATEGORY_COLORS.length]
                          }
                          opacity={entry.category === activeCategory ? 1 : 0.75}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
                No category data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sub-Issue Bar Chart for Active Category */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <FolderTree className="h-4 w-4 text-purple-500" />
                  Sub-Issues: {activeCategory || "Select Category"}
                </CardTitle>
                <CardDescription>Granular breakdown for {activeCategory}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loadingSubIssues ? (
              <Skeleton className="h-[300px] w-full rounded-md" />
            ) : subIssues && subIssues.length > 0 ? (
              <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={subIssues.slice(0, 8)}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 110, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} horizontal={false} />
                    <XAxis type="number" fontSize={11} tickLine={false} />
                    <YAxis
                      dataKey="sub_issue"
                      type="category"
                      fontSize={11}
                      tickLine={false}
                      width={105}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        borderColor: "hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(val) => [`${val} occurrences`, "Count"]}
                    />
                    <Bar
                      dataKey="count"
                      fill="#8b5cf6"
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground text-sm space-y-2">
                <FolderTree className="h-8 w-8 stroke-1 text-muted-foreground/60" />
                <p>No sub-issue breakdown recorded for this category.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trend Line Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-500" />
            Monthly Complaint Trend
          </CardTitle>
          <CardDescription>Historical volume trajectory per financial category</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTrend ? (
            <Skeleton className="h-[350px] w-full rounded-md" />
          ) : trendData.length > 0 ? (
            <div className="h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="month" fontSize={11} tickLine={false} dy={5} />
                  <YAxis fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: "10px", fontSize: "11px" }} />
                  {allCategories.map((cat, idx) => (
                    <Line
                      key={cat}
                      type="monotone"
                      dataKey={cat}
                      name={cat}
                      stroke={CATEGORY_COLORS[idx % CATEGORY_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
              No trend data available.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommendations Surge Alert Cards */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          <h2 className="text-xl font-bold tracking-tight">Active Recommendations & Volume Surges</h2>
        </div>

        {loadingRecommendations ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Skeleton className="h-28 w-full rounded-lg" />
            <Skeleton className="h-28 w-full rounded-lg" />
          </div>
        ) : recommendations && recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, i) => (
              <Card key={i} className="border-amber-500/30 bg-amber-500/5">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold">{rec.category}</CardTitle>
                    <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 font-bold">
                      +{rec.pct_change}% Volume Spike
                    </Badge>
                  </div>
                  <CardDescription className="text-xs">
                    Latest month volume: {rec.volume} complaints
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-foreground/90 font-medium">
                    {rec.recommendation}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-emerald-500/20 bg-emerald-500/5">
            <CardContent className="flex items-center gap-3 py-4">
              <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
              <div className="text-sm">
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  Normal Operating Thresholds:
                </span>{" "}
                <span className="text-muted-foreground">
                  No anomalous volume spikes detected in recent complaints across all 9 categories.
                </span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
