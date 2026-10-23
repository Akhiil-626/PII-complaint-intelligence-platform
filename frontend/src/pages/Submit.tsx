import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  submitComplaint,
  getSubmissions,
  type ProcessComplaintResponse,
  type LiveSubmissionRecord,
} from "@/lib/api"
import SafeguardBadges from "@/components/complaint/SafeguardBadges"
import RedactionComparison from "@/components/complaint/RedactionComparison"
import ModelConfidence from "@/components/complaint/ModelConfidence"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Send,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Bot,
  Layers,
  History,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react"
import { toast } from "sonner"

export default function Submit() {
  const [complaintText, setComplaintText] = useState("")
  const [submittedText, setSubmittedText] = useState("")
  const [lastResult, setLastResult] = useState<ProcessComplaintResponse | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    return () => {
      setSubmittedText("")
    }
  }, [])

  const {
    data: recentSubmissions,
    isLoading: loadingSubmissions,
    refetch: refetchSubmissions,
    isFetching: fetchingSubmissions,
  } = useQuery<LiveSubmissionRecord[]>({
    queryKey: ["submissions"],
    queryFn: () => getSubmissions(20),
    refetchOnMount: "always",
  })

  const mutation = useMutation({
    mutationFn: (text: string) => submitComplaint(text),
    onSuccess: (data, variables) => {
      setSubmittedText(variables)
      setLastResult(data)
      toast.success("Complaint processed successfully", {
        description: `Generated Complaint ID: ${data.complaint_id}`,
      })
      queryClient.invalidateQueries({ queryKey: ["submissions"] })
      queryClient.invalidateQueries({ queryKey: ["overview"] })
      queryClient.invalidateQueries({ queryKey: ["review-queue"] })
    },
    onError: (err: any) => {
      const msg = err?.message || ""
      if (msg.includes("503") || msg.toLowerCase().includes("loading")) {
        toast.error("Models still loading, try again shortly", {
          description: "High-parameter neural models are initializing in the background.",
        })
      } else {
        toast.error("Processing failed", {
          description: msg || "Failed to process complaint text.",
        })
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = complaintText.trim()
    if (!trimmed) {
      toast.error("Please enter complaint text before submitting.")
      return
    }
    if (trimmed.length > 10000) {
      toast.error("Complaint text is too long (maximum 10,000 characters).")
      return
    }
    setSubmittedText("")
    mutation.mutate(trimmed)
  }

  const handleFillSample = (sample: string) => {
    setComplaintText(sample)
  }

  return (
    <div className="space-y-10">
      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Submit & Analyze Complaint</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Real-time privacy scrubbing, 3-model consensus benchmarking, and hierarchical classification.
        </p>
      </div>

      {/* Submission Form */}
      <Card className="border shadow-sm">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Send className="h-4 w-4 text-primary" />
                Live Complaint Ingestion
              </CardTitle>
              <CardDescription>
                Raw text undergoes Presidio entity masking before any LLM inference or database storage.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() =>
                  handleFillSample(
                    "My name is John Smith and I was charged twice for my credit card bill of $450 this month on card 4111-2222-3333-4444. Please email me at john.smith@example.com."
                  )
                }
              >
                Sample (PII Rich)
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() =>
                  handleFillSample(
                    "I was charged twice on my credit card and nobody is helping me"
                  )
                }
              >
                Sample (Double Charge)
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Textarea
              placeholder="Paste or type customer complaint here. PII will be automatically detected and redacted..."
              className="min-h-[120px] resize-y font-mono text-sm leading-relaxed"
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              disabled={mutation.isPending}
            />

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
              <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                Presidio redaction engine: strict privacy mode active
              </div>
              <Button
                type="submit"
                disabled={mutation.isPending || !complaintText.trim()}
                className="gap-2 min-w-[170px]"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Processing... (20-60s)
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Process Complaint
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {lastResult && (
        <div className="space-y-6 animate-in fade-in-50 duration-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <h2 className="text-xl font-bold tracking-tight">Intelligence Pipeline Output</h2>
            </div>
            <Badge variant="outline" className="font-mono text-xs px-2.5 py-1">
              ID: {lastResult.complaint_id}
            </Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Redacted Text & Summary Card */}
            <Card className="flex flex-col justify-between">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-500" />
                  Redacted Complaint Text
                </CardTitle>
                <CardDescription>Zero raw PII leaves this perimeter</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3.5 rounded-md bg-muted/60 text-xs font-mono leading-relaxed border whitespace-pre-wrap">
                  {lastResult.redacted_text}
                </div>

                <div className="space-y-1.5 pt-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Bot className="h-3.5 w-3.5 text-primary" />
                    AI Summary (Llama 3.1 8B)
                  </span>
                  <p className="text-sm leading-relaxed p-3 rounded-md bg-primary/5 border border-primary/20 text-foreground font-medium">
                    {lastResult.summary}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Classification & Consensus Card */}
            <Card className="flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Layers className="h-4 w-4 text-purple-500" />
                    Classification & Model Agreement
                  </CardTitle>
                  {lastResult.agreement.needs_review ? (
                    <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1 text-xs">
                      <AlertTriangle className="h-3 w-3" />
                      Needs Review
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1 text-xs">
                      <CheckCircle2 className="h-3 w-3" />
                      Unanimous
                    </Badge>
                  )}
                </div>
                {lastResult.agreement.review_reason && (
                  <CardDescription className="text-xs text-amber-600 dark:text-amber-400">
                    Reason: {lastResult.agreement.review_reason}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Official Hierarchical Decision */}
                <div className="p-3.5 rounded-lg border bg-card space-y-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Final Hierarchical Classification
                  </span>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="text-base font-bold text-foreground">
                        {lastResult.final_classification.domain}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-2 mt-0.5">
                        <span>Sub-issue: {lastResult.final_classification.sub_issue}</span>
                        {lastResult.final_classification.sub_issue_confidence < 0.3 && (
                          <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4">
                            Low confidence
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-primary">
                        {(lastResult.final_classification.domain_confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-[10px] text-muted-foreground">Domain Conf.</div>
                    </div>
                  </div>
                </div>

                {/* 3-Model Comparison Table */}
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Model Comparison Benchmarking
                  </span>
                  <div className="rounded-md border overflow-hidden">
                    <Table>
                      <TableHeader className="bg-muted/40">
                        <TableRow className="h-8">
                          <TableHead className="text-xs">Model Architecture</TableHead>
                          <TableHead className="text-xs">Predicted Domain</TableHead>
                          <TableHead className="text-xs text-right">Confidence</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow className="h-9">
                          <TableCell className="font-medium text-xs">TF-IDF + SVM</TableCell>
                          <TableCell className="text-xs">{lastResult.model_comparison.tfidf_svm.category}</TableCell>
                          <TableCell className="text-xs text-right font-mono font-semibold">
                            {(lastResult.model_comparison.tfidf_svm.confidence * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                        <TableRow className="h-9">
                          <TableCell className="font-medium text-xs">Sentence-BERT + LogReg</TableCell>
                          <TableCell className="text-xs">{lastResult.model_comparison.sentence_bert_logreg.category}</TableCell>
                          <TableCell className="text-xs text-right font-mono font-semibold">
                            {(lastResult.model_comparison.sentence_bert_logreg.confidence * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                        <TableRow className="h-9">
                          <TableCell className="font-medium text-xs">Fine-Tuned DistilBERT</TableCell>
                          <TableCell className="text-xs">{lastResult.model_comparison.distilbert.category}</TableCell>
                          <TableCell className="text-xs text-right font-mono font-semibold">
                            {(lastResult.model_comparison.distilbert.confidence * 100).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Redacted Entities Table */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-emerald-500" />
                Detected & Redacted Entities ({lastResult.entities_redacted.length})
              </CardTitle>
              <CardDescription>
                Audited tokens scrubbed from the original complaint stream
              </CardDescription>
            </CardHeader>
            <CardContent>
              {lastResult.entities_redacted.length > 0 ? (
                <div className="rounded-md border overflow-hidden">
                  <Table>
                    <TableHeader className="bg-muted/40">
                      <TableRow className="h-8">
                        <TableHead className="text-xs">Entity Type</TableHead>
                        <TableHead className="text-xs">Scrubbed Text</TableHead>
                        <TableHead className="text-xs text-right">Detection Score</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lastResult.entities_redacted.map((ent, idx) => (
                        <TableRow key={idx} className="h-9">
                          <TableCell className="text-xs font-medium">
                            <Badge variant="outline" className="text-[11px] font-mono">
                              {ent.entity_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs font-mono text-muted-foreground">
                            {ent.text || "—"}
                          </TableCell>
                          <TableCell className="text-xs text-right font-mono">
                            {ent.score != null ? (ent.score * 100).toFixed(0) + "%" : "100%"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="py-6 text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  No identifiable PII entities detected in this complaint.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Safeguard Badges */}
          <SafeguardBadges
            leakCheck={lastResult.leak_check}
            scopeCheck={lastResult.scope_check}
            agreement={lastResult.agreement}
          />

          {/* Redaction Comparison */}
          <RedactionComparison
            submittedText={submittedText}
            entities={lastResult.entities_redacted}
            redactedText={lastResult.redacted_text}
          />

          {/* Model Confidence & Consensus */}
          <ModelConfidence
            modelComparison={lastResult.model_comparison}
            agreement={lastResult.agreement}
            finalDomain={lastResult.final_classification.domain}
          />
        </div>
      )}

      {/* Recent Submissions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4 text-muted-foreground" />
                Recent Live Submissions
              </CardTitle>
              <CardDescription>Last 20 complaints processed by the live pipeline</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchSubmissions()}
              disabled={fetchingSubmissions}
              className="gap-1.5 text-xs"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${fetchingSubmissions ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingSubmissions ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : recentSubmissions && recentSubmissions.length > 0 ? (
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow className="h-9">
                    <TableHead className="text-xs whitespace-nowrap">ID</TableHead>
                    <TableHead className="text-xs whitespace-nowrap">Date / Time</TableHead>
                    <TableHead className="text-xs whitespace-nowrap">Predicted Domain</TableHead>
                    <TableHead className="text-xs whitespace-nowrap">Sub-Issue</TableHead>
                    <TableHead className="text-xs">Redacted Text</TableHead>
                    <TableHead className="text-xs whitespace-nowrap text-center">Review Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentSubmissions.map((row) => (
                    <TableRow key={row.complaint_id} className="hover:bg-muted/50">
                      <TableCell className="text-xs font-mono font-medium whitespace-nowrap">
                        {row.complaint_id}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(row.timestamp).toLocaleString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </TableCell>
                      <TableCell className="text-xs font-medium whitespace-nowrap">
                        {row.predicted_category}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[150px] truncate">
                        {row.predicted_sub_issue || "—"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[260px] truncate font-mono">
                        {row.redacted_text}
                      </TableCell>
                      <TableCell className="text-center whitespace-nowrap">
                        {row.resolved ? (
                          <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px]">
                            Resolved
                          </Badge>
                        ) : row.needs_review ? (
                          <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-[10px]">
                            Pending Review
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px]">
                            Valid
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No live submissions recorded yet.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
