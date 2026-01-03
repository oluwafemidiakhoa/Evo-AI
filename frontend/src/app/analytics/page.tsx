"use client"

import { useState } from "react"
import Link from "next/link"
import useSWR from "swr"
import { BarChart3, TrendingUp, Activity, Zap } from "lucide-react"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

import { campaignsAPI, variantsAPI } from "@/lib/api/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { getStatusColor } from "@/lib/utils"
import type { Campaign, Variant } from "@/types"

export default function AnalyticsPage() {
  const [_selectedCampaign, _setSelectedCampaign] = useState<string | null>(null)

  const { data: campaignsData, isLoading: campaignsLoading } = useSWR(
    ["campaigns", 1, 100],
    () => campaignsAPI.list(1, 100)
  )

  const { data: variantsData } = useSWR(
    ["variants-analytics"],
    () => variantsAPI.list({ page: 1, pageSize: 1000 })
  )

  const campaigns: Campaign[] = campaignsData?.campaigns || []
  const allVariants: Variant[] = variantsData?.variants || []

  // Calculate overall statistics
  const totalCampaigns = campaigns.length
  const activeCampaigns = campaigns.filter((c) => c.status === "active").length
  const completedCampaigns = campaigns.filter((c) => c.status === "completed").length
  const totalVariants = allVariants.length
  const selectedVariants = allVariants.filter((v) => v.is_selected).length

  // Campaign status distribution
  const statusData = [
    { name: "Draft", value: campaigns.filter((c) => c.status === "draft").length, color: "#94a3b8" },
    { name: "Active", value: activeCampaigns, color: "#3b82f6" },
    { name: "Paused", value: campaigns.filter((c) => c.status === "paused").length, color: "#eab308" },
    { name: "Completed", value: completedCampaigns, color: "#22c55e" },
    { name: "Failed", value: campaigns.filter((c) => c.status === "failed").length, color: "#ef4444" },
  ].filter((d) => d.value > 0)

  // Variants by generation
  const generationData = allVariants.reduce((acc, v) => {
    const gen = `Gen ${v.generation}`
    const existing = acc.find((d) => d.generation === gen)
    if (existing) {
      existing.total += 1
      if (v.is_selected) existing.selected += 1
    } else {
      acc.push({
        generation: gen,
        total: 1,
        selected: v.is_selected ? 1 : 0,
      })
    }
    return acc
  }, [] as Array<{ generation: string; total: number; selected: number }>)

  // Mutation type distribution
  const mutationData = allVariants.reduce((acc, v) => {
    if (v.mutation_type) {
      const existing = acc.find((d) => d.type === v.mutation_type)
      if (existing) {
        existing.count += 1
      } else {
        acc.push({ type: v.mutation_type, count: 1 })
      }
    }
    return acc
  }, [] as Array<{ type: string; count: number }>)

  // Selection rate by generation
  const selectionRateData = generationData.map((d) => ({
    generation: d.generation,
    rate: d.total > 0 ? (d.selected / d.total) * 100 : 0,
  }))

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
        <p className="text-muted-foreground">
          Insights and visualizations across all campaigns
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-6 md:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Campaigns
            </CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCampaigns}</div>
            <p className="text-xs text-muted-foreground">
              {activeCampaigns} active, {completedCampaigns} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Variants
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalVariants}</div>
            <p className="text-xs text-muted-foreground">
              Across all campaigns
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Selection Rate
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalVariants > 0
                ? `${((selectedVariants / totalVariants) * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              {selectedVariants} / {totalVariants} variants
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Max Generation
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allVariants.length > 0
                ? Math.max(...allVariants.map((v) => v.generation))
                : 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Evolution depth
            </p>
          </CardContent>
        </Card>
      </div>

      {campaignsLoading ? (
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      ) : campaigns.length === 0 ? (
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="text-center py-12 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="mb-2">No campaigns yet</p>
              <p className="text-sm mb-4">
                Create a campaign to see analytics
              </p>
              <Button asChild>
                <Link href="/campaigns/new">Create Campaign</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Charts Row 1 */}
          <div className="grid gap-6 md:grid-cols-2 mb-8">
            {/* Campaign Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Campaign Status Distribution</CardTitle>
                <CardDescription>
                  Current state of all campaigns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name}: ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Variants by Generation */}
            <Card>
              <CardHeader>
                <CardTitle>Variants by Generation</CardTitle>
                <CardDescription>
                  Total and selected variants per generation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={generationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="generation" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total" fill="#3b82f6" name="Total" />
                    <Bar dataKey="selected" fill="#22c55e" name="Selected" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 2 */}
          <div className="grid gap-6 md:grid-cols-2 mb-8">
            {/* Selection Rate Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Selection Rate by Generation</CardTitle>
                <CardDescription>
                  Percentage of selected variants per generation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={selectionRateData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="generation" />
                    <YAxis />
                    <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="rate"
                      stroke="#22c55e"
                      strokeWidth={2}
                      name="Selection Rate (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Mutation Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Mutation Strategy Distribution</CardTitle>
                <CardDescription>
                  Frequency of each mutation type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mutationData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="type" type="category" width={100} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8b5cf6" name="Count" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Recent Campaigns Table */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Campaigns</CardTitle>
              <CardDescription>
                Latest experimental evolution campaigns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {campaigns.slice(0, 10).map((campaign) => (
                  <Link
                    key={campaign.id}
                    href={`/campaigns/${campaign.id}`}
                    className="block"
                  >
                    <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex-1">
                        <div className="font-medium mb-1">{campaign.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {campaign.description || "No description"}
                        </div>
                      </div>
                      <Badge
                        className={getStatusColor(campaign.status)}
                      >
                        {campaign.status}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
