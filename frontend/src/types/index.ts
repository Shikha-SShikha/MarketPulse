// Signal types
export type EventType =
  | 'announcement'
  | 'hire'
  | 'policy'
  | 'partnership'
  | 'm&a'
  | 'retraction'
  | 'launch'
  | 'other';

export type Confidence = 'Low' | 'Medium' | 'High';

export type ImpactArea = 'Ops' | 'Tech' | 'Integrity' | 'Procurement';

export type SignalStatus = 'pending_review' | 'approved' | 'rejected';

export type SourceType = 'rss' | 'linkedin' | 'web' | 'email';

export interface Signal {
  id: string;
  entity: string;
  event_type: string;
  topic: string;
  source_url: string;
  evidence_snippet: string;
  confidence: string;
  impact_areas: string[];
  entity_tags: string[];
  created_at: string;
  curator_name: string | null;
  notes: string | null;
  // Automation fields
  status: string;
  data_source_id: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  // Entity relationships (populated when requested)
  entities?: Entity[];
}

export interface SignalCreate {
  entity: string;
  event_type: EventType;
  topic: string;
  source_url: string;
  evidence_snippet: string;
  confidence: Confidence;
  impact_areas: ImpactArea[];
  entity_tags?: string[];
  notes?: string;
}

export interface SignalListResponse {
  signals: Signal[];
  total: number;
  limit: number;
  offset: number;
}

// Semantic Search types
export interface SemanticSearchResult {
  signal: Signal;
  similarity_score: number;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total: number;
}

// Theme types
export interface Theme {
  id: string;
  title: string;
  key_players: string[];
  aggregate_confidence: string;
  impact_areas: string[];
  so_what: string;
  now_what: string[];
  created_at: string;
  signals: Signal[];
}

// Weekly Brief types
export interface WeeklyBrief {
  id: string;
  week_start: string;
  week_end: string;
  generated_at: string;
  total_signals: number;
  coverage_areas: string[];
  themes: Theme[];
}

// API Error type
export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}

// Data Source types
export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  url: string | null;
  config: Record<string, any> | null;
  enabled: boolean;
  last_fetched_at: string | null;
  last_success_at: string | null;
  error_count: number;
  last_error: string | null;
  default_confidence: string;
  default_impact_areas: string[];
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreate {
  name: string;
  source_type: SourceType;
  url?: string;
  config?: Record<string, any>;
  enabled?: boolean;
  default_confidence?: Confidence;
  default_impact_areas?: ImpactArea[];
}

export interface DataSourceUpdate {
  name?: string;
  url?: string;
  config?: Record<string, any>;
  enabled?: boolean;
  default_confidence?: Confidence;
  default_impact_areas?: ImpactArea[];
}

// Notification types
export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  link: string | null;
  read: boolean;
  dismissed: boolean;
  created_at: string;
}

export interface SignalStatusUpdate {
  status: SignalStatus;
  reviewer_name?: string;
}

export interface CollectSignalsResponse {
  message: string;
  signals_collected: number;
  signals_pending_review: number;
  sources_processed: number;
  errors: string[];
}

// Entity types
export type EntitySegment = 'customer' | 'competitor' | 'industry' | 'influencer';

export interface Entity {
  id: string;
  name: string;
  segment: string;
  aliases: string[];
  entity_metadata: Record<string, any> | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntityCreate {
  name: string;
  segment: EntitySegment;
  aliases?: string[];
  entity_metadata?: Record<string, any>;
  notes?: string;
}

export interface EntityUpdate {
  name?: string;
  segment?: EntitySegment;
  aliases?: string[];
  entity_metadata?: Record<string, any>;
  notes?: string;
}

export interface EntityListResponse {
  entities: Entity[];
  total: number;
}

// Segment Statistics types
export interface SegmentStats {
  segment: string;
  signal_count: number;
  entity_count: number;
  recent_signals: number;
}

export interface SegmentStatsResponse {
  stats: SegmentStats[];
  total_signals: number;
}

// Signal Summary types
export interface SignalSummaryItem {
  insight: string;
  signal_ids: string[];
  entities: string[];
}

export interface SignalSummary {
  summary: string;
  key_insights: SignalSummaryItem[];
  total_signals: number;
  date_range: string;
  segments_covered: string[];
  impact_areas: string[];
}
