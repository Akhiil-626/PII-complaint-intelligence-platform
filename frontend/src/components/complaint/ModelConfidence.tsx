import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, CheckCircle2, AlertTriangle, Users } from "lucide-react"
import type { ModelComparison, Agreement } from "@/lib/api"

interface ModelConfidenceProps {
  modelComparison: ModelComparison
  agreement: Agreement
  finalDomain: string
}

const CATEGORY_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  "Bank account/service": {
    bar: "bg-blue-500 dark:bg-blue-400",
    text: "text-blue-700 dark:text-blue-300",
    bg: "bg-blue-50 dark:bg-blue-950/40",
  },
  "Credit reporting": {
    bar: "bg-purple-500 dark:bg-purple-400",
    text: "text-purple-700 dark:text-purple-300",
    bg: "bg-purple-50 dark:bg-purple-950/40",
  },
  "Credit/Prepaid card": {
    bar: "bg-indigo-500 dark:bg-indigo-400",
    text: "text-indigo-700 dark:text-indigo-300",
    bg: "bg-indigo-50 dark:bg-indigo-950/40",
  },
  "Debt collection": {
    bar: "bg-rose-500 dark:bg-rose-400",
    text: "text-rose-700 dark:text-rose-300",
    bg: "bg-rose-50 dark:bg-rose-950/40",
  },
  "Money transfer": {
    bar: "bg-emerald-500 dark:bg-emerald-400",
    text: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-950/40",
  },
  "Mortgage": {
    bar: "bg-cyan-500 dark:bg-cyan-400",
    text: "text-cyan-700 dark:text-cyan-300",
    bg: "bg-cyan-50 dark:bg-cyan-950/40",
  },
  "Personal/Payday loan": {
    bar: "bg-amber-500 dark:bg-amber-400",
    text: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-950/40",
  },
  "Student loan": {
    bar: "bg-teal-500 dark:bg-teal-400",
    text: "text-teal-700 dark:text-teal-300",
    bg: "bg-teal-50 dark:bg-teal-950/40",
  },
  "Vehicle loan or lease": {
    bar: "bg-orange-500 dark:bg-orange-400",
    text: "text-orange-700 dark:text-orange-300",
    bg: "bg-orange-50 dark:bg-orange-950/40",
  },
}

const DEFAULT_COLOR = {
  bar: "bg-primary",
  text: "text-foreground",
  bg: "bg-muted",
}

export default function ModelConfidence({
  modelComparison,
  agreement,
  finalDomain,
}: ModelConfidenceProps) {
  const models = [
    {
      name: "Keyword model (TF-IDF)",
      prediction: modelComparison.tfidf_svm,
    },
    {
      name: "Meaning model (Sentence-BERT)",
      prediction: modelComparison.sentence_bert_logreg,
    },
    {
      name: "Deep model (DistilBERT)",
      prediction: modelComparison.distilbert,
    },
  ]

  // Calculate consensus: max number of models agreeing on the same category
  const voteCounts: Record<string, number> = {}
  models.forEach((m) => {
    const cat = m.prediction.category
    voteCounts[cat] = (voteCounts[cat] || 0) + 1
  })
  const maxAgreement = Math.max(...Object.values(voteCounts), 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-purple-500" />
          How the models voted
        </CardTitle>
        <CardDescription>
          Multi-architecture model confidence distributions and consensus tracking
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model confidence bars */}
        <div className="space-y-4">
          {models.map((m) => {
            const conf = Math.max(0, Math.min(1, m.prediction.confidence))
            const pct = (conf * 100).toFixed(1)
            const color = CATEGORY_COLORS[m.prediction.category] || DEFAULT_COLOR

            return (
              <div key={m.name} className="space-y-1.5">
                <div className="flex flex-wrap items-center justify-between text-xs gap-1">
                  <span className="font-medium text-foreground">{m.name}</span>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${color.text}`}>
                      {m.prediction.category}
                    </span>
                    <span className="font-mono text-muted-foreground font-semibold">
                      {pct}%
                    </span>
                  </div>
                </div>
                {/* Horizontal progress bar */}
                <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${color.bar}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>

        {/* Consensus Meter */}
        <div className="p-3.5 rounded-lg border bg-card space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-primary" />
              Consensus Meter
            </span>
            <div className="flex items-center gap-1.5 text-xs font-semibold">
              {maxAgreement === 3 ? (
                <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  3 of 3 models agree
                </span>
              ) : maxAgreement === 2 ? (
                <span className="text-amber-600 dark:text-amber-400 flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  2 of 3 models agree
                </span>
              ) : (
                <span className="text-rose-600 dark:text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  1 of 3 models agree
                </span>
              )}
            </div>
          </div>

          {/* 3-segment visual meter */}
          <div className="grid grid-cols-3 gap-2 py-1">
            {[1, 2, 3].map((segIndex) => {
              const isFilled = segIndex <= maxAgreement
              const fillColor =
                maxAgreement === 3
                  ? "bg-emerald-500"
                  : maxAgreement === 2
                  ? "bg-amber-500"
                  : "bg-rose-500"

              return (
                <div
                  key={segIndex}
                  className={`h-2 rounded-full transition-colors duration-300 ${
                    isFilled ? fillColor : "bg-muted border border-border"
                  }`}
                />
              )
            })}
          </div>

          {/* Differing predictions note if not unanimous */}
          {!agreement.unanimous && (
            <p className="text-xs text-muted-foreground pt-1">
              Predictions split across:{" "}
              <span className="font-medium text-foreground">
                {agreement.distinct_predictions.join(", ")}
              </span>
            </p>
          )}
        </div>

        {/* Final Classification callout */}
        <div className="p-3.5 rounded-lg border bg-muted/40 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
              Official Pipeline Output
            </span>
            <span className="text-sm font-bold text-foreground">
              {finalDomain}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground sm:text-right max-w-sm">
            The final answer comes from the hierarchical classifier, which evaluates domain and sub-issue taxonomy and may differ from the individual benchmark votes.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
