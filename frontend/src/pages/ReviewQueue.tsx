import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getReviewQueue,
  resolveReviewItem,
  type LiveSubmissionRecord,
} from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  AlertCircle,
  CheckCheck,
  Layers,
} from "lucide-react"
import { toast } from "sonner"

export default function ReviewQueue() {
  const queryClient = useQueryClient()

  const {
    data: items,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<LiveSubmissionRecord[]>({
    queryKey: ["review-queue"],
    queryFn: getReviewQueue,
  })

  const resolveMutation = useMutation({
    mutationFn: (complaintId: string) => resolveReviewItem(complaintId),
    onSuccess: (_, complaintId) => {
      toast.success("Flag resolved", {
        description: `Complaint ${complaintId} marked as resolved and removed from review queue.`,
      })
      queryClient.invalidateQueries({ queryKey: ["review-queue"] })
      queryClient.invalidateQueries({ queryKey: ["overview"] })
      queryClient.invalidateQueries({ queryKey: ["submissions"] })
    },
    onError: (err: any) => {
      toast.error("Failed to resolve complaint", {
        description: err?.message || "Could not update resolution status.",
      })
    },
  })

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
          <AlertCircle className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">Failed to Load Review Queue</h2>
          <p className="text-sm text-muted-foreground max-w-md">
            {error instanceof Error ? error.message : "Error querying review items from server."}
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
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight"> Review Queue</h1>
            {items && items.length > 0 && (
              <Badge variant="destructive" className="text-xs px-2 py-0.5 font-bold">
                {items.length} Pending
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Complaints flagged by automated confidence guards due to inter-model disagreement or low confidence.
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

      {/* Review Queue Items */}
      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-44 w-full rounded-xl" />
          <Skeleton className="h-44 w-full rounded-xl" />
          <Skeleton className="h-44 w-full rounded-xl" />
        </div>
      ) : items && items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.complaint_id} className="border border-border/80 shadow-sm transition-all hover:shadow-md">
              <CardHeader className="pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <CardTitle className="font-mono text-base font-bold text-foreground">
                        {item.complaint_id}
                      </CardTitle>
                      <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        Flagged For Review
                      </Badge>
                    </div>
                    <CardDescription className="text-xs text-muted-foreground">
                      Submitted on {new Date(item.timestamp).toLocaleString()}
                    </CardDescription>
                  </div>

                  <Button
                    size="sm"
                    className="gap-2 self-start sm:self-auto shrink-0 bg-emerald-600 hover:bg-emerald-700 text-white"
                    disabled={resolveMutation.isPending}
                    onClick={() => resolveMutation.mutate(item.complaint_id)}
                  >
                    <CheckCheck className="h-4 w-4" />
                    Mark as resolved
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Review Reason Alert */}
                {item.review_reason && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300 font-medium flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
                    <div>
                      <span className="font-bold">Disagreement Trigger:</span> {item.review_reason}
                    </div>
                  </div>
                )}

                {/* Redacted Complaint Text */}
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Redacted Complaint Excerpt
                  </span>
                  <div className="p-3.5 rounded-md bg-muted/50 border text-xs font-mono leading-relaxed text-foreground/90 whitespace-pre-wrap">
                    {item.redacted_text}
                  </div>
                </div>

                {/* 3 Model Predictions Row */}
                <div className="space-y-2 pt-1">
                  <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-primary" />
                    Tri-Model Classification Breakdown
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-2.5 rounded-lg border bg-card space-y-1">
                      <div className="text-[11px] text-muted-foreground font-medium">TF-IDF + SVM</div>
                      <div className="text-xs font-bold text-foreground truncate">
                        {item.tfidf_prediction || "—"}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-lg border bg-card space-y-1">
                      <div className="text-[11px] text-muted-foreground font-medium">Sentence-BERT + LogReg</div>
                      <div className="text-xs font-bold text-foreground truncate">
                        {item.sbert_prediction || "—"}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-lg border bg-card space-y-1">
                      <div className="text-[11px] text-muted-foreground font-medium">DistilBERT</div>
                      <div className="text-xs font-bold text-foreground truncate">
                        {item.distilbert_prediction || "—"}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        /* Empty State */
        <Card className="border-dashed py-16 text-center">
          <CardContent className="flex flex-col items-center justify-center space-y-4">
            <div className="h-16 w-16 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <CheckCircle className="h-8 w-8" />
            </div>
            <div className="space-y-1 max-w-sm">
              <h3 className="text-xl font-bold tracking-tight">No complaints need review</h3>
              <p className="text-sm text-muted-foreground">
                All live complaints have reached model consensus or have already been resolved by human reviewers.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Check for New Submissions
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
