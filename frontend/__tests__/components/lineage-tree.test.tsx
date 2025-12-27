/**
 * Tests for LineageTree component.
 *
 * Validates D3.js lineage visualization rendering and interactions.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { LineageTree } from '@/components/lineage-tree'

describe('LineageTree Component', () => {
  const mockLineage = [
    {
      id: '1',
      generation: 0,
      mutation_type: null,
      is_selected: true,
    },
    {
      id: '2',
      generation: 1,
      mutation_type: 'refactor',
      is_selected: true,
    },
    {
      id: '3',
      generation: 2,
      mutation_type: 'optimize',
      is_selected: false,
    },
  ]

  const currentVariantId = '3'

  it('renders without crashing', () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders all nodes in lineage', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      const nodes = document.querySelectorAll('.node')
      expect(nodes).toHaveLength(mockLineage.length)
    })
  })

  it('highlights current variant node differently', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      const circles = document.querySelectorAll('circle')
      const currentNode = Array.from(circles).find(
        (circle) => circle.getAttribute('fill') === '#3b82f6'
      )
      expect(currentNode).toBeInTheDocument()
    })
  })

  it('shows different colors for selected vs non-selected variants', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      const circles = document.querySelectorAll('circle')
      const selectedNodes = Array.from(circles).filter(
        (circle) => circle.getAttribute('fill') === '#22c55e'
      )
      const notSelectedNodes = Array.from(circles).filter(
        (circle) => circle.getAttribute('fill') === '#64748b'
      )

      expect(selectedNodes.length).toBeGreaterThan(0)
      expect(notSelectedNodes.length).toBeGreaterThan(0)
    })
  })

  it('displays generation labels on nodes', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      const text = screen.getByText(/Gen 0/)
      expect(text).toBeInTheDocument()
    })
  })

  it('calls onNodeClick when node is clicked', async () => {
    const handleClick = jest.fn()

    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
        onNodeClick={handleClick}
      />
    )

    await waitFor(() => {
      const nodes = document.querySelectorAll('.node')
      expect(nodes.length).toBeGreaterThan(0)
    })

    const firstNode = document.querySelector('.node')
    if (firstNode) {
      fireEvent.click(firstNode)
      expect(handleClick).toHaveBeenCalled()
    }
  })

  it('renders legend with correct labels', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Current')).toBeInTheDocument()
      expect(screen.getByText('Selected')).toBeInTheDocument()
      expect(screen.getByText('Not Selected')).toBeInTheDocument()
    })
  })

  it('handles empty lineage gracefully', () => {
    render(
      <LineageTree
        lineage={[]}
        currentVariantId={currentVariantId}
      />
    )

    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('handles single node lineage', async () => {
    const singleNode = [mockLineage[0]]

    render(
      <LineageTree
        lineage={singleNode}
        currentVariantId={singleNode[0].id}
      />
    )

    await waitFor(() => {
      const nodes = document.querySelectorAll('.node')
      expect(nodes).toHaveLength(1)
    })
  })

  it('displays mutation types in node labels', async () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/refactor/)).toBeInTheDocument()
      expect(screen.getByText(/optimize/)).toBeInTheDocument()
    })
  })

  it('updates when lineage prop changes', async () => {
    const { rerender } = render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId={currentVariantId}
      />
    )

    await waitFor(() => {
      const nodes = document.querySelectorAll('.node')
      expect(nodes).toHaveLength(3)
    })

    const newLineage = [
      ...mockLineage,
      {
        id: '4',
        generation: 3,
        mutation_type: 'expand',
        is_selected: true,
      },
    ]

    rerender(
      <LineageTree
        lineage={newLineage}
        currentVariantId={'4'}
      />
    )

    await waitFor(() => {
      const nodes = document.querySelectorAll('.node')
      expect(nodes).toHaveLength(4)
    })
  })

  it('scales SVG height based on lineage length', async () => {
    const longLineage = Array.from({ length: 10 }, (_, i) => ({
      id: `${i}`,
      generation: i,
      mutation_type: 'refactor',
      is_selected: false,
    }))

    render(
      <LineageTree
        lineage={longLineage}
        currentVariantId="9"
      />
    )

    await waitFor(() => {
      const svg = document.querySelector('svg')
      const height = svg?.getAttribute('height')
      expect(Number(height)).toBeGreaterThan(600)
    })
  })
})

describe('LineageTree Accessibility', () => {
  const mockLineage = [
    {
      id: '1',
      generation: 0,
      mutation_type: null,
      is_selected: true,
    },
  ]

  it('has proper SVG structure', () => {
    render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId="1"
      />
    )

    const svg = document.querySelector('svg')
    expect(svg).toHaveClass('border', 'rounded-lg')
  })

  it('maintains responsive container', () => {
    const { container } = render(
      <LineageTree
        lineage={mockLineage}
        currentVariantId="1"
      />
    )

    const wrapper = container.firstChild
    expect(wrapper).toHaveClass('w-full', 'overflow-x-auto')
  })
})

describe('LineageTree Performance', () => {
  it('handles large lineages without crashing', async () => {
    const largeLineage = Array.from({ length: 100 }, (_, i) => ({
      id: `${i}`,
      generation: i,
      mutation_type: 'refactor',
      is_selected: i % 3 === 0,
    }))

    const { container } = render(
      <LineageTree
        lineage={largeLineage}
        currentVariantId="99"
      />
    )

    await waitFor(() => {
      expect(container).toBeInTheDocument()
    })
  })
})
