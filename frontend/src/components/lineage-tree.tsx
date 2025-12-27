"use client"

import { useEffect, useRef } from "react"
import * as d3 from "d3"

interface LineageNode {
  id: string
  generation: number
  mutation_type: string | null
  is_selected: boolean
  content_preview?: string
  [key: string]: any
}

interface LineageTreeProps {
  lineage: LineageNode[]
  currentVariantId: string
  onNodeClick?: (nodeId: string) => void
}

export function LineageTree({ lineage, currentVariantId, onNodeClick }: LineageTreeProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || lineage.length === 0) return

    // Clear existing content
    d3.select(svgRef.current).selectAll("*").remove()

    // Set up dimensions
    const container = containerRef.current
    const width = container.clientWidth
    const height = Math.max(600, lineage.length * 80)
    const margin = { top: 40, right: 120, bottom: 40, left: 120 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Prepare hierarchical data
    const nodes = [...lineage].reverse() // Oldest first

    // Create tree layout
    const treeLayout = d3.tree<LineageNode>()
      .size([innerHeight, innerWidth])
      .separation(() => 1)

    // Build hierarchy - linear chain from oldest to newest
    const rootNode = d3.hierarchy({
      id: nodes[0].id,
      generation: nodes[0].generation,
      mutation_type: nodes[0].mutation_type,
      is_selected: nodes[0].is_selected,
      children: buildChain(nodes.slice(1))
    } as any)

    function buildChain(remainingNodes: LineageNode[]): any[] {
      if (remainingNodes.length === 0) return []
      const [first, ...rest] = remainingNodes
      return [{
        id: first.id,
        generation: first.generation,
        mutation_type: first.mutation_type,
        is_selected: first.is_selected,
        children: buildChain(rest)
      }]
    }

    const treeData = treeLayout(rootNode)

    // Draw links
    g.selectAll(".link")
      .data(treeData.links())
      .join("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", (d: any) => {
        const targetNode = d.target.data as LineageNode
        return targetNode.is_selected ? "#22c55e" : "#94a3b8"
      })
      .attr("stroke-width", (d: any) => {
        const targetNode = d.target.data as LineageNode
        return targetNode.is_selected ? 3 : 2
      })
      .attr("stroke-opacity", 0.6)
      .attr("d", d3.linkHorizontal()
        .x((d: any) => d.y)
        .y((d: any) => d.x) as any
      )

    // Draw nodes
    const node = g.selectAll(".node")
      .data(treeData.descendants())
      .join("g")
      .attr("class", "node")
      .attr("transform", (d: any) => `translate(${d.y},${d.x})`)
      .style("cursor", "pointer")
      .on("click", (event, d: any) => {
        event.stopPropagation()
        if (onNodeClick) {
          onNodeClick(d.data.id)
        }
      })

    // Node circles
    node.append("circle")
      .attr("r", (d: any) => {
        const nodeData = d.data as LineageNode
        return nodeData.id === currentVariantId ? 12 : 8
      })
      .attr("fill", (d: any) => {
        const nodeData = d.data as LineageNode
        if (nodeData.id === currentVariantId) return "#3b82f6"
        return nodeData.is_selected ? "#22c55e" : "#64748b"
      })
      .attr("stroke", (d: any) => {
        const nodeData = d.data as LineageNode
        return nodeData.id === currentVariantId ? "#1e40af" : "#fff"
      })
      .attr("stroke-width", (d: any) => {
        const nodeData = d.data as LineageNode
        return nodeData.id === currentVariantId ? 3 : 2
      })

    // Node labels
    node.append("text")
      .attr("dy", "0.31em")
      .attr("x", (d: any) => (d.children ? -15 : 15))
      .attr("text-anchor", (d: any) => (d.children ? "end" : "start"))
      .attr("font-size", "12px")
      .attr("font-weight", (d: any) => {
        const nodeData = d.data as LineageNode
        return nodeData.id === currentVariantId ? "bold" : "normal"
      })
      .text((d: any) => {
        const nodeData = d.data as LineageNode
        return `Gen ${nodeData.generation}${nodeData.mutation_type ? ` (${nodeData.mutation_type})` : ""}`
      })
      .clone(true).lower()
      .attr("stroke", "white")
      .attr("stroke-width", 3)

    // Add legend
    const legend = svg.append("g")
      .attr("transform", `translate(${width - 100}, 20)`)

    const legendData = [
      { label: "Current", color: "#3b82f6" },
      { label: "Selected", color: "#22c55e" },
      { label: "Not Selected", color: "#64748b" }
    ]

    legendData.forEach((item, i) => {
      const legendItem = legend.append("g")
        .attr("transform", `translate(0, ${i * 20})`)

      legendItem.append("circle")
        .attr("r", 6)
        .attr("fill", item.color)
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)

      legendItem.append("text")
        .attr("x", 12)
        .attr("y", 4)
        .attr("font-size", "11px")
        .text(item.label)
    })

  }, [lineage, currentVariantId, onNodeClick])

  return (
    <div ref={containerRef} className="w-full overflow-x-auto">
      <svg ref={svgRef} className="border rounded-lg bg-muted/20" />
    </div>
  )
}
