"use client"

import { useState } from "react"
import Link from "next/link"
import useSWR from "swr"
import { Search, Filter, CheckCircle, XCircle } from "lucide-react"

import { variantsAPI, evaluationsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, truncate } from "@/lib/utils"
import type { Variant } from "@/types"

export default function VariantsPage() {
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [selectedOnly, setSelectedOnly] = useState(false)
  const [generation, setGeneration] = useState<number | undefined>(undefined)
  const [searchQuery, setSearchQuery] = useState("")

  const { data, error, isLoading } = useSWR(
    ["variants", page, pageSize, selectedOnly, generation],
    () =>
      variantsAPI.list({
        page,
        pageSize,
        selectedOnly,
        generation,
      })
  )

  const variants: Variant[] = data?.variants || []
  const totalPages = data?.total_pages || 1

  const filteredVariants = searchQuery
    ? variants.filter((v) =>
        v.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        v.mutation_type?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : variants

  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Variants</h1>
        <p className="text-muted-foreground">
          Browse and search all generated code variants
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
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="search">Search Content</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search in variant content..."
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="generation">Generation</Label>
              <Input
                id="generation"
                type="number"
                min="0"
                placeholder="Filter by generation..."
                value={generation || ""}
                onChange={(e) =>
                  setGeneration(
                    e.target.value ? parseInt(e.target.value) : undefined
                  )
                }
              />
            </div>

            <div className="space-y-2">
              <Label>Selection Status</Label>
              <div className="flex gap-2 pt-2">
                <Button
                  variant={!selectedOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedOnly(false)}
                >
                  All
                </Button>
                <Button
                  variant={selectedOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedOnly(true)}
                >
                  Selected Only
                </Button>
              </div>
            </div>
          </div>

          {(searchQuery || generation || selectedOnly) && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSearchQuery("")
                  setGeneration(undefined)
                  setSelectedOnly(false)
                }}
              >
                Clear All Filters
              </Button>
              <span className="text-sm text-muted-foreground">
                {filteredVariants.length} variant(s) found
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Variants Table */}
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>
            {filteredVariants.length} variant(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              Failed to load variants: {error.message}
            </div>
          ) : filteredVariants.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Generation</TableHead>
                    <TableHead>Content Preview</TableHead>
                    <TableHead>Mutation Type</TableHead>
                    <TableHead>Selected</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredVariants.map((variant: Variant) => (
                    <TableRow key={variant.id}>
                      <TableCell className="font-mono text-xs">
                        {variant.id.substring(0, 8)}...
                      </TableCell>
                      <TableCell className="font-medium">
                        {variant.generation}
                      </TableCell>
                      <TableCell className="max-w-md">
                        <code className="text-xs bg-muted px-2 py-1 rounded block overflow-hidden">
                          {truncate(variant.content, 100)}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {variant.mutation_type || "initial"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {variant.is_selected ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-gray-400" />
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(variant.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            asChild
                          >
                            <Link href={`/variants/${variant.id}`}>
                              View
                            </Link>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            asChild
                          >
                            <Link href={`/variants/${variant.id}/lineage`}>
                              Lineage
                            </Link>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
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
            <div className="text-center py-8 text-muted-foreground">
              No variants found matching your filters
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
