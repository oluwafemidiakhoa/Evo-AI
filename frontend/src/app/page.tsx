"use client"

import Link from "next/link"
import useSWR from "swr"
import { Zap, GitBranch, CheckCircle, TrendingUp, Plus } from "lucide-react"

import { campaignsAPI, variantsAPI, tasksAPI } from "@/lib/api/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, getStatusColor } from "@/lib/utils"
import type { Campaign, Job } from "@/types"

export default function DashboardPage() {
  const { data: campaignsData, isLoading: campaignsLoading } = useSWR(
    ["campaigns", 1, 10],
    () => campaignsAPI.list(1, 10)
  )

  const { data: variantsData } = useSWR(
    ["variants-recent"],
    () => variantsAPI.list({ page: 1, pageSize: 5 })
  )

  const { data: jobs } = useSWR(
    ["recent-jobs"],
    () => tasksAPI.listJobs({ limit: 5 })
  )

  const campaigns: Campaign[] = campaignsData?.campaigns || []
  const totalCampaigns = campaignsData?.total || 0

  const activeCampaigns = campaigns.filter((c) => c.status === "active").length
  const completedCampaigns = campaigns.filter((c) => c.status === "completed").length

  const totalVariants = variantsData?.total || 0
  const selectedVariants = variantsData?.variants?.filter((v: any) => v.is_selected).length || 0

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to the Evo-AI experimental evolution platform
        </p>
      </div>

      {/* Stats Overview */}
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
              {activeCampaigns} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Completed
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedCampaigns}</div>
            <p className="text-xs text-muted-foreground">
              {totalCampaigns > 0
                ? `${((completedCampaigns / totalCampaigns) * 100).toFixed(0)}% success rate`
                : "No campaigns yet"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Variants
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
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
              Selected Variants
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{selectedVariants}</div>
            <p className="text-xs text-muted-foreground">
              {totalVariants > 0
                ? `${((selectedVariants / totalVariants) * 100).toFixed(1)}% selection rate`
                : "No variants yet"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Campaigns */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Campaigns</CardTitle>
                <CardDescription>
                  Your most recent evolution experiments
                </CardDescription>
              </div>
              <Button asChild size="sm">
                <Link href="/campaigns/new">
                  <Plus className="mr-2 h-4 w-4" />
                  New
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {campaignsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : campaigns.length > 0 ? (
              <div className="space-y-3">
                {campaigns.slice(0, 5).map((campaign) => (
                  <Link
                    key={campaign.id}
                    href={`/campaigns/${campaign.id}`}
                    className="block"
                  >
                    <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                      <div className="flex-1">
                        <div className="font-medium mb-1">{campaign.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {campaign.description || "No description"}
                        </div>
                      </div>
                      <Badge className={getStatusColor(campaign.status)}>
                        {campaign.status}
                      </Badge>
                    </div>
                  </Link>
                ))}
                {campaigns.length > 5 && (
                  <Button variant="ghost" asChild className="w-full">
                    <Link href="/campaigns">View All Campaigns</Link>
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  No campaigns yet
                </p>
                <Button asChild>
                  <Link href="/campaigns/new">
                    Create Your First Campaign
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Jobs */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest task executions</CardDescription>
          </CardHeader>
          <CardContent>
            {jobs && jobs.length > 0 ? (
              <div className="space-y-3">
                {jobs.map((job: Job) => (
                  <div
                    key={job.job_id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div className="flex-1">
                      <div className="font-medium mb-1 capitalize">
                        {job.task_type.replace("_", " ")}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(job.created_at)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {job.status === "running" && (
                        <div className="text-sm text-muted-foreground">
                          {(job.progress * 100).toFixed(0)}%
                        </div>
                      )}
                      <Badge className={getStatusColor(job.status)}>
                        {job.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No recent activity
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <Button asChild className="h-auto py-4 flex-col gap-2">
                <Link href="/campaigns/new">
                  <Zap className="h-6 w-6" />
                  <div>
                    <div className="font-semibold">New Campaign</div>
                    <div className="text-xs font-normal opacity-80">
                      Start an evolution experiment
                    </div>
                  </div>
                </Link>
              </Button>

              <Button asChild variant="outline" className="h-auto py-4 flex-col gap-2">
                <Link href="/variants">
                  <GitBranch className="h-6 w-6" />
                  <div>
                    <div className="font-semibold">Browse Variants</div>
                    <div className="text-xs font-normal">
                      Explore generated code
                    </div>
                  </div>
                </Link>
              </Button>

              <Button asChild variant="outline" className="h-auto py-4 flex-col gap-2">
                <Link href="/reports">
                  <TrendingUp className="h-6 w-6" />
                  <div>
                    <div className="font-semibold">View Reports</div>
                    <div className="text-xs font-normal">
                      Analyze results
                    </div>
                  </div>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
