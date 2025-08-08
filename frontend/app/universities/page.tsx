'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { 
  Search, 
  MapPin, 
  GraduationCap, 
  Star, 
  Users, 
  DollarSign,
  Filter,
  Heart,
  ExternalLink,
  RefreshCw,
  Trash2
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, University } from '@/lib/api'
import AppLayout from '@/components/layout/AppLayout'

export default function UniversitiesPage() {
  const router = useRouter()
  const [universities, setUniversities] = useState<University[]>([])
  const [filteredUniversities, setFilteredUniversities] = useState<University[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [suggestionStats, setSuggestionStats] = useState<any>(null)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [favorites, setFavorites] = useState<string[]>([])
  const isLoadingRef = useRef(false)

  useEffect(() => {
    // Check authentication and load universities
    const checkAuthAndLoadUniversities = async () => {
      if (isLoadingRef.current) return;
      isLoadingRef.current = true;
      setIsLoading(true);

      try {
        // Check if user is authenticated
        const isAuth = await api.isAuthenticated();
        if (!isAuth) {
          toast.error('Please log in to view your university matches')
          router.push('/login')
          return
        }

        // Check if user has completed questionnaire
        const userProfile = await api.getProfile()
        if (!userProfile.personality_summary || !userProfile.personality_profile) {
          toast.error('Please complete the questionnaire first to get personalized matches')
          router.push('/questionnaire')
          return
        }

        // First, check if user has saved suggestions
        try {
          const suggestionsResponse = await api.getUserSuggestions(20)
          if (suggestionsResponse.suggestions && suggestionsResponse.suggestions.length > 0) {
            console.log('Found saved suggestions:', suggestionsResponse.suggestions.length)
            
            // Extract university data from saved suggestions
            const universityData = suggestionsResponse.suggestions
              .map((suggestion: any) => suggestion.university_data)
              .filter(Boolean)
            
            setUniversities(universityData)
            setFilteredUniversities(universityData)
            setSuggestionStats(suggestionsResponse.stats)
            toast.success('Your saved university matches loaded successfully!')
            return
          }
        } catch (suggestionError) {
          console.log('No saved suggestions found, will generate new ones')
        }

        // If no saved suggestions, generate new ones
        console.log('Generating new collection matches...')
        const matchesResponse = await api.generateCollectionMatches(20)
        console.log('Matches response:', matchesResponse)
        
        // The response should be an array of matches, each with university_data
        const matches = Array.isArray(matchesResponse) ? matchesResponse : []
        
        // Extract university data from matches
        const universityData = matches.map((match: any) => match.university_data).filter(Boolean)
        
        setUniversities(universityData)
        setFilteredUniversities(universityData)
        
        // Fetch suggestion stats after generating new suggestions
        try {
          const suggestionsResponse = await api.getUserSuggestions(20)
          setSuggestionStats(suggestionsResponse.stats)
        } catch (statsError) {
          console.log('Could not fetch suggestion stats:', statsError)
        }
        
        toast.success('Your personalized university matches generated and saved successfully!')
      } catch (error) {
        console.error('Error loading universities:', error)
        
        // Handle different types of errors
        if (error instanceof Error) {
          if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            toast.error('Please log in to view your university matches')
            router.push('/login')
          } else if (error.message.includes('400') || error.message.includes('questionnaire')) {
            toast.error('Please complete the questionnaire first to get personalized matches')
            router.push('/questionnaire')
          } else {
            toast.error('Failed to load university matches. Please try again.')
          }
        } else {
          toast.error('Failed to load university matches. Please try again.')
        }
      } finally {
        setIsLoading(false)
        isLoadingRef.current = false
      }
    }

    checkAuthAndLoadUniversities()
  }, [router])

  // Filter universities based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredUniversities(universities)
      return
    }

    const filtered = universities.filter(uni => {
      const query = searchQuery.toLowerCase()
      
      // Helper function to safely check programs
      const checkPrograms = (programs: any) => {
        if (!programs) return false
        
        // Convert to array if it's a string or object
        let programsArray = programs
        if (typeof programs === 'string') {
          try {
            programsArray = JSON.parse(programs)
          } catch {
            return false
          }
        }
        
        if (!Array.isArray(programsArray)) {
          return false
        }
        
        return programsArray.some((program: any) => 
          program.name && program.name.toLowerCase().includes(query) ||
          (program.field && program.field.toLowerCase().includes(query))
        )
      }

      return (
        (uni.name && uni.name.toLowerCase().includes(query)) ||
        (uni.city && uni.city.toLowerCase().includes(query)) ||
        (uni.state && uni.state.toLowerCase().includes(query)) ||
        (uni.country && uni.country.toLowerCase().includes(query)) ||
        checkPrograms(uni.programs)
      )
    })

    setFilteredUniversities(filtered)
  }, [searchQuery, universities])

  const toggleFavorite = (universityId: string) => {
    setFavorites(prev => 
      prev.includes(universityId) 
        ? prev.filter(id => id !== universityId)
        : [...prev, universityId]
    )
  }

  const handleUniversityClick = (universityId: string) => {
    // Navigate to university detail page
    router.push(`/universities/${universityId}`)
  }

  const handleRegenerateSuggestions = async () => {
    setIsRegenerating(true)
    try {
      // Show loading toast
      const loadingToast = toast.loading('Regenerating your university matches...')
      
      // Call the regenerate API
      const result = await api.regenerateSuggestions(true, 20)
      
      // Dismiss loading toast
      toast.dismiss(loadingToast)
      
      // Show success message
      toast.success(result.message)
      
      // Fetch the new suggestions
      const suggestionsResponse = await api.getUserSuggestions(20)
      
      if (suggestionsResponse.suggestions && suggestionsResponse.suggestions.length > 0) {
        // Extract university data from saved suggestions
        const universityData = suggestionsResponse.suggestions
          .map((suggestion: any) => suggestion.university_data)
          .filter(Boolean)
        
        // Update state with new suggestions
        setUniversities(universityData)
        setFilteredUniversities(universityData)
        
        // Update suggestion stats
        setSuggestionStats(suggestionsResponse.stats)
        
        console.log('Successfully regenerated and loaded new suggestions:', universityData.length)
      } else {
        toast.error('No suggestions were generated. Please try again.')
      }
    } catch (error) {
      console.error('Error regenerating suggestions:', error)
      
      // Handle different types of errors
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          toast.error('Please log in to regenerate suggestions')
          router.push('/login')
        } else if (error.message.includes('400') || error.message.includes('questionnaire')) {
          toast.error('Please complete the questionnaire first to get personalized matches')
          router.push('/questionnaire')
        } else {
          toast.error('Failed to regenerate suggestions. Please try again.')
        }
      } else {
        toast.error('Failed to regenerate suggestions. Please try again.')
      }
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleClearSuggestions = async () => {
    // Add confirmation dialog
    if (!confirm('Are you sure you want to clear all your university suggestions? This action cannot be undone.')) {
      return
    }
    
    try {
      // Show loading toast
      const loadingToast = toast.loading('Clearing suggestions...')
      
      const result = await api.clearUserSuggestions()
      
      // Dismiss loading toast
      toast.dismiss(loadingToast)
      
      if (result.cleared) {
        toast.success('Suggestions cleared successfully')
        setUniversities([])
        setFilteredUniversities([])
        setSuggestionStats(null)
      } else {
        toast.success('No suggestions to clear')
      }
    } catch (error) {
      console.error('Error clearing suggestions:', error)
      toast.error('Failed to clear suggestions. Please try again.')
    }
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
      return `$${university.tuition_domestic.toLocaleString()}`
    }
    return 'Not available'
  }

  const formatAcceptanceRate = (rate: number | undefined) => {
    if (rate) {
      return `${(rate * 100).toFixed(1)}%`
    }
    return 'Not available'
  }

  const formatStudentLife = (studentLife: any) => {
    if (!studentLife) return null
    
    try {
      const data = typeof studentLife === 'string' ? JSON.parse(studentLife) : studentLife
      if (typeof data === 'object' && data !== null) {
        const categories = Object.keys(data)
        return `${categories.length} categories available`
      }
    } catch (e) {
      // Ignore parsing errors
    }
    return null
  }

  const formatRankings = (university: University) => {
    const rankings = []
    if (university.world_ranking) rankings.push(`World: #${university.world_ranking}`)
    if (university.national_ranking) rankings.push(`National: #${university.national_ranking}`)
    if (university.regional_ranking) rankings.push(`Regional: #${university.regional_ranking}`)
    return rankings.length > 0 ? rankings.join(' • ') : 'Not available'
  }

  const formatPrograms = (programs: any) => {
    if (!programs) return 'Not available'
    
    try {
      // Convert to array if it's a string or object
      let programsArray = programs
      if (typeof programs === 'string') {
        programsArray = JSON.parse(programs)
      }
      
      if (Array.isArray(programsArray)) {
        return `${programsArray.length} programs available`
      }
      
      return 'Not available'
    } catch (e) {
      // Ignore parsing errors
      return 'Not available'
    }
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
    <AppLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Page Header with Actions */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Your University Matches</h1>
              <p className="text-muted-foreground">
                Discover universities that match your profile and preferences
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                {filteredUniversities.length} Matches Found
              </Badge>
              <Button
                variant="outline"
                size="sm"
                asChild
              >
                <Link href="/browse">
                  Browse All Universities
                </Link>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRegenerateSuggestions}
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
                    Regenerating...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Regenerate
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearSuggestions}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
        </div>

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

          {/* Suggestion Stats Section */}
          {suggestionStats && (
            <div className="mb-6">
              <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {suggestionStats.total_suggestions || universities.length}
                      </div>
                      <div className="text-sm text-muted-foreground">Total Matches</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {suggestionStats.average_score ? `${(suggestionStats.average_score * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-muted-foreground">Avg. Match Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {suggestionStats.highest_score ? `${(suggestionStats.highest_score * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-muted-foreground">Best Match</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {suggestionStats.last_updated ? new Date(suggestionStats.last_updated).toLocaleDateString() : 'N/A'}
                      </div>
                      <div className="text-sm text-muted-foreground">Last Updated</div>
                    </div>
                  </div>
                  {suggestionStats.matching_methods && Object.keys(suggestionStats.matching_methods).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-blue-200">
                      <div className="text-sm text-muted-foreground mb-2">Matching Methods Used:</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(suggestionStats.matching_methods).map(([method, count]) => (
                          <Badge key={method} variant="outline" className="text-xs">
                            {method}: {String(count)}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

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
                      <div className="flex items-center space-x-2 mb-2">
                        {university.world_ranking && (
                          <Badge variant="outline" className="text-xs">
                            #{university.world_ranking} World
                          </Badge>
                        )}
                        {university.national_ranking && (
                          <Badge variant="outline" className="text-xs">
                            #{university.national_ranking} National
                          </Badge>
                        )}
                        {university.regional_ranking && (
                          <Badge variant="outline" className="text-xs">
                            #{university.regional_ranking} Regional
                          </Badge>
                        )}
                      </div>
                      {university.type && (
                        <Badge variant="secondary" className="text-xs">
                          {university.type}
                        </Badge>
                      )}
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
                  <p className="text-sm text-muted-foreground line-clamp-2">
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
                    {university.student_faculty_ratio && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Student-Faculty Ratio:</span>
                        <span className="font-medium">{university.student_faculty_ratio}:1</span>
                      </div>
                    )}
                    {university.international_students_percentage && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">International Students:</span>
                        <span className="font-medium">{university.international_students_percentage}%</span>
                      </div>
                    )}
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Programs:</span>
                      <span className="font-medium">{formatPrograms(university.programs)}</span>
                    </div>
                    {formatStudentLife(university.student_life) && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Student Life:</span>
                        <span className="font-medium">{formatStudentLife(university.student_life)}</span>
                      </div>
                    )}
                    {university.campus_size && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Campus:</span>
                        <span className="font-medium">{university.campus_size}</span>
                      </div>
                    )}
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
      </AppLayout>
    )
  } 