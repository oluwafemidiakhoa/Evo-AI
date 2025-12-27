"use client"

import { use } from "react"
import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, FileText, Download, ExternalLink } from "lucide-react"

import { reportsAPI, campaignsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate } from "@/lib/utils"
import type { Report } from "@/types"

export default function ReportDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)

  const { data: report, isLoading: reportLoading } = useSWR(
    ["report", id],
    () => reportsAPI.get(id)
  )

  const { data: campaign } = useSWR(
    report ? ["campaign", report.campaign_id] : null,
    () => campaignsAPI.get(report!.campaign_id)
  )

  const handleDownload = () => {
    if (!report) return

    const blob = new Blob([JSON.stringify(report.content, null, 2)], {
      type: "application/json",
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `report-${report.id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (reportLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Report Not Found</h1>
          <p className="text-muted-foreground mb-4">
            The report you are looking for does not exist.
          </p>
          <Button asChild>
            <Link href="/reports">Back to Reports</Link>
          </Button>
        </div>
      </div>
    )
  }

  const typedReport: Report = report

  return (
    <div className="container mx-auto py-8 max-w-5xl">
      <Button variant="ghost" asChild className="mb-4">
        <Link href="/reports">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Reports
        </Link>
      </Button>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold">Report Details</h1>
          <Button variant="outline" onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download JSON
          </Button>
        </div>
        <p className="text-muted-foreground font-mono text-sm">
          ID: {typedReport.id}
        </p>
      </div>

      {/* Report Metadata */}
      <div className="grid gap-6 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Report Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary" className="capitalize text-base">
              {typedReport.report_type.replace(/_/g, " ")}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Campaign
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Link
              href={`/campaigns/${typedReport.campaign_id}`}
              className="flex items-center gap-1 text-primary hover:underline"
            >
              <span className="font-medium">
                {campaign?.name || typedReport.campaign_id.substring(0, 8)}
              </span>
              <ExternalLink className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Generated
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-medium">
              {formatDate(typedReport.created_at)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Report Content */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Report Content</CardTitle>
          <CardDescription>
            Generated analysis and metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {typedReport.content && typeof typedReport.content === "object" ? (
            <div className="space-y-6">
              {/* Render different sections based on report type */}
              {typedReport.report_type === "round_summary" && (
                <RoundSummaryContent content={typedReport.content} />
              )}
              {typedReport.report_type === "campaign_summary" && (
                <CampaignSummaryContent content={typedReport.content} />
              )}
              {typedReport.report_type === "lineage_analysis" && (
                <LineageAnalysisContent content={typedReport.content} />
              )}
              {typedReport.report_type === "performance_metrics" && (
                <PerformanceMetricsContent content={typedReport.content} />
              )}

              {/* Fallback: Show raw JSON */}
              {!["round_summary", "campaign_summary", "lineage_analysis", "performance_metrics"].includes(
                typedReport.report_type
              ) && (
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                  {JSON.stringify(typedReport.content, null, 2)}
                </pre>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No content available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      {typedReport.metadata && Object.keys(typedReport.metadata).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Metadata</CardTitle>
            <CardDescription>Additional report information</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
              {JSON.stringify(typedReport.metadata, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Component for Round Summary reports
function RoundSummaryContent({ content }: { content: Record<string, any> }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <StatCard label="Total Variants" value={content.total_variants} />
        <StatCard label="Selected Variants" value={content.selected_variants} />
        <StatCard label="Average Score" value={content.average_score?.toFixed(3)} />
        <StatCard label="Max Score" value={content.max_score?.toFixed(3)} />
      </div>
      {content.summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{content.summary}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Component for Campaign Summary reports
function CampaignSummaryContent({ content }: { content: Record<string, any> }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total Rounds" value={content.total_rounds} />
        <StatCard label="Total Variants" value={content.total_variants} />
        <StatCard label="Selection Rate" value={`${(content.selection_rate * 100).toFixed(1)}%`} />
      </div>
      {content.insights && Array.isArray(content.insights) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Key Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {content.insights.map((insight: string, i: number) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-primary">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Component for Lineage Analysis reports
function LineageAnalysisContent({ content }: { content: Record<string, any> }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <StatCard label="Max Generation" value={content.max_generation} />
        <StatCard label="Total Lineages" value={content.total_lineages} />
      </div>
      {content.analysis && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap">
              {typeof content.analysis === "string"
                ? content.analysis
                : JSON.stringify(content.analysis, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Component for Performance Metrics reports
function PerformanceMetricsContent({ content }: { content: Record<string, any> }) {
  return (
    <div className="space-y-4">
      {content.metrics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(content.metrics).map(([key, value]) => (
            <StatCard
              key={key}
              label={key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
              value={typeof value === "number" ? value.toFixed(3) : String(value)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Utility component for stat display
function StatCard({ label, value }: { label: string; value: any }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-sm text-muted-foreground mb-1">{label}</div>
        <div className="text-2xl font-bold">{value ?? "N/A"}</div>
      </CardContent>
    </Card>
  )
}
