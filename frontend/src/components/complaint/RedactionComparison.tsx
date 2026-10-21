import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldCheck, Eye, EyeOff } from "lucide-react"
import type { EntityRedacted } from "@/lib/api"
import { buildSegments } from "@/lib/highlight"

interface RedactionComparisonProps {
  submittedText: string
  entities: EntityRedacted[]
  redactedText: string
}

interface EntityStyle {
  label: string
  bg: string
  border: string
  text: string
  badgeBg: string
  badgeText: string
}

const ENTITY_CONFIG: Record<string, EntityStyle> = {
  PERSON: {
    label: "Person",
    bg: "bg-blue-100/80 dark:bg-blue-950/60",
    border: "border-blue-300 dark:border-blue-700",
    text: "text-blue-900 dark:text-blue-100",
    badgeBg: "bg-blue-200 dark:bg-blue-900",
    badgeText: "text-blue-800 dark:text-blue-200",
  },
  EMAIL_ADDRESS: {
    label: "Email",
    bg: "bg-violet-100/80 dark:bg-violet-950/60",
    border: "border-violet-300 dark:border-violet-700",
    text: "text-violet-900 dark:text-violet-100",
    badgeBg: "bg-violet-200 dark:bg-violet-900",
    badgeText: "text-violet-800 dark:text-violet-200",
  },
  PHONE_NUMBER: {
    label: "Phone",
    bg: "bg-emerald-100/80 dark:bg-emerald-950/60",
    border: "border-emerald-300 dark:border-emerald-700",
    text: "text-emerald-900 dark:text-emerald-100",
    badgeBg: "bg-emerald-200 dark:bg-emerald-900",
    badgeText: "text-emerald-800 dark:text-emerald-200",
  },
  ACCOUNT_NUMBER: {
    label: "Account",
    bg: "bg-amber-100/80 dark:bg-amber-950/60",
    border: "border-amber-300 dark:border-amber-700",
    text: "text-amber-900 dark:text-amber-100",
    badgeBg: "bg-amber-200 dark:bg-amber-900",
    badgeText: "text-amber-800 dark:text-amber-200",
  },
  AADHAAR_NUMBER: {
    label: "Aadhaar",
    bg: "bg-rose-100/80 dark:bg-rose-950/60",
    border: "border-rose-300 dark:border-rose-700",
    text: "text-rose-900 dark:text-rose-100",
    badgeBg: "bg-rose-200 dark:bg-rose-900",
    badgeText: "text-rose-800 dark:text-rose-200",
  },
  COMPLAINT_ID: {
    label: "Complaint ID",
    bg: "bg-teal-100/80 dark:bg-teal-950/60",
    border: "border-teal-300 dark:border-teal-700",
    text: "text-teal-900 dark:text-teal-100",
    badgeBg: "bg-teal-200 dark:bg-teal-900",
    badgeText: "text-teal-800 dark:text-teal-200",
  },
  CREDIT_CARD: {
    label: "Card",
    bg: "bg-orange-100/80 dark:bg-orange-950/60",
    border: "border-orange-300 dark:border-orange-700",
    text: "text-orange-900 dark:text-orange-100",
    badgeBg: "bg-orange-200 dark:bg-orange-900",
    badgeText: "text-orange-800 dark:text-orange-200",
  },
  CREDENTIAL: {
    label: "Credential",
    bg: "bg-red-100/80 dark:bg-red-950/60",
    border: "border-red-300 dark:border-red-700",
    text: "text-red-900 dark:text-red-100",
    badgeBg: "bg-red-200 dark:bg-red-900",
    badgeText: "text-red-800 dark:text-red-200",
  },
}

const DEFAULT_STYLE: EntityStyle = {
  label: "Sensitive",
  bg: "bg-gray-100 dark:bg-gray-800/80",
  border: "border-gray-300 dark:border-gray-600",
  text: "text-gray-900 dark:text-gray-100",
  badgeBg: "bg-gray-200 dark:bg-gray-700",
  badgeText: "text-gray-800 dark:text-gray-200",
}

