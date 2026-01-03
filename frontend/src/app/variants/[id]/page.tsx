"use client"

import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, Code, GitBranch, Calendar } from "lucide-react"

import { variantsAPI, evaluationsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatDate, formatScore } from "@/lib/utils"
import { LineageTree } from "@/components/lineage-tree"

export default function VariantDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const { id } = params

  const { data: variant, error: variantError } = useSWR(['variant', id], () => variantsAPI.get(id))
  const { data: lineage } = useSWR(variant ? ['variant-lineage', id] : null, () => variantsAPI.getLineage(id))
  const { data: evaluations } = useSWR(variant ? ['variant-evaluations', id] : null, () => evaluationsAPI.list({ variantId: id }))

  if (variantError) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-destructive">Failed to load variant: {variantError.message}</p>
      </div>
    )
  }

  if (!variant) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground">Loading variant...</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <Button variant="ghost" asChild className="mb-4">
          <Link href="/variants">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Variants
          </Link>
        </Button>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Code className="h-8 w-8 text-purple-600" />
              <h1 className="text-4xl font-bold tracking-tight">
                Variant Details
              </h1>
            </div>
            <p className="text-sm text-muted-foreground font-mono">
              {variant.id}
            </p>
          </div>
          <Badge className={variant.is_selected ? 'bg-green-600' : 'bg-gray-600'}>
            {variant.is_selected ? 'Selected' : 'Not Selected'}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Generation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{variant.generation}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Mutation Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold capitalize">
              {variant.mutation_type || 'initial'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Parent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-mono">
              {variant.parent_id ? variant.parent_id.substring(0, 8) + '...' : 'None (founder)'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Created
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">{formatDate(variant.created_at)}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Variant Content</CardTitle>
          <CardDescription>Generated code or prompt</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="p-4 bg-muted rounded-lg overflow-x-auto">
            <code className="text-sm">{variant.content}</code>
          </pre>
        </CardContent>
      </Card>

      {lineage && lineage.lineage && lineage.lineage.length > 0 && (
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Lineage Tree</CardTitle>
                <CardDescription>Ancestry chain for this variant</CardDescription>
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link href={'/variants/' + id + '/lineage'}>
                  <GitBranch className="mr-2 h-4 w-4" />
                  Full Lineage View
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <LineageTree 
              lineage={lineage.lineage} 
              currentVariantId={id}
            />
          </CardContent>
        </Card>
      )}

      {evaluations && evaluations.evaluations && evaluations.evaluations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Evaluations</CardTitle>
            <CardDescription>Scores and metrics for this variant</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {evaluations.evaluations.map((evaluation: any) => (
                <div key={evaluation.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-lg font-semibold">
                      Score: {formatScore(evaluation.score)}
                    </div>
                    <Badge variant="outline">{formatDate(evaluation.created_at)}</Badge>
                  </div>
                  {evaluation.metrics && Object.keys(evaluation.metrics).length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                      {Object.entries(evaluation.metrics).map(([key, value]: [string, any]) => (
                        <div key={key} className="text-sm">
                          <div className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</div>
                          <div className="font-medium">{typeof value === 'number' ? formatScore(value) : value}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
