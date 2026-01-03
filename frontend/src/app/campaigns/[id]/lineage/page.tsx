"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { ArrowLeft, GitBranch } from "lucide-react"

import { campaignsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CampaignLineageGraph } from "@/components/campaign-lineage-graph"

export default function CampaignLineagePage({
  params,
}: {
  params: { id: string }
}) {
  const { id } = params
  const router = useRouter()
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const { data: campaign, error: campaignError } = useSWR(
    ['campaign', id],
    () => campaignsAPI.get(id)
  )

  const { data: lineageData, error: lineageError } = useSWR(
    campaign ? ['campaign-lineage', id] : null,
    () => campaignsAPI.getLineage(id)
  )

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId)
    router.push(`/variants/${nodeId}`)
  }

  if (campaignError || lineageError) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-destructive">
          Failed to load lineage data: {campaignError?.message || lineageError?.message}
        </p>
      </div>
    )
  }

  if (!campaign || !lineageData) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">Loading lineage visualization...</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <Button variant="ghost" asChild className="mb-4">
          <Link href={`/campaigns/${id}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Campaign
          </Link>
        </Button>

        <div className="flex items-center gap-3 mb-4">
          <GitBranch className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              Evolution Lineage
            </h1>
            <p className="text-muted-foreground">
              {campaign.name} - Visualizing {lineageData.total_variants} variants across {lineageData.max_generation + 1} generations
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Variants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{lineageData.total_variants}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Generations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{lineageData.max_generation + 1}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Selected Variants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {lineageData.variants.filter((v: any) => v.is_selected).length}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lineage Graph</CardTitle>
          <CardDescription>
            Click on any node to view variant details. Green nodes indicate selected variants that progressed to the next generation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {lineageData.variants.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No variants yet. Execute the campaign to see the evolution tree.
            </div>
          ) : (
            <CampaignLineageGraph
              variants={lineageData.variants}
              onNodeClick={handleNodeClick}
            />
          )}
        </CardContent>
      </Card>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#22c55e] border-2 border-white"></div>
              <span className="text-sm">Selected (progressed to next generation)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#64748b] border-2 border-white"></div>
              <span className="text-sm">Not selected</span>
            </div>
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Parent-child relationship</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
