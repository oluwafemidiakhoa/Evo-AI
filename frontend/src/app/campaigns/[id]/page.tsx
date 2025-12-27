"use client"

import { useState } from "react"
import { use } from "react"
import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, Play, Pause, BarChart3, GitBranch, FileText } from "lucide-react"

import { campaignsAPI, roundsAPI, tasksAPI, reportsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatDate, formatScore, getStatusColor } from "@/lib/utils"

export default function CampaignDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const [executingRound, setExecutingRound] = useState<number | null>(null)

  const { data: campaign, error: campaignError, mutate: mutateCampaign } = useSWR(
    ['campaign', id],
    () => campaignsAPI.get(id)
  )

  const { data: rounds, error: roundsError, mutate: mutateRounds } = useSWR(
    campaign ? ['rounds', id] : null,
    () => roundsAPI.list(id)
  )

  const { data: stats } = useSWR(
    campaign ? ['campaign-stats', id] : null,
    () => campaignsAPI.getStats(id)
  )

  const { data: reports } = useSWR(
    campaign ? ['reports', id] : null,
    () => reportsAPI.list({ campaignId: id, pageSize: 5 })
  )

  const handleStartCampaign = async () => {
    try {
      await campaignsAPI.start(id)
      mutateCampaign()
    } catch (error: any) {
      alert(`Failed to start campaign: ${error.message}`)
    }
  }

  const handleExecuteRound = async (roundNumber: number) => {
    setExecutingRound(roundNumber)
    try {
      const job = await tasksAPI.executeRound(id, roundNumber)
      alert(`Round ${roundNumber} queued. Job ID: ${job.job_id}`)

      // Poll for completion
      const pollInterval = setInterval(async () => {
        const status = await tasksAPI.getJob(job.job_id)
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          setExecutingRound(null)
          mutateRounds()
          if (status.status === 'failed') {
            alert(`Round ${roundNumber} failed: ${status.error}`)
          }
        }
      }, 2000)
    } catch (error: any) {
      alert(`Failed to execute round: ${error.message}`)
      setExecutingRound(null)
    }
  }

  if (campaignError) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-destructive">Failed to load campaign: {campaignError.message}</p>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <Button variant="ghost" asChild className="mb-4">
          <Link href="/campaigns">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Campaigns
          </Link>
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              {campaign.name}
            </h1>
            {campaign.description && (
              <p className="text-muted-foreground">{campaign.description}</p>
            )}
          </div>
          <Badge className={getStatusColor(campaign.status)}>
            {campaign.status}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Rounds
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.completed_rounds || 0} / {campaign.config.max_rounds || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Variants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_variants || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Max Generation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.max_generation || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Selection Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats ? formatScore(stats.selection_rate) : 'N/A'}
            </div>
          </CardContent>
        </Card>
      </div>

      {stats && stats.total_variants > 0 && (
        <Card className="mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <GitBranch className="h-8 w-8 text-blue-600" />
                <div>
                  <h3 className="font-semibold text-lg">Explore Evolution Tree</h3>
                  <p className="text-sm text-muted-foreground">
                    Visualize the complete lineage across all {stats.total_variants} variants
                  </p>
                </div>
              </div>
              <Button asChild>
                <Link href={`/campaigns/${id}/lineage`}>
                  <GitBranch className="mr-2 h-4 w-4" />
                  View Lineage
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Max Rounds</dt>
              <dd className="text-lg">{campaign.config.max_rounds}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                Variants per Round
              </dt>
              <dd className="text-lg">{campaign.config.variants_per_round}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Evaluators</dt>
              <dd className="text-lg">
                {campaign.config.evaluators?.join(', ') || 'None'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Created</dt>
              <dd className="text-lg">{formatDate(campaign.created_at)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {campaign.status === 'pending' && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Start Campaign</CardTitle>
            <CardDescription>
              Campaign is ready to start. Click below to begin execution.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleStartCampaign}>
              <Play className="mr-2 h-4 w-4" />
              Start Campaign
            </Button>
          </CardContent>
        </Card>
      )}

      {reports && reports.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Reports</CardTitle>
                <CardDescription>
                  Generated analysis and insights
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link href="/reports">
                  <FileText className="mr-2 h-4 w-4" />
                  View All
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {reports.slice(0, 5).map((report: any) => (
                <Link
                  key={report.id}
                  href={`/reports/${report.id}`}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm capitalize">
                      {report.report_type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(report.created_at)}
                  </span>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Rounds</CardTitle>
            {campaign.status === 'in_progress' && (
              <Button size="sm" variant="outline">
                <Play className="mr-2 h-4 w-4" />
                Execute Next Round
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {roundsError ? (
            <p className="text-destructive">Failed to load rounds</p>
          ) : !rounds ? (
            <p className="text-muted-foreground">Loading rounds...</p>
          ) : rounds.length === 0 ? (
            <p className="text-muted-foreground">No rounds yet</p>
          ) : (
            <div className="space-y-4">
              {rounds.map((round: any) => (
                <div
                  key={round.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-2xl font-bold text-muted-foreground">
                      #{round.round_number}
                    </div>
                    <div>
                      <div className="font-medium">Round {round.round_number}</div>
                      <div className="text-sm text-muted-foreground">
                        {round.started_at
                          ? `Started ${formatDate(round.started_at)}`
                          : 'Not started'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(round.status)}>
                      {round.status}
                    </Badge>
                    {round.status === 'pending' && (
                      <Button
                        size="sm"
                        onClick={() => handleExecuteRound(round.round_number)}
                        disabled={executingRound === round.round_number}
                      >
                        {executingRound === round.round_number ? (
                          <>Executing...</>
                        ) : (
                          <>
                            <Play className="mr-2 h-3 w-3" />
                            Execute
                          </>
                        )}
                      </Button>
                    )}
                    {round.status === 'completed' && (
                      <Button size="sm" variant="outline" asChild>
                        <Link href={`/campaigns/${id}/rounds/${round.round_number}`}>
                          <BarChart3 className="mr-2 h-3 w-3" />
                          View Details
                        </Link>
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
