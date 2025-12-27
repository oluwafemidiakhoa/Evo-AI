"use client"

import { use } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { ArrowLeft, GitBranch, Info } from "lucide-react"

import { variantsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { LineageTree } from "@/components/lineage-tree"
import type { Lineage } from "@/types"

export default function VariantLineagePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()

  const { data: variant, isLoading: variantLoading } = useSWR(
    ["variant", id],
    () => variantsAPI.get(id)
  )

  const { data: lineageData, isLoading: lineageLoading } = useSWR(
    ["lineage", id],
    () => variantsAPI.getLineage(id)
  )

  if (variantLoading || lineageLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-8 w-64 mb-4" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!variant || !lineageData) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Lineage Not Found</h1>
          <p className="text-muted-foreground mb-4">
            Unable to load lineage data for this variant.
          </p>
          <Button asChild>
            <Link href="/variants">Back to Variants</Link>
          </Button>
        </div>
      </div>
    )
  }

  const typedLineage: Lineage = lineageData
  const lineage = typedLineage.lineage || []

  const handleNodeClick = (nodeId: string) => {
    router.push(`/variants/${nodeId}`)
  }

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <Button variant="ghost" asChild className="mb-4">
        <Link href={`/variants/${id}`}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Variant
        </Link>
      </Button>

      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <GitBranch className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Lineage Visualization</h1>
        </div>
        <p className="text-muted-foreground">
          Evolutionary history from founder to current variant
        </p>
      </div>

      {/* Lineage Stats */}
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Current Generation
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{variant.generation}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Ancestors
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{lineage.length}</div>
            <p className="text-xs text-muted-foreground">
              {typedLineage.generations} generation(s)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Founder Variant
            </CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="font-mono text-sm">
              {typedLineage.founder
                ? `${typedLineage.founder.id.substring(0, 8)}...`
                : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              Generation 0
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Mutation Types
            </CardTitle>
            <Info className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1">
              {Array.from(
                new Set(
                  lineage
                    .filter((n) => n.mutation_type)
                    .map((n) => n.mutation_type)
                )
              ).map((type) => (
                <Badge key={type} variant="secondary" className="text-xs">
                  {type}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info Alert */}
      <Card className="mb-6 bg-blue-50 dark:bg-blue-950 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Interactive Lineage Tree
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                This visualization shows the complete evolutionary history from the founder variant (Generation 0)
                to the current variant. Click on any node to navigate to that variant. Selected variants are
                highlighted in green, and the current variant is highlighted in blue.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lineage Tree Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Evolution Tree</CardTitle>
          <CardDescription>
            Click on any node to view that variant&apos;s details
          </CardDescription>
        </CardHeader>
        <CardContent>
          {lineage.length > 0 ? (
            <LineageTree
              lineage={[...lineage, {
                id: variant.id,
                generation: variant.generation,
                mutation_type: variant.mutation_type,
                is_selected: variant.is_selected
              }]}
              currentVariantId={id}
              onNodeClick={handleNodeClick}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>This is a founder variant with no ancestors.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lineage Details Table */}
      {lineage.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Lineage Details</CardTitle>
            <CardDescription>
              Complete ancestry chain with metadata
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...lineage, {
                id: variant.id,
                generation: variant.generation,
                mutation_type: variant.mutation_type,
                is_selected: variant.is_selected
              }].map((node, index) => (
                <div
                  key={node.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    node.id === id
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  } transition-colors`}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="flex items-center gap-2 min-w-[100px]">
                      <Badge variant={node.id === id ? "default" : "outline"}>
                        Gen {node.generation}
                      </Badge>
                      {node.id === id && (
                        <Badge variant="secondary">Current</Badge>
                      )}
                    </div>
                    <span className="font-mono text-sm text-muted-foreground">
                      {node.id.substring(0, 12)}...
                    </span>
                    {node.mutation_type && (
                      <Badge variant="secondary" className="capitalize">
                        {node.mutation_type}
                      </Badge>
                    )}
                    {node.is_selected && (
                      <Badge className="bg-green-100 text-green-800">
                        Selected
                      </Badge>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    asChild
                    disabled={node.id === id}
                  >
                    <Link href={`/variants/${node.id}`}>
                      {node.id === id ? "Current" : "View"}
                    </Link>
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
