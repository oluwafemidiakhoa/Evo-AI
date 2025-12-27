"use client"

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"

interface GraphNode {
  id: string
  generation: number
  mutation_type: string | null
  is_selected: boolean
  round_id: string
}

interface GraphLink {
  source: string
  target: string
}

interface CampaignLineageGraphProps {
  variants: GraphNode[]
  onNodeClick?: (nodeId: string) => void
}

export function CampaignLineageGraph({ variants, onNodeClick }: CampaignLineageGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || variants.length === 0) return

    // Clear existing content
    d3.select(svgRef.current).selectAll("*").remove()

    // Set up dimensions
    const container = containerRef.current
    const width = container.clientWidth
    const height = Math.max(600, variants.length * 40)
    const margin = { top: 40, right: 40, bottom: 40, left: 40 }

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Group variants by generation for layout
    const byGeneration = d3.group(variants, d => d.generation)
    const maxGeneration = d3.max(variants, d => d.generation) || 0

    // Calculate positions
    const xScale = d3.scaleLinear()
      .domain([0, maxGeneration])
      .range([0, width - margin.left - margin.right])

    const positions = new Map<string, { x: number; y: number }>()

    byGeneration.forEach((nodes, gen) => {
      const ySpacing = (height - margin.top - margin.bottom) / (nodes.length + 1)
      nodes.forEach((node, i) => {
        positions.set(node.id, {
          x: xScale(gen),
          y: (i + 1) * ySpacing
        })
      })
    })

    // Create links data (parent-child relationships)
    const links: GraphLink[] = []
    // Note: This requires parent_id in the data, which we'll add from the API
    // For now, we'll create links based on generation progression
    variants.forEach(variant => {
      const sameRoundPrevGen = variants.find(v =>
        v.generation === variant.generation - 1 &&
        v.round_id === variant.round_id
      )
      if (sameRoundPrevGen) {
        links.push({
          source: sameRoundPrevGen.id,
          target: variant.id
        })
      }
    })

    // Draw links
    g.selectAll(".link")
      .data(links)
      .join("line")
      .attr("class", "link")
      .attr("x1", d => positions.get(d.source)?.x || 0)
      .attr("y1", d => positions.get(d.source)?.y || 0)
      .attr("x2", d => positions.get(d.target)?.x || 0)
      .attr("y2", d => positions.get(d.target)?.y || 0)
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", 2)
      .attr("stroke-opacity", 0.4)

    // Draw nodes
    const nodes = g.selectAll(".node")
      .data(variants)
      .join("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${positions.get(d.id)?.x},${positions.get(d.id)?.y})`)
      .style("cursor", "pointer")
      .on("mouseenter", (event, d) => {
        setHoveredNode(d.id)
      })
      .on("mouseleave", () => {
        setHoveredNode(null)
      })
      .on("click", (event, d) => {
        event.stopPropagation()
        if (onNodeClick) {
          onNodeClick(d.id)
        }
      })

    // Node circles
    nodes.append("circle")
      .attr("r", d => hoveredNode === d.id ? 10 : 7)
      .attr("fill", d => d.is_selected ? "#22c55e" : "#64748b")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("transition", "r 0.2s")

    // Node labels (generation)
    nodes.append("text")
      .attr("dy", -12)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("font-weight", "500")
      .text(d => `G${d.generation}`)
      .clone(true).lower()
      .attr("stroke", "white")
      .attr("stroke-width", 3)

    // Generation axis
    const generations = Array.from({ length: maxGeneration + 1 }, (_, i) => i)
    g.selectAll(".gen-label")
      .data(generations)
      .join("text")
      .attr("class", "gen-label")
      .attr("x", d => xScale(d))
      .attr("y", -10)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#64748b")
      .text(d => `Generation ${d}`)

  }, [variants, hoveredNode, onNodeClick])

  return (
    <div ref={containerRef} className="w-full overflow-x-auto">
      <svg ref={svgRef} className="border rounded-lg bg-muted/20" />
    </div>
  )
}
