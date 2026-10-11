import { useQuery } from "@tanstack/react-query"
import { getPrivacy, type PrivacyResponse } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  Percent,
} from "lucide-react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts"

const ENTITY_PALETTE = [
  "#10b981", // emerald
  "#3b82f6", // blue
  "#8b5cf6", // purple
  "#f59e0b", // amber
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#f97316", // orange
  "#64748b", // slate
]

export default function Privacy() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<PrivacyResponse>({
    queryKey: ["privacy"],
    queryFn: getPrivacy,
  })

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <AlertCircle className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">Failed to Load Privacy Metrics</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            {error instanceof Error ? error.message : "Error querying privacy audit endpoints."}
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Privacy Preservation & Redaction</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Zero-trust PII scrubbing via Presidio and mathematical k-anonymity quasi-identifier audits.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="gap-2 self-start sm:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Top Stat Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total PII Redacted
              </CardTitle>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                <ShieldCheck className="h-4 w-4" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-3xl font-bold tracking-tight text-foreground">
                {data?.total_redacted.toLocaleString()}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Scrubbed entities across all datasets</p>
          </CardContent>
        </Card>

        <Card className="border shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Re-Identification Reduction
              </CardTitle>
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
                <Percent className="h-4 w-4" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="text-3xl font-bold tracking-tight text-blue-500">
                {data
                  ? `${(data.k_anonymity.baseline.pct_at_risk - data.k_anonymity.mitigated.pct_at_risk).toFixed(1)}%`
                  : "—"}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Drop in vulnerable record footprint</p>
          </CardContent>
        </Card>

        <Card className="border shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Active Mitigating Strategy
              </CardTitle>
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
                <Lock className="h-4 w-4" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            {isLoading ? (
              <Skeleton className="h-8 w-36" />
            ) : (
              <div className="text-lg font-mono font-bold truncate text-foreground">
                {data?.k_anonymity.strategy || "—"}
              </div>
            )}
            <p className="text-xs text-muted-foreground">Quasi-identifier generalization scheme</p>
          </CardContent>
        </Card>
      </div>

      {/* Entity Breakdown Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-emerald-500" />
            Redacted Entity Breakdown
          </CardTitle>
          <CardDescription>
            Frequency distribution of identified and scrubbed PII token categories
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[280px] w-full rounded-md" />
          ) : data && data.breakdown.length > 0 ? (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.breakdown}
                  margin={{ top: 10, right: 30, left: 10, bottom: 30 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} vertical={false} />
                  <XAxis
                    dataKey="entity_type"
                    fontSize={11}
                    tickLine={false}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                  />
                  <YAxis fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val) => [`${val} tokens scrubbed`, "Entities"]}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {data.breakdown.map((_, idx) => (
                      <Cell
                        key={`cell-${idx}`}
                        fill={ENTITY_PALETTE[idx % ENTITY_PALETTE.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-muted-foreground text-sm">
              No entity redaction records available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Side-by-Side k-Anonymity Risk Comparison */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">k-Anonymity Compliance Audit</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Empirical re-identification risk metrics comparing baseline data vs mitigated release.
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-64 w-full rounded-lg" />
            <Skeleton className="h-64 w-full rounded-lg" />
          </div>
        ) : data ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Baseline Card */}
            <Card className="border-rose-500/20 bg-rose-500/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-rose-500" />
                    Baseline (Unmitigated)
                  </CardTitle>
                  <Badge variant="outline" className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 text-xs">
                    High Re-ID Risk
                  </Badge>
                </div>
                <CardDescription>
                  Original data with unbinned submission timestamps and granular sub-products
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Unique Record Signatures:</span>
                    <span className="font-mono font-bold text-base text-rose-600 dark:text-rose-400">
                      {data.k_anonymity.baseline.pct_unique}%
                    </span>
                  </div>
                  <div className="w-full bg-rose-500/20 rounded-full h-2">
                    <div
                      className="bg-rose-500 h-2 rounded-full"
                      style={{ width: `${data.k_anonymity.baseline.pct_unique}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Records at Re-ID Risk:</span>
                    <span className="font-mono font-bold text-base text-rose-600 dark:text-rose-400">
                      {data.k_anonymity.baseline.pct_at_risk}%
                    </span>
                  </div>
                  <div className="w-full bg-rose-500/20 rounded-full h-2">
                    <div
                      className="bg-rose-500 h-2 rounded-full"
                      style={{ width: `${data.k_anonymity.baseline.pct_at_risk}%` }}
                    />
                  </div>
                </div>

                <div className="pt-2 text-xs text-muted-foreground">
                  Baseline state exposes over 80% of rows to auxiliary linkage attacks via quasi-identifiers.
                </div>
              </CardContent>
            </Card>

            {/* Mitigated Card */}
            <Card className="border-emerald-500/20 bg-emerald-500/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    Mitigated (Compliant Release)
                  </CardTitle>
                  <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs">
                    Audit Passed
                  </Badge>
                </div>
                <CardDescription>
                  Applied strategy: <code className="font-mono text-primary">{data.k_anonymity.strategy}</code>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Unique Record Signatures:</span>
                    <span className="font-mono font-bold text-base text-emerald-600 dark:text-emerald-400">
                      {data.k_anonymity.mitigated.pct_unique}%
                    </span>
                  </div>
                  <div className="w-full bg-emerald-500/20 rounded-full h-2">
                    <div
                      className="bg-emerald-500 h-2 rounded-full"
                      style={{ width: `${data.k_anonymity.mitigated.pct_unique}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Records at Re-ID Risk:</span>
                    <span className="font-mono font-bold text-base text-emerald-600 dark:text-emerald-400">
                      {data.k_anonymity.mitigated.pct_at_risk}%
                    </span>
                  </div>
                  <div className="w-full bg-emerald-500/20 rounded-full h-2">
                    <div
                      className="bg-emerald-500 h-2 rounded-full"
                      style={{ width: `${data.k_anonymity.mitigated.pct_at_risk}%` }}
                    />
                  </div>
                </div>

                <div className="pt-2 text-xs text-muted-foreground">
                  Achieves significant risk reduction while maintaining downstream classification fidelity.
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </div>
  )
}
