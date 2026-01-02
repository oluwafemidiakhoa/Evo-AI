/**
 * API client for Evo-AI backend.
 *
 * Provides type-safe methods for all backend endpoints.
 */

const RAW_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL
const API_BASE_URL =
  RAW_API_BASE_URL?.replace(/\/$/, '') ||
  (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8002')

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new APIError(
      error.error || 'API request failed',
      response.status,
      error.detail
    )
  }

  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

// Campaign API
export const campaignsAPI = {
  async list(page = 1, pageSize = 50, status?: string) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...(status && { status }),
    })
    return fetchAPI<any>(`/api/campaigns?${params}`)
  },

  async get(id: string) {
    return fetchAPI<any>(`/api/campaigns/${id}`)
  },

  async create(data: {
    name: string
    description?: string
    config: Record<string, any>
  }) {
    return fetchAPI<any>('/api/campaigns', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async update(id: string, data: {
    name?: string
    description?: string
    config?: Record<string, any>
  }) {
    return fetchAPI<any>(`/api/campaigns/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async delete(id: string) {
    return fetchAPI<void>(`/api/campaigns/${id}`, {
      method: 'DELETE',
    })
  },

  async start(id: string) {
    return fetchAPI<any>(`/api/campaigns/${id}/start`, {
      method: 'POST',
    })
  },

  async getStats(id: string) {
    return fetchAPI<any>(`/api/campaigns/${id}/stats`)
  },
}

// Rounds API
export const roundsAPI = {
  async list(campaignId: string) {
    return fetchAPI<any[]>(`/api/campaigns/${campaignId}/rounds`)
  },

  async get(campaignId: string, roundNumber: number) {
    return fetchAPI<any>(`/api/campaigns/${campaignId}/rounds/${roundNumber}`)
  },

  async execute(campaignId: string, roundNumber: number) {
    return fetchAPI<any>(
      `/api/campaigns/${campaignId}/rounds/${roundNumber}/execute`,
      { method: 'POST' }
    )
  },

  async getStats(roundId: string) {
    return fetchAPI<any>(`/api/rounds/${roundId}/stats`)
  },
}

// Variants API
export const variantsAPI = {
  async list(params: {
    roundId?: string
    selectedOnly?: boolean
    generation?: number
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params.roundId) searchParams.set('round_id', params.roundId)
    if (params.selectedOnly) searchParams.set('selected_only', 'true')
    if (params.generation) searchParams.set('generation', params.generation.toString())
    if (params.page) searchParams.set('page', params.page.toString())
    if (params.pageSize) searchParams.set('page_size', params.pageSize.toString())

    return fetchAPI<any>(`/api/variants?${searchParams}`)
  },

  async listByRound(roundId: string, selectedOnly?: boolean) {
    return this.list({ roundId, selectedOnly })
  },

  async get(id: string) {
    return fetchAPI<any>(`/api/variants/${id}`)
  },

  async getLineage(id: string) {
    return fetchAPI<any>(`/api/variants/${id}/lineage`)
  },

  async getDescendants(id: string) {
    return fetchAPI<any>(`/api/variants/${id}/descendants`)
  },
}

// Evaluations API
export const evaluationsAPI = {
  async list(params: {
    variantId?: string
    evaluatorType?: string
    status?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params.variantId) searchParams.set('variant_id', params.variantId)
    if (params.evaluatorType) searchParams.set('evaluator_type', params.evaluatorType)
    if (params.status) searchParams.set('status', params.status)
    if (params.page) searchParams.set('page', params.page.toString())
    if (params.pageSize) searchParams.set('page_size', params.pageSize.toString())

    return fetchAPI<any>(`/api/evaluations?${searchParams}`)
  },

  async listByVariant(variantId: string, evaluatorType?: string) {
    return this.list({ variantId, evaluatorType })
  },

  async get(id: string) {
    return fetchAPI<any>(`/api/evaluations/${id}`)
  },
}

// Reports API
export const reportsAPI = {
  async list(params: {
    campaignId?: string
    roundId?: string
    reportType?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params.campaignId) searchParams.set('campaign_id', params.campaignId)
    if (params.roundId) searchParams.set('round_id', params.roundId)
    if (params.reportType) searchParams.set('report_type', params.reportType)
    if (params.page) searchParams.set('page', params.page.toString())
    if (params.pageSize) searchParams.set('page_size', params.pageSize.toString())

    return fetchAPI<any>(`/api/reports?${searchParams}`)
  },

  async get(id: string) {
    return fetchAPI<any>(`/api/reports/${id}`)
  },
}

// Tasks API (Ray)
export const tasksAPI = {
  async executeRound(campaignId: string, roundNumber: number, traceId?: string) {
    return fetchAPI<any>(`/api/tasks/rounds/execute?campaign_id=${campaignId}`, {
      method: 'POST',
      body: JSON.stringify({ round_number: roundNumber, trace_id: traceId }),
    })
  },

  async executeCampaign(campaignId: string, maxRounds?: number, traceId?: string) {
    return fetchAPI<any>(`/api/tasks/campaigns/execute?campaign_id=${campaignId}`, {
      method: 'POST',
      body: JSON.stringify({ max_rounds: maxRounds, trace_id: traceId }),
    })
  },

  async getJob(jobId: string) {
    return fetchAPI<any>(`/api/tasks/${jobId}`)
  },

  async listJobs(params: {
    campaignId?: string
    status?: string
    limit?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params.campaignId) searchParams.set('campaign_id', params.campaignId)
    if (params.status) searchParams.set('status', params.status)
    if (params.limit) searchParams.set('limit', params.limit.toString())

    return fetchAPI<any[]>(`/api/tasks?${searchParams}`)
  },

  async cancelJob(jobId: string) {
    return fetchAPI<any>(`/api/tasks/${jobId}/cancel`, {
      method: 'POST',
    })
  },

  async deleteJob(jobId: string) {
    return fetchAPI<void>(`/api/tasks/${jobId}`, {
      method: 'DELETE',
    })
  },
}

// Health check
export const healthAPI = {
  async check() {
    return fetchAPI<any>('/health')
  },
}
