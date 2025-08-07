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
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { apiService, University } from '@/lib/api'

export default function UniversitiesPage() {
  const [universities, setUniversities] = useState<University[]>([])
  const [filteredUniversities, setFilteredUniversities] = useState<University[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [favorites, setFavorites] = useState<number[]>([])
  const router = useRouter()

  useEffect(() => {
    // Load universities from API
    const loadUniversities = async () => {
      setIsLoading(true)
      try {
        const data = await apiService.getUniversities()
        setUniversities(data)
        setFilteredUniversities(data)
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
      (uni.city && uni.city.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (uni.state && uni.state.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (uni.country && uni.country.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (uni.programs && uni.programs.some(program => 
        program.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (program.field && program.field.toLowerCase().includes(searchQuery.toLowerCase()))
      ))
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

  const handleUniversityClick = (universityId: number) => {
    router.push(`/universities/${universityId}`)
  }

  const getMatchScoreColor = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-800'
    if (score >= 80) return 'bg-blue-100 text-blue-800'
    if (score >= 70) return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
  }

  const formatLocation = (university: University) => {
    const parts = [university.city, university.state, university.country].filter(Boolean)
    return parts.join(', ')
  }

  const formatTuition = (university: University) => {
    if (university.tuition_domestic) {
      return `$${university.tuition_domestic.toLocaleString()}/year`
    }
    if (university.tuition_international) {
      return `$${university.tuition_international.toLocaleString()}/year`
    }
    return 'Tuition not available'
  }

  const formatAcceptanceRate = (rate: number | undefined) => {
    if (rate === undefined || rate === null) return 'Not available'
    return `${rate.toFixed(1)}%`
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
            <Card 
              key={university.id} 
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleUniversityClick(university.id)}
            >
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-2">{university.name}</CardTitle>
                    <div className="flex items-center text-sm text-muted-foreground mb-2">
                      <MapPin className="h-4 w-4 mr-1" />
                      {formatLocation(university)}
                    </div>
                    <div className="flex items-center space-x-2">
                      {university.world_ranking && (
                        <Badge variant="outline" className="text-xs">
                          #{university.world_ranking} World Ranking
                        </Badge>
                      )}
                      {university.national_ranking && (
                        <Badge variant="outline" className="text-xs">
                          #{university.national_ranking} National Ranking
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleFavorite(university.id)
                    }}
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
                  {university.description || 'No description available'}
                </p>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Acceptance Rate:</span>
                    <span className="font-medium">{formatAcceptanceRate(university.acceptance_rate)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Tuition:</span>
                    <span className="font-medium">{formatTuition(university)}</span>
                  </div>
                  {university.student_population && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Students:</span>
                      <span className="font-medium">{university.student_population.toLocaleString()}</span>
                    </div>
                  )}
                </div>

                <Separator />

                <div>
                  <h4 className="text-sm font-medium mb-2">Top Programs:</h4>
                  <div className="flex flex-wrap gap-1">
                    {university.programs && university.programs.slice(0, 3).map((program, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {program.name}
                      </Badge>
                    ))}
                    {university.programs && university.programs.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{university.programs.length - 3} more
                      </Badge>
                    )}
                    {(!university.programs || university.programs.length === 0) && (
                      <Badge variant="secondary" className="text-xs">
                        Programs not available
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