'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Search, 
  MapPin, 
  GraduationCap, 
  Star, 
  Users, 
  DollarSign,
  Filter,
  Heart,
  ExternalLink
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface University {
  id: number
  name: string
  location: string
  ranking: number
  acceptanceRate: string
  tuition: string
  programs: string[]
  matchScore: number
  description: string
  image?: string
}

export default function UniversitiesPage() {
  const [universities, setUniversities] = useState<University[]>([])
  const [filteredUniversities, setFilteredUniversities] = useState<University[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [favorites, setFavorites] = useState<number[]>([])

  // Mock data for demonstration
  const mockUniversities: University[] = [
    {
      id: 1,
      name: "Stanford University",
      location: "Stanford, CA",
      ranking: 2,
      acceptanceRate: "4.3%",
      tuition: "$56,169/year",
      programs: ["Computer Science", "Engineering", "Business", "Medicine"],
      matchScore: 95,
      description: "Stanford University is a private research university known for its entrepreneurial spirit and innovation."
    },
    {
      id: 2,
      name: "MIT",
      location: "Cambridge, MA",
      ranking: 1,
      acceptanceRate: "6.7%",
      tuition: "$55,450/year",
      programs: ["Engineering", "Computer Science", "Physics", "Mathematics"],
      matchScore: 92,
      description: "Massachusetts Institute of Technology is a world-renowned institution for science and technology."
    },
    {
      id: 3,
      name: "Harvard University",
      location: "Cambridge, MA",
      ranking: 3,
      acceptanceRate: "4.6%",
      tuition: "$54,768/year",
      programs: ["Law", "Medicine", "Business", "Arts & Sciences"],
      matchScore: 88,
      description: "Harvard University is America's oldest institution of higher learning and a world leader in research."
    },
    {
      id: 4,
      name: "University of California, Berkeley",
      location: "Berkeley, CA",
      ranking: 22,
      acceptanceRate: "14.8%",
      tuition: "$44,008/year",
      programs: ["Engineering", "Computer Science", "Business", "Environmental Science"],
      matchScore: 85,
      description: "UC Berkeley is a top-ranked public university known for its research and social activism."
    },
    {
      id: 5,
      name: "Carnegie Mellon University",
      location: "Pittsburgh, PA",
      ranking: 22,
      acceptanceRate: "15.4%",
      tuition: "$58,924/year",
      programs: ["Computer Science", "Engineering", "Arts", "Business"],
      matchScore: 82,
      description: "Carnegie Mellon is known for its world-class programs in computer science and the arts."
    }
  ]

  useEffect(() => {
    // Simulate loading data
    const loadUniversities = async () => {
      setIsLoading(true)
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500))
        setUniversities(mockUniversities)
        setFilteredUniversities(mockUniversities)
        toast.success('University matches loaded successfully!')
      } catch (error) {
        console.error('Error loading universities:', error)
        toast.error('Failed to load universities')
      } finally {
        setIsLoading(false)
      }
    }

    loadUniversities()
  }, [])

  useEffect(() => {
    // Filter universities based on search query
    const filtered = universities.filter(uni =>
      uni.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      uni.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      uni.programs.some(program => 
        program.toLowerCase().includes(searchQuery.toLowerCase())
      )
    )
    setFilteredUniversities(filtered)
  }, [searchQuery, universities])

  const toggleFavorite = (universityId: number) => {
    setFavorites(prev => 
      prev.includes(universityId) 
        ? prev.filter(id => id !== universityId)
        : [...prev, universityId]
    )
  }

  const getMatchScoreColor = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-800'
    if (score >= 80) return 'bg-blue-100 text-blue-800'
    if (score >= 70) return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg font-medium">Loading your university matches...</p>
          <p className="text-muted-foreground">This may take a few moments</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                href="/" 
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Home
              </Link>
              <div className="flex items-center space-x-2">
                <GraduationCap className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold">Your University Matches</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                {filteredUniversities.length} Matches Found
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Search and Filter Section */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search universities, locations, or programs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm">
                Sort by Match Score
              </Button>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">Your Personalized Matches</h2>
          <p className="text-muted-foreground">
            Based on your questionnaire responses, here are the universities that best match your profile.
          </p>
        </div>

        {/* Universities Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredUniversities.map((university) => (
            <Card key={university.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-2">{university.name}</CardTitle>
                    <div className="flex items-center text-sm text-muted-foreground mb-2">
                      <MapPin className="h-4 w-4 mr-1" />
                      {university.location}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        #{university.ranking} Ranking
                      </Badge>
                      <Badge className={`text-xs ${getMatchScoreColor(university.matchScore)}`}>
                        {university.matchScore}% Match
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleFavorite(university.id)}
                    className={`p-1 h-8 w-8 ${
                      favorites.includes(university.id) ? 'text-red-500' : 'text-muted-foreground'
                    }`}
                  >
                    <Heart className={`h-4 w-4 ${
                      favorites.includes(university.id) ? 'fill-current' : ''
                    }`} />
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {university.description}
                </p>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Acceptance Rate:</span>
                    <span className="font-medium">{university.acceptanceRate}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Tuition:</span>
                    <span className="font-medium">{university.tuition}</span>
                  </div>
                </div>

                <Separator />

                <div>
                  <h4 className="text-sm font-medium mb-2">Top Programs:</h4>
                  <div className="flex flex-wrap gap-1">
                    {university.programs.slice(0, 3).map((program, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {program}
                      </Badge>
                    ))}
                    {university.programs.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{university.programs.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="flex space-x-2 pt-2">
                  <Button size="sm" className="flex-1">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                  <Button size="sm" variant="outline">
                    Compare
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* No Results */}
        {filteredUniversities.length === 0 && (
          <div className="text-center py-12">
            <GraduationCap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No universities found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search terms or filters
            </p>
            <Button onClick={() => setSearchQuery('')}>
              Clear Search
            </Button>
          </div>
        )}

        {/* Action Section */}
        <div className="mt-12 text-center">
          <Card className="gradient-bg text-white border-0">
            <CardContent className="pt-8 pb-8">
              <h3 className="text-xl font-bold mb-2">Need More Options?</h3>
              <p className="text-white/90 mb-6">
                Complete additional questions to get more personalized recommendations
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button variant="secondary" asChild>
                  <Link href="/questionnaire">
                    Retake Questionnaire
                  </Link>
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white hover:text-primary">
                  Contact Advisor
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 