"use client"

import { useState } from "react"
import Link from "next/link"
import useSWR from "swr"
import { FileText, Filter, Calendar } from "lucide-react"

import { reportsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate } from "@/lib/utils"
import type { Report } from "@/types"

export default function ReportsPage() {
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [reportType, setReportType] = useState<string | undefined>(undefined)
  const [campaignId, setCampaignId] = useState<string>("")

  const { data, error, isLoading } = useSWR(
    ["reports", page, pageSize, reportType, campaignId],
    () =>
      reportsAPI.list({
        page,
        pageSize,
        reportType,
        campaignId: campaignId || undefined,
      })
  )

  const reports: Report[] = data?.reports || []
  const totalPages = data?.total_pages || 1

  const reportTypes = [
    { value: "round_summary", label: "Round Summary" },
    { value: "campaign_summary", label: "Campaign Summary" },
    { value: "lineage_analysis", label: "Lineage Analysis" },
    { value: "performance_metrics", label: "Performance Metrics" },
  ]

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Reports</h1>
        <p className="text-muted-foreground">
          Generated reports and analysis from campaigns
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="campaign-id">Campaign ID</Label>
              <Input
                id="campaign-id"
                placeholder="Filter by campaign ID..."
                value={campaignId}
                onChange={(e) => setCampaignId(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Report Type</Label>
              <div className="flex flex-wrap gap-2 pt-1">
                <Button
                  variant={!reportType ? "default" : "outline"}
                  size="sm"
                  onClick={() => setReportType(undefined)}
                >
                  All Types
                </Button>
                {reportTypes.map((type) => (
                  <Button
                    key={type.value}
                    variant={reportType === type.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setReportType(type.value)}
                  >
                    {type.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          {(reportType || campaignId) && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setReportType(undefined)
                  setCampaignId("")
                }}
              >
                Clear All Filters
              </Button>
              <span className="text-sm text-muted-foreground">
                {reports.length} report(s) found
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reports List */}
      <Card>
        <CardHeader>
          <CardTitle>All Reports</CardTitle>
          <CardDescription>{reports.length} report(s)</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              Failed to load reports: {error.message}
            </div>
          ) : reports.length > 0 ? (
            <>
              <div className="space-y-3">
                {reports.map((report: Report) => (
                  <Link
                    key={report.id}
                    href={`/reports/${report.id}`}
                    className="block"
                  >
                    <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-4 flex-1">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="secondary" className="capitalize">
                              {report.report_type.replace(/_/g, " ")}
                            </Badge>
                            {report.round_id && (
                              <span className="text-xs text-muted-foreground">
                                Round Report
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Campaign: {report.campaign_id.substring(0, 8)}...
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            {formatDate(report.created_at)}
                          </div>
                        </div>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <div className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 1}
                      onClick={() => setPage(page - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === totalPages}
                      onClick={() => setPage(page + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No reports found</p>
              <p className="text-sm mt-2">
                Reports are automatically generated when campaigns complete
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
