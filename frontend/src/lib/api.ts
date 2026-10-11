export interface HealthResponse {
  status: string
  models_loaded: boolean
}

export interface OverviewResponse {
  total_complaints: number
  total_categories: number
  total_pii_redacted: number
  live_submissions: number
  pending_review: number
}

export interface CategoryCount {
  category: string
  count: number
}

export interface SubIssueCount {
  sub_issue: string
  count: number
}

export interface TrendItem {
  month: string
  category: string
  count: number
}

export interface EntityBreakdown {
  entity_type: string
  count: number
}

export interface KAnonymityRisk {
  pct_unique: number
  pct_at_risk: number
}

export interface KAnonymityData {
  strategy: string
  baseline: KAnonymityRisk
  mitigated: KAnonymityRisk
}

export interface PrivacyResponse {
  total_redacted: number
  breakdown: EntityBreakdown[]
  k_anonymity: KAnonymityData
}

export interface RecommendationItem {
  category: string
  volume: number
  pct_change: number
  recommendation: string
}

export interface RootCauseItem {
  root_cause: string
  count: number
}

export interface CausalNode {
  id: string
  type?: string | null
}

export interface CausalEdge {
  source: string
  target: string
  weight: number
}

export interface CausalGraphResponse {
  nodes: CausalNode[]
  edges: CausalEdge[]
}

export interface LiveSubmissionRecord {
  complaint_id: string
  timestamp: string
  redacted_text: string
  summary?: string | null
  predicted_category: string
  predicted_sub_issue?: string | null
  domain_confidence: number
  tfidf_prediction?: string | null
  sbert_prediction?: string | null
  distilbert_prediction?: string | null
  needs_review: boolean
  review_reason?: string | null
  num_entities_redacted: number
  resolved: boolean
  [key: string]: any
}

export interface EntityRedacted {
  entity_type: string
  text?: string
  start?: number
  end?: number
  score?: number
}

export interface ModelPrediction {
  category: string
  confidence: number
}

export interface ModelComparison {
  tfidf_svm: ModelPrediction
  sentence_bert_logreg: ModelPrediction
  distilbert: ModelPrediction
}

export interface Agreement {
  unanimous: boolean
  distinct_predictions: string[]
  average_confidence: number
  needs_review: boolean
  review_reason: string | null
}

export interface FinalClassification {
  domain: string
  sub_issue: string
  domain_confidence: number
  sub_issue_confidence: number
}

export interface ProcessComplaintResponse {
  complaint_id: string
  timestamp: string
  redacted_text: string
  summary: string
  entities_redacted: EntityRedacted[]
  model_comparison: ModelComparison
  agreement: Agreement
  final_classification: FinalClassification
}

export interface ResolveResponse {
  status: string
  complaint_id: string
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    let errorDetail = res.statusText
    try {
      const errJson = await res.json()
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(`API Error ${res.status}: ${errorDetail}`)
  }
  return res.json()
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/api/health")
}

export async function getOverview(): Promise<OverviewResponse> {
  return fetchJson<OverviewResponse>("/api/overview")
}

export async function getCategories(): Promise<CategoryCount[]> {
  return fetchJson<CategoryCount[]>("/api/categories")
}

export async function getSubIssues(category: string): Promise<SubIssueCount[]> {
  return fetchJson<SubIssueCount[]>(`/api/sub-issues?category=${encodeURIComponent(category)}`)
}

export async function getTrend(): Promise<TrendItem[]> {
  return fetchJson<TrendItem[]>("/api/trend")
}

export async function getPrivacy(): Promise<PrivacyResponse> {
  return fetchJson<PrivacyResponse>("/api/privacy")
}

export async function getRecommendations(): Promise<RecommendationItem[]> {
  return fetchJson<RecommendationItem[]>("/api/recommendations")
}

export async function getRootCauses(): Promise<RootCauseItem[]> {
  return fetchJson<RootCauseItem[]>("/api/causal/root-causes")
}

export async function getCausalGraph(): Promise<CausalGraphResponse> {
  return fetchJson<CausalGraphResponse>("/api/causal/graph")
}

export async function getSubmissions(limit: number = 20): Promise<LiveSubmissionRecord[]> {
  return fetchJson<LiveSubmissionRecord[]>(`/api/submissions?limit=${limit}`)
}

export async function submitComplaint(text: string): Promise<ProcessComplaintResponse> {
  return fetchJson<ProcessComplaintResponse>("/api/complaints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
}

export async function getReviewQueue(): Promise<LiveSubmissionRecord[]> {
  return fetchJson<LiveSubmissionRecord[]>("/api/review-queue")
}

export async function resolveReviewItem(complaintId: string): Promise<ResolveResponse> {
  return fetchJson<ResolveResponse>(`/api/review-queue/${encodeURIComponent(complaintId)}/resolve`, {
    method: "POST",
  })
}
