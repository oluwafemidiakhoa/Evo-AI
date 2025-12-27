"use client"

import { use } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { ArrowLeft, GitBranch, TrendingUp, Filter } from "lucide-react"

import { campaignsAPI, variantsAPI, roundsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { CampaignLineageGraph } from "@/components/campaign-lineage-graph"
import type { Variant } from "@/types"

export default function CampaignLineagePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()

  const { data: campaign, isLoading: campaignLoading } = useSWR(
    ["campaign", id],
    () => campaignsAPI.get(id)
  )

  const { data: rounds } = useSWR(
    ["rounds", id],
    () => roundsAPI.list(id)
  )

  const { data: stats } = useSWR(
    ["campaign-stats", id],
    () => campaignsAPI.getStats(id)
  )

  // Fetch all variants for the campaign
  const { data: variantsData, isLoading: variantsLoading } = useSWR(
    ["campaign-variants", id],
    async () => {
      if (!rounds) return []
      const allVariants: Variant[] = []
      for (const round of rounds) {
        const roundVariants = await variantsAPI.listByRound(round.id)
        allVariants.push(...roundVariants)
      }
      return allVariants
    }
  )

  const handleNodeClick = (nodeId: string) => {
    router.push(`/variants/${nodeId}`)
  }

  if (campaignLoading || variantsLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Campaign Not Found</h1>
          <Button asChild>
            <Link href="/campaigns">Back to Campaigns</Link>
          </Button>
        </div>
      </div>
    )
  }

  const variants: Variant[] = variantsData || []
  const selectedVariants = variants.filter(v => v.is_selected)
  const maxGeneration = Math.max(...variants.map(v => v.generation), 0)

  // Group variants by generation
  const byGeneration = variants.reduce((acc, v) => {
    if (!acc[v.generation]) acc[v.generation] = []
    acc[v.generation].push(v)
    return acc
  }, {} as Record<number, Variant[]>)

  // Count mutation types
  const mutationCounts = variants.reduce((acc, v) => {
    if (v.mutation_type) {
      acc[v.mutation_type] = (acc[v.mutation_type] || 0) + 1
    }
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <Button variant="ghost" asChild className="mb-4">
        <Link href={`/campaigns/${id}`}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Campaign
        </Link>
      </Button>

      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <GitBranch className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Campaign Lineage</h1>
        </div>
        <p className="text-muted-foreground">
          {campaign.name} - Complete evolutionary history
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Variants
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{variants.length}</div>
            <p className="text-xs text-muted-foreground">
              Across {stats?.total_rounds || 0} rounds
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Selected Variants
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{selectedVariants.length}</div>
            <p className="text-xs text-muted-foreground">
              {variants.length > 0
                ? `${((selectedVariants.length / variants.length) * 100).toFixed(1)}% selection rate`
                : "No variants"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Max Generation
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{maxGeneration}</div>
            <p className="text-xs text-muted-foreground">
              Evolution depth
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Mutation Types
            </CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(mutationCounts).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Distinct strategies
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Mutation Type Distribution */}
      {Object.keys(mutationCounts).length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Mutation Strategy Distribution</CardTitle>
            <CardDescription>
              Frequency of each mutation type across all variants
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-5">
              {Object.entries(mutationCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <Badge variant="secondary" className="capitalize mb-1">
                        {type}
                      </Badge>
                      <div className="text-xs text-muted-foreground">
                        {((count / variants.length) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                    <div className="text-2xl font-bold">{count}</div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Generation Distribution */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Generation Distribution</CardTitle>
          <CardDescription>
            Number of variants per generation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(byGeneration)
              .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
              .map(([gen, vars]) => {
                const selectedCount = vars.filter(v => v.is_selected).length
                const percentage = (vars.length / variants.length) * 100

                return (
                  <div key={gen} className="flex items-center gap-4">
                    <div className="min-w-[100px]">
                      <Badge variant="outline">Generation {gen}</Badge>
                    </div>
                    <div className="flex-1">
                      <div className="h-8 bg-muted rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-primary/70 flex items-center justify-end pr-2"
                          style={{ width: `${percentage}%` }}
                        >
                          {percentage > 10 && (
                            <span className="text-xs font-medium text-white">
                              {vars.length}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="min-w-[120px] text-sm text-muted-foreground text-right">
                      {vars.length} total, {selectedCount} selected
                    </div>
                  </div>
                )
              })}
          </div>
        </CardContent>
      </Card>

      {/* Lineage Graph Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Evolution Graph</CardTitle>
          <CardDescription>
            Visual representation of variant evolution (click nodes to view details)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {variants.length > 0 ? (
            <CampaignLineageGraph
              variants={variants.map(v => ({
                id: v.id,
                generation: v.generation,
                mutation_type: v.mutation_type,
                is_selected: v.is_selected,
                round_id: v.round_id
              }))}
              onNodeClick={handleNodeClick}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No variants generated yet</p>
              <p className="text-sm mt-2">Execute rounds to see the evolution graph</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="mt-6 flex gap-4">
        <Button asChild>
          <Link href={`/campaigns/${id}`}>
            View Campaign Details
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/variants">
            Browse All Variants
          </Link>
        </Button>
      </div>
    </div>
  )
}
