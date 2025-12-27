"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { campaignsAPI } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function NewCampaignPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    max_rounds: 20,
    variants_per_round: 10,
    evaluators: ["llm_judge"],
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const campaign = await campaignsAPI.create({
        name: formData.name,
        description: formData.description || undefined,
        config: {
          max_rounds: formData.max_rounds,
          variants_per_round: formData.variants_per_round,
          evaluators: formData.evaluators,
        },
      })

      router.push(`/campaigns/${campaign.id}`)
    } catch (error: any) {
      alert(`Failed to create campaign: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8 max-w-2xl">
      <Button variant="ghost" asChild className="mb-4">
        <Link href="/campaigns">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Campaigns
        </Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Create New Campaign</CardTitle>
          <CardDescription>
            Set up a new evolution experiment campaign
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium mb-2"
              >
                Campaign Name *
              </label>
              <input
                id="name"
                type="text"
                required
                className="w-full px-3 py-2 border border-input rounded-md bg-background"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium mb-2"
              >
                Description
              </label>
              <textarea
                id="description"
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-md bg-background"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="max_rounds"
                  className="block text-sm font-medium mb-2"
                >
                  Max Rounds *
                </label>
                <input
                  id="max_rounds"
                  type="number"
                  required
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  value={formData.max_rounds}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_rounds: parseInt(e.target.value),
                    })
                  }
                />
              </div>

              <div>
                <label
                  htmlFor="variants_per_round"
                  className="block text-sm font-medium mb-2"
                >
                  Variants per Round *
                </label>
                <input
                  id="variants_per_round"
                  type="number"
                  required
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background"
                  value={formData.variants_per_round}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      variants_per_round: parseInt(e.target.value),
                    })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Evaluators
              </label>
              <div className="space-y-2">
                {["llm_judge", "unit_test", "benchmark"].map((evaluator) => (
                  <label key={evaluator} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.evaluators.includes(evaluator)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            evaluators: [...formData.evaluators, evaluator],
                          })
                        } else {
                          setFormData({
                            ...formData,
                            evaluators: formData.evaluators.filter(
                              (ev) => ev !== evaluator
                            ),
                          })
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm capitalize">
                      {evaluator.replace("_", " ")}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Campaign"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
