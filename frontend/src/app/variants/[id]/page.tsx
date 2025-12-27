"use client"

import { use } from "react"
import Link from "next/link"
import useSWR from "swr"
import { ArrowLeft, CheckCircle, XCircle, GitBranch, Code2 } from "lucide-react"

import { variantsAPI, evaluationsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, formatScore, getStatusColor } from "@/lib/utils"
import type { Variant, Evaluation } from "@/types"

export default function VariantDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)

  const { data: variant, isLoading: variantLoading } = useSWR(
    ["variant", id],
    () => variantsAPI.get(id)
  )

  const { data: evaluations, isLoading: evaluationsLoading } = useSWR(
    ["evaluations", id],
    () => evaluationsAPI.listByVariant(id)
  )

  const { data: lineageData } = useSWR(
    ["lineage", id],
    () => variantsAPI.getLineage(id)
  )

  const { data: descendants } = useSWR(
    ["descendants", id],
    () => variantsAPI.getDescendants(id)
  )

  if (variantLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!variant) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Variant Not Found</h1>
          <p className="text-muted-foreground mb-4">
            The variant you are looking for does not exist.
          </p>
          <Button asChild>
            <Link href="/variants">Back to Variants</Link>
          </Button>
        </div>
      </div>
    )
  }

  const typedVariant: Variant = variant
  const lineage = lineageData?.lineage || []
  const descendantsList = descendants?.descendants || []

  return (
    <div className="container mx-auto py-8 max-w-6xl">
      <Button variant="ghost" asChild className="mb-4">
        <Link href="/variants">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Variants
        </Link>
      </Button>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold">Variant Detail</h1>
          {typedVariant.is_selected ? (
            <Badge className="bg-green-100 text-green-800">
              <CheckCircle className="mr-1 h-3 w-3" />
              Selected
            </Badge>
          ) : (
            <Badge variant="outline">Not Selected</Badge>
          )}
        </div>
        <p className="text-muted-foreground font-mono text-sm">
          ID: {typedVariant.id}
        </p>
      </div>

      {/* Variant Info Cards */}
      <div className="grid gap-6 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Generation</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{typedVariant.generation}</div>
            <p className="text-xs text-muted-foreground">
              {lineage.length > 0 ? `${lineage.length} ancestor(s)` : "Founder"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mutation Type</CardTitle>
            <Code2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {typedVariant.mutation_type || "Initial"}
            </div>
            <p className="text-xs text-muted-foreground">Evolution method</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Descendants</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{descendantsList.length}</div>
            <p className="text-xs text-muted-foreground">Child variants</p>
          </CardContent>
        </Card>
      </div>

      {/* Content */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Code Content</CardTitle>
          <CardDescription>
            Generated code for this variant
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded-lg overflow-x-auto">
            <code className="text-sm">{typedVariant.content}</code>
          </pre>
        </CardContent>
      </Card>

      {/* Evaluations */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Evaluations</CardTitle>
          <CardDescription>
            Performance and quality assessments
          </CardDescription>
        </CardHeader>
        <CardContent>
          {evaluationsLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : evaluations && evaluations.length > 0 ? (
            <div className="space-y-4">
              {evaluations.map((evaluation: Evaluation) => (
                <div
                  key={evaluation.id}
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="capitalize">
                        {evaluation.evaluator_type.replace("_", " ")}
                      </Badge>
                      <Badge className={getStatusColor(evaluation.status)}>
                        {evaluation.status}
                      </Badge>
                    </div>
                    {evaluation.score !== null && (
                      <div className="text-3xl font-bold">
                        {formatScore(evaluation.score)}
                      </div>
                    )}
                  </div>

                  {evaluation.result_data &&
                    Object.keys(evaluation.result_data).length > 0 && (
                      <div className="mt-2">
                        <h4 className="text-sm font-medium mb-1">
                          Result Data:
                        </h4>
                        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                          {JSON.stringify(evaluation.result_data, null, 2)}
                        </pre>
                      </div>
                    )}

                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    <div>Created: {formatDate(evaluation.created_at)}</div>
                    {evaluation.completed_at && (
                      <div>
                        Completed: {formatDate(evaluation.completed_at)}
                      </div>
                    )}
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

      {/* Lineage */}
      {lineage.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Lineage</CardTitle>
                <CardDescription>
                  Ancestry chain from founder to this variant
                </CardDescription>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link href={`/variants/${id}/lineage`}>
                  <GitBranch className="mr-2 h-4 w-4" />
                  View Full Tree
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lineage.map((ancestor, index) => (
                <div
                  key={ancestor.id}
                  className="flex items-center gap-4 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2 flex-1">
                    <Badge variant="outline">Gen {ancestor.generation}</Badge>
                    <span className="font-mono text-sm">
                      {ancestor.id.substring(0, 8)}...
                    </span>
                    {ancestor.mutation_type && (
                      <Badge variant="secondary">
                        {ancestor.mutation_type}
                      </Badge>
                    )}
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={`/variants/${ancestor.id}`}>View</Link>
                  </Button>
                </div>
              ))}
              <div className="flex items-center gap-4 p-3 border-2 border-primary rounded-lg bg-primary/5">
                <div className="flex items-center gap-2 flex-1">
                  <Badge>Gen {typedVariant.generation}</Badge>
                  <span className="font-mono text-sm font-bold">
                    {typedVariant.id.substring(0, 8)}... (Current)
                  </span>
                  {typedVariant.mutation_type && (
                    <Badge variant="secondary">
                      {typedVariant.mutation_type}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Descendants */}
      {descendantsList.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Descendants</CardTitle>
            <CardDescription>
              Variants evolved from this one
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {descendantsList.map((descendant: Variant) => (
                <div
                  key={descendant.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">Gen {descendant.generation}</Badge>
                    <span className="font-mono text-sm">
                      {descendant.id.substring(0, 8)}...
                    </span>
                    {descendant.mutation_type && (
                      <Badge variant="secondary">
                        {descendant.mutation_type}
                      </Badge>
                    )}
                    {descendant.is_selected && (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    )}
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={`/variants/${descendant.id}`}>View</Link>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