function renderRedacted(text: string) {
  const parts = text.split(/(\[[A-Za-z0-9_ -]+\])/)
  return parts.map((part, i) => {
    if (part.startsWith("[") && part.endsWith("]")) {
      return (
        <span
          key={i}
          className="inline-block px-1.5 py-0.5 mx-0.5 rounded text-[11px] font-mono bg-muted text-muted-foreground border border-border font-medium"
        >
          {part}
        </span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export default function RedactionComparison({
  submittedText,
  entities,
  redactedText,
}: RedactionComparisonProps) {
  const segments = buildSegments(submittedText, entities)

  // Tally counts of present entity types
  const typeCounts: Record<string, number> = {}
  for (const ent of entities) {
    typeCounts[ent.entity_type] = (typeCounts[ent.entity_type] || 0) + 1
  }
  const presentTypes = Object.entries(typeCounts)
  const totalHidden = entities.length

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              What we protected
            </CardTitle>
            <CardDescription>
              Side-by-side verification of client-side inputs versus system-visible redacted text
            </CardDescription>
          </div>
          {totalHidden > 0 ? (
            <div className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 w-fit">
              {totalHidden} sensitive {totalHidden === 1 ? "item" : "items"} hidden
            </div>
          ) : (
            <div className="text-xs font-medium px-2.5 py-1 rounded-full bg-muted text-muted-foreground border border-border w-fit">
              No sensitive items detected
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Two-column side-by-side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left Column: Your complaint */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Eye className="h-3.5 w-3.5" />
              Your complaint
            </div>
            <div className="p-3.5 rounded-md bg-muted/30 border text-xs font-mono leading-relaxed min-h-[140px] whitespace-pre-wrap">
              {segments.length > 0 ? (
                segments.map((seg, idx) => {
                  if (seg.entityType) {
                    const style = ENTITY_CONFIG[seg.entityType] || DEFAULT_STYLE
                    return (
                      <mark
                        key={idx}
                        className={`inline-flex items-baseline px-1.5 py-0.5 mx-0.5 rounded border text-xs font-mono font-medium ${style.bg} ${style.border} ${style.text}`}
                      >
                        <span>{seg.text}</span>
                        <span
                          className={`ml-1 text-[9px] font-sans font-semibold uppercase px-1 py-0.5 rounded ${style.badgeBg} ${style.badgeText}`}
                        >
                          {style.label}
                        </span>
                      </mark>
                    )
                  }
                  return <span key={idx}>{seg.text}</span>
                })
              ) : (
                <span className="text-muted-foreground italic">No text submitted</span>
              )}
            </div>
          </div>

          {/* Right Column: What the system sees */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <EyeOff className="h-3.5 w-3.5 text-emerald-500" />
              What the system sees
            </div>
            <div className="p-3.5 rounded-md bg-muted/60 border text-xs font-mono leading-relaxed min-h-[140px] whitespace-pre-wrap">
              {renderRedacted(redactedText)}
            </div>
          </div>
        </div>

        {/* Legend of present entity types */}
        {presentTypes.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mr-1">
              Protected types:
            </span>
            {presentTypes.map(([type, count]) => {
              const style = ENTITY_CONFIG[type] || DEFAULT_STYLE
              return (
                <span
                  key={type}
                  className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[11px] font-medium ${style.bg} ${style.border} ${style.text}`}
                >
                  <span className="font-semibold">{style.label}</span>
                  <span
                    className={`px-1 rounded-full text-[10px] font-bold ${style.badgeBg} ${style.badgeText}`}
                  >
                    {count}
                  </span>
                </span>
              )
            })}
          </div>
        )}

        {/* Browser-only privacy notice */}
        <p className="text-[11px] text-muted-foreground italic">
          Highlighting happens in your browser. Your original text is never stored or sent back.
        </p>
      </CardContent>
    </Card>
  )
}
