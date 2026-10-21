import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, AlertCircle, Shield } from "lucide-react"
import type { LeakCheck, ScopeCheck, Agreement } from "@/lib/api"

interface SafeguardBadgesProps {
  leakCheck?: LeakCheck
  scopeCheck?: ScopeCheck
  agreement?: Agreement
}

const LEAK_TYPE_NAMES: Record<string, string> = {
  PASSWORD: "Password",
  NAME: "Name",
  ADDRESS: "Address",
  ID_NUMBER: "ID Number",
  ACCOUNT: "Account",
  CONTACT: "Contact",
  OTHER: "Other PII",
}

export default function SafeguardBadges({
  leakCheck,
  scopeCheck,
}: SafeguardBadgesProps) {
  // Determine if each badge should render
  const showLeakBadge = Boolean(leakCheck && leakCheck.enabled)
  const showScopeBadge = Boolean(scopeCheck && scopeCheck.enabled)

  // If both badges would be hidden, render nothing at all (not an empty card)
  if (!showLeakBadge && !showScopeBadge) {
    return null
  }

  // Format leak type names for display
  const leakTypeSummary =
    leakCheck?.leak_types && leakCheck.leak_types.length > 0
      ? Array.from(new Set(leakCheck.leak_types.map((t) => LEAK_TYPE_NAMES[t] || t))).join(", ")
      : ""

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Shield className="h-4 w-4 text-primary" />
          Safety checks
        </CardTitle>
        <CardDescription>
          Automated privacy leak verification and financial domain relevance checks
        </CardDescription>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Privacy Double-Check Badge */}
            {showLeakBadge && leakCheck && (
              <div className="p-3 rounded-lg border bg-card space-y-1.5 flex flex-col justify-between">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Privacy Verification
                  </span>
                  {leakCheck.error ? (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge
                          variant="outline"
                          className="bg-muted text-muted-foreground border-border gap-1.5 text-xs py-1 cursor-help"
                        >
                          <AlertCircle className="h-3.5 w-3.5" />
                          Privacy double-check unavailable
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">
                          Privacy audit could not complete: {leakCheck.error}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  ) : leakCheck.leak_count === 0 ? (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge
                          variant="outline"
                          className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 gap-1.5 text-xs py-1 cursor-help"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                          Privacy double-check passed
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">
                          No residual passwords, contact info, or names were found after redaction.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge
                          variant="outline"
                          className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30 gap-1.5 text-xs py-1 font-semibold cursor-help"
                        >
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                          {leakCheck.leak_count} hidden item(s) found and masked
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">
                          Masked residual tokens: {leakTypeSummary || "Sensitive items"}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {leakCheck.error
                    ? "Verification service unavailable; default Presidio rules were applied."
                    : leakCheck.leak_count === 0
                    ? "Verified clean: secondary AI privacy auditor detected no residual PII."
                    : `Secondary audit detected and masked ${leakCheck.leak_count} residual item(s): ${leakTypeSummary}.`}
                </p>
              </div>
            )}

            {/* Scope Check Badge */}
            {showScopeBadge && scopeCheck && (
              <div className="p-3 rounded-lg border bg-card space-y-1.5 flex flex-col justify-between">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Domain Scope
                  </span>
                  {scopeCheck.in_scope ? (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge
                          variant="outline"
                          className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 gap-1.5 text-xs py-1 cursor-help"
                        >
                          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                          Looks like a financial complaint
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">
                          Similarity score {scopeCheck.score.toFixed(3)} exceeds threshold {scopeCheck.threshold.toFixed(3)}.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge
                          variant="outline"
                          className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30 gap-1.5 text-xs py-1 font-semibold cursor-help"
                        >
                          <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />
                          May not be a financial complaint
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">
                          Similarity score {scopeCheck.score.toFixed(3)} is below threshold {scopeCheck.threshold.toFixed(3)}.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {scopeCheck.in_scope
                      ? "Complaint content falls within consumer financial services taxonomy."
                      : "Complaint appears outside the CFPB financial services domain."}
                  </span>
                  <span className="text-[11px] font-mono ml-2 shrink-0">
                    score {scopeCheck.score.toFixed(2)} / {scopeCheck.threshold.toFixed(2)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </TooltipProvider>
      </CardContent>
    </Card>
  )
}
