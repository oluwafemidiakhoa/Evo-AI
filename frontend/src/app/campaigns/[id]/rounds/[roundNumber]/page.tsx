"use client"

import { use, useState } from "react"
import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, CheckCircle, XCircle, Clock, TrendingUp } from "lucide-react"

import { campaignsAPI, roundsAPI, variantsAPI, evaluationsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, formatScore, getStatusColor, truncate } from "@/lib/utils"
import type { Round, Variant, Evaluation, RoundStats } from "@/types"

export default function RoundDetailPage({
  params,
}: {
  params: Promise<{ id: string; roundNumber: string }>
}) {
  const { id: campaignId, roundNumber } = use(params)
  const roundNum = parseInt(roundNumber)

  const { data: campaign } = useSWR(["campaign", campaignId], () =>
    campaignsAPI.get(campaignId)
  )

  const { data: rounds } = useSWR(["rounds", campaignId], () =>
    roundsAPI.list(campaignId)
  )

  const round = rounds?.find((r: Round) => r.round_number === roundNum)

  const { data: stats } = useSWR(
    round ? ["round-stats", round.id] : null,
    () => roundsAPI.getStats(round!.id)
  )

  const { data: variants, isLoading: variantsLoading } = useSWR(
    round ? ["variants", round.id] : null,
    () => variantsAPI.listByRound(round!.id)
  )

  const [selectedVariant, setSelectedVariant] = useState<string | null>(null)

  const { data: evaluations } = useSWR(
    selectedVariant ? ["evaluations", selectedVariant] : null,
    () => evaluationsAPI.listByVariant(selectedVariant!)
  )

  if (!round) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  const statsData: RoundStats | undefined = stats

  return (
    <div className="container mx-auto py-8">
      <Button variant="ghost" asChild className="mb-4">
        <Link href={`/campaigns/${campaignId}`}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Campaign
        </Link>
      </Button>

      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Round {round.round_number}
            </h1>
            <p className="text-muted-foreground">
              {campaign?.name || "Campaign"}
            </p>
          </div>
          <Badge className={getStatusColor(round.status)}>
            {round.status}
          </Badge>
        </div>
      </div>

      {/* Round Statistics */}
      <div className="grid gap-6 md:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Variants
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.total_variants || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Selected Variants
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.selected_variants || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsData?.total_variants
                ? `${((statsData.selected_variants / statsData.total_variants) * 100).toFixed(1)}% selection rate`
                : ""}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Average Score
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {statsData?.average_score !== null
                ? formatScore(statsData.average_score)
                : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              {statsData?.min_score !== null && statsData?.max_score !== null
                ? `Range: ${formatScore(statsData.min_score)} - ${formatScore(statsData.max_score)}`
                : ""}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {round.started_at && round.completed_at
                ? `${Math.round((new Date(round.completed_at).getTime() - new Date(round.started_at).getTime()) / 1000)}s`
                : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              {round.started_at ? formatDate(round.started_at) : "Not started"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Variants Table */}
      <Card>
        <CardHeader>
          <CardTitle>Variants</CardTitle>
          <CardDescription>
            All variants generated in this round
          </CardDescription>
        </CardHeader>
        <CardContent>
          {variantsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : variants && variants.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Generation</TableHead>
                  <TableHead>Content Preview</TableHead>
                  <TableHead>Mutation Type</TableHead>
                  <TableHead>Selected</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {variants.map((variant: Variant) => (
                  <TableRow
                    key={variant.id}
                    className={
                      selectedVariant === variant.id ? "bg-muted" : ""
                    }
                  >
                    <TableCell className="font-medium">
                      {variant.generation}
                    </TableCell>
                    <TableCell className="max-w-md">
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {truncate(variant.content, 100)}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {variant.mutation_type || "initial"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {variant.is_selected ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-gray-400" />
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(variant.created_at)}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setSelectedVariant(
                            selectedVariant === variant.id
                              ? null
                              : variant.id
                          )
                        }
                      >
                        {selectedVariant === variant.id
                          ? "Hide Evaluations"
                          : "View Evaluations"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No variants generated yet
            </div>
          )}
        </CardContent>
      </Card>

      {/* Evaluations Panel */}
      {selectedVariant && evaluations && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Evaluations</CardTitle>
            <CardDescription>
              Evaluation results for selected variant
            </CardDescription>
          </CardHeader>
          <CardContent>
            {evaluations.length > 0 ? (
              <div className="space-y-4">
                {evaluations.map((evaluation: Evaluation) => (
                  <div
                    key={evaluation.id}
                    className="border rounded-lg p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {evaluation.evaluator_type}
                        </Badge>
                        <Badge className={getStatusColor(evaluation.status)}>
                          {evaluation.status}
                        </Badge>
                      </div>
                      {evaluation.score !== null && (
                        <div className="text-2xl font-bold">
                          {formatScore(evaluation.score)}
                        </div>
                      )}
                    </div>
                    {evaluation.result_data &&
                      Object.keys(evaluation.result_data).length > 0 && (
                        <div className="mt-2">
                          <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                            {JSON.stringify(evaluation.result_data, null, 2)}
                          </pre>
                        </div>
                      )}
                    <div className="text-xs text-muted-foreground">
                      Created: {formatDate(evaluation.created_at)}
                      {evaluation.completed_at &&
                        ` | Completed: ${formatDate(evaluation.completed_at)}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No evaluations found for this variant
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
