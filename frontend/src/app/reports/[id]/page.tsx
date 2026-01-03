"use client"

import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, Calendar, FileText } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { reportsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatDate } from "@/lib/utils"

export default function ReportDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const { id } = params

  const { data: report, error } = useSWR(['report', id], () => reportsAPI.get(id))

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-destructive">Failed to load report: {error.message}</p>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">Loading report...</p>
      </div>
    )
  }

  const reportFormat =
    report.format ||
    report.metadata?.format ||
    (typeof report.content === "string" ? "text" : "json")

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <Button variant="ghost" asChild className="mb-4">
          <Link href="/reports">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Reports
          </Link>
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <FileText className="h-8 w-8 text-blue-600" />
              <h1 className="text-4xl font-bold tracking-tight capitalize">
                {report.report_type.replace(/_/g, " ")}
              </h1>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(report.created_at)}
              </div>
              <Badge variant="secondary">{reportFormat}</Badge>
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Report Content</CardTitle>
          <CardDescription>Generated analysis and insights</CardDescription>
        </CardHeader>
        <CardContent>
          {report.content ? (
            typeof report.content === "string" ? (
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report.content}
                </ReactMarkdown>
              </div>
            ) : (
              <pre className="text-sm rounded-lg bg-muted/50 p-4 overflow-auto">
                {JSON.stringify(report.content, null, 2)}
              </pre>
            )
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No content available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
