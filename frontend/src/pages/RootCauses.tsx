import { useState, useRef, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  getRootCauses,
  getCausalGraph,
  type RootCauseItem,
  type CausalGraphResponse,
} from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import {
  Network,
  BarChart3,
  RefreshCw,
  AlertCircle,
  Info,
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
import ForceGraph2D from "react-force-graph-2d"

const TYPE_COLORS: Record<string, string> = {
  root_cause: "#ef4444", // Red
  immediate_cause: "#f59e0b", // Amber
  category: "#3b82f6", // Blue
}

export default function RootCauses() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [graphWidth, setGraphWidth] = useState(800)

  const {
    data: rootCauses,
    isLoading: loadingCauses,
    isError: errorCauses,
    refetch: refetchCauses,
  } = useQuery<RootCauseItem[]>({
    queryKey: ["root-causes"],
    queryFn: getRootCauses,
  })

  const {
    data: graphDataRaw,
    isLoading: loadingGraph,
    isError: errorGraph,
    refetch: refetchGraph,
    isFetching: fetchingGraph,
  } = useQuery<CausalGraphResponse>({
    queryKey: ["causal-graph"],
    queryFn: getCausalGraph,
  })

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setGraphWidth(containerRef.current.clientWidth)
      }
    }
    updateWidth()
    window.addEventListener("resize", updateWidth)
    return () => window.removeEventListener("resize", updateWidth)
  }, [])

  const refetchAll = () => {
    refetchCauses()
    refetchGraph()
  }

  // Format data for react-force-graph-2d
  const formattedGraph = graphDataRaw
    ? {
        nodes: graphDataRaw.nodes.map((n) => ({
          id: n.id,
          name: n.id,
          type: n.type || "unknown",
          val: n.type === "root_cause" ? 7 : n.type === "category" ? 10 : 5,
        })),
        links: graphDataRaw.edges.map((e) => ({
          source: e.source,
          target: e.target,
          weight: e.weight || 1,
        })),
      }
    : { nodes: [], links: [] }

  if (errorCauses || errorGraph) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <AlertCircle className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">Failed to Load Causal Intelligence</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            Unable to fetch root causes or parse graph structure.
          </p>
        </div>
        <Button onClick={refetchAll} variant="outline" className="gap-2">
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
          <h1 className="text-3xl font-bold tracking-tight">Causal Discovery & Root Causes</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Structural causal graph mapping root causes to immediate customer issues and categories.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refetchAll}
          disabled={fetchingGraph}
          className="gap-2 self-start sm:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${fetchingGraph ? "animate-spin" : ""}`} />
          Refresh Graph
        </Button>
      </div>

      {/* Top Root Causes Horizontal Bar Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-rose-500" />
                Top 10 Root Causes by Outgoing Influence
              </CardTitle>
              <CardDescription>
                Sum of outgoing edge weights in causal DAG representing propagated fault impact
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingCauses ? (
            <Skeleton className="h-[320px] w-full rounded-md" />
          ) : rootCauses && rootCauses.length > 0 ? (
            <div className="h-[340px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={rootCauses}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 180, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} horizontal={false} />
                  <XAxis type="number" fontSize={11} tickLine={false} />
                  <YAxis
                    dataKey="root_cause"
                    type="category"
                    fontSize={11}
                    tickLine={false}
                    width={170}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val) => [`${val} aggregated impact weight`, "Causal Influence"]}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {rootCauses.map((_, idx) => (
                      <Cell
                        key={`cell-${idx}`}
                        fill="#ef4444"
                        opacity={1 - idx * 0.05}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
              No root causes identified.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Force-Directed Graph Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Network className="h-4 w-4 text-primary" />
                Interactive Causal Dependency Graph
              </CardTitle>
              <CardDescription>
                Drag nodes to inspect dependency clusters and downstream category pathways
              </CardDescription>
            </div>

            {/* Graph Legend */}
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-[#ef4444]" />
                <span>Root Cause</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-[#f59e0b]" />
                <span>Immediate Cause</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full bg-[#3b82f6]" />
                <span>Product Category</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div
            ref={containerRef}
            className="w-full h-[520px] rounded-lg border overflow-hidden bg-slate-950 relative"
          >
            {loadingGraph ? (
              <div className="h-full flex items-center justify-center">
                <Skeleton className="h-full w-full" />
              </div>
            ) : formattedGraph.nodes.length > 0 ? (
              <ForceGraph2D
                width={graphWidth}
                height={520}
                graphData={formattedGraph}
                nodeLabel={(node: any) => `${node.id} (${node.type})`}
                nodeColor={(node: any) => TYPE_COLORS[node.type] || "#a855f7"}
                nodeRelSize={4}
                linkWidth={(link: any) => Math.sqrt(link.weight || 1)}
                linkColor={() => "#475569"}
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                cooldownTicks={100}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                No graph nodes or edges found.
              </div>
            )}
          </div>

          {/* Mandatory Caption */}
          <div className="mt-3 flex items-start gap-2 text-xs text-muted-foreground p-3 rounded-md bg-muted/50 border">
            <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
            <p>
              Analysis ran on a sample using a local LLM. Causal pairs were systematically extracted and structured into NetworkX GEXF graph representations.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
