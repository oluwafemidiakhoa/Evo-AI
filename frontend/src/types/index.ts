/**
 * TypeScript types for Evo-AI platform.
 */

export interface Campaign {
  id: string
  name: string
  description: string | null
  status: 'draft' | 'active' | 'paused' | 'completed' | 'failed'
  config: Record<string, any>
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface Round {
  id: string
  campaign_id: string
  round_number: number
  status:
    | 'pending'
    | 'planning'
    | 'generating'
    | 'evaluating'
    | 'selecting'
    | 'reporting'
    | 'completed'
    | 'failed'
  config: Record<string, any>
  started_at: string | null
  completed_at: string | null
}

export interface Variant {
  id: string
  round_id: string
  parent_id: string | null
  generation: number
  content: string
  content_hash: string
  mutation_type: string | null
  is_selected: boolean
  created_at: string
}

export interface Evaluation {
  id: string
  variant_id: string
  evaluator_type: string
  score: number | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  result_data: Record<string, any>
  created_at: string
  completed_at: string | null
}

export interface Report {
  id: string
  campaign_id: string
  round_id: string | null
  report_type: string
  format?: string
  content: any
  metadata: Record<string, any>
  created_at: string
}

export interface Job {
  job_id: string
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  campaign_id: string | null
  round_number: number | null
  progress: number
  result: Record<string, any> | null
  error: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
}

export interface CampaignStats {
  campaign_id: string
  total_rounds: number
  completed_rounds: number
  total_variants: number
  total_selected: number
  max_generation: number
  selection_rate: number
}

export interface RoundStats {
  round_id: string
  round_number: number
  total_variants: number
  selected_variants: number
  average_score: number | null
  min_score: number | null
  max_score: number | null
}

export interface Lineage {
  variant_id: string
  lineage: Array<{
    id: string
    generation: number
    mutation_type: string | null
    [key: string]: any
  }>
  generations: number
  founder: Record<string, any> | null
}
