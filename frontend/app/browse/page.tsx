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
  Globe,
  Building,
  BookOpen
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, University } from '@/lib/api'
import AppLayout from '@/components/layout/AppLayout'

export default function BrowseUniversitiesPage() {
  const router = useRouter()
  const [universities, setUniversities] = useState<University[]>([])
  const [filteredUniversities, setFilteredUniversities] = useState<University[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [favorites, setFavorites] = useState<string[]>([])
  const [filters, setFilters] = useState({
    country: '',
    state: '',
    type: '',
    hasRanking: false,
    hasPrograms: false,
    minAcceptanceRate: '',
    maxAcceptanceRate: '',
    minTuition: '',
    maxTuition: '',
    minStudentPopulation: '',
    maxStudentPopulation: '',
    hasInternationalStudents: false,
    hasFinancialAid: false
  })
  const isLoadingRef = useRef(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  // Initial load effect
  useEffect(() => {
    const checkAuthAndLoadUniversities = async () => {
      if (isLoadingRef.current) return;
      isLoadingRef.current = true;
      setIsLoading(true);

      try {
        const isAuth = await api.isAuthenticated();
        if (!isAuth) {
          toast.error('Please log in to browse universities')
          router.push('/login')
          return
        }

        const response = await api.browseUniversities({
          limit: 1000,
        })
        
        setUniversities(response.universities)
        setFilteredUniversities(response.universities)
        toast.success(`Loaded ${response.universities.length} universities successfully!`)
      } catch (error) {
        console.error('Error loading universities:', error)
        
        if (error instanceof Error) {
          if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            toast.error('Please log in to browse universities')
            router.push('/login')
          } else {
            toast.error('Failed to load universities. Please try again.')
          }
        } else {
          toast.error('Failed to load universities. Please try again.')
        }
      } finally {
        setIsLoading(false)
        isLoadingRef.current = false
      }
    }

    checkAuthAndLoadUniversities()
  }, [router])

  // Debounced search effect
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    searchTimeoutRef.current = setTimeout(() => {
      const loadUniversities = async () => {
        if (isLoadingRef.current) return;
        isLoadingRef.current = true;
        setIsLoading(true);

        try {
          const response = await api.browseUniversities({
            limit: 1000,
            search: searchQuery || undefined,
            country: filters.country || undefined,
            state: filters.state || undefined,
            type: filters.type || undefined,
            hasRanking: filters.hasRanking || undefined,
            hasPrograms: filters.hasPrograms || undefined,
            minAcceptanceRate: filters.minAcceptanceRate ? parseFloat(filters.minAcceptanceRate) : undefined,
            maxAcceptanceRate: filters.maxAcceptanceRate ? parseFloat(filters.maxAcceptanceRate) : undefined,
            minTuition: filters.minTuition ? parseFloat(filters.minTuition) : undefined,
            maxTuition: filters.maxTuition ? parseFloat(filters.maxTuition) : undefined,
            minStudentPopulation: filters.minStudentPopulation ? parseInt(filters.minStudentPopulation) : undefined,
            maxStudentPopulation: filters.maxStudentPopulation ? parseInt(filters.maxStudentPopulation) : undefined
          })
          
          setUniversities(response.universities)
          setFilteredUniversities(response.universities)
        } catch (error) {
          console.error('Error searching universities:', error)
          toast.error('Failed to search universities. Please try again.')
        } finally {
          setIsLoading(false)
          isLoadingRef.current = false
        }
      }

      loadUniversities()
    }, 500)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchQuery, filters])

  const toggleFavorite = (universityId: string) => {
    setFavorites(prev => 
      prev.includes(universityId) 
        ? prev.filter(id => id !== universityId)
        : [...prev, universityId]
    )
  }

  const handleUniversityClick = (universityId: string) => {
    router.push(`/universities/${universityId}`)
  }

  const clearFilters = () => {
    setFilters({
      country: '',
      state: '',
      type: '',
      hasRanking: false,
      hasPrograms: false,
      minAcceptanceRate: '',
      maxAcceptanceRate: '',
      minTuition: '',
      maxTuition: '',
      minStudentPopulation: '',
      maxStudentPopulation: '',
      hasInternationalStudents: false,
      hasFinancialAid: false
    })
    setSearchQuery('')
  }

  const handleFilterChange = (filterType: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }))
  }

  const getUniqueCountries = () => {
    const countries = universities
      .map(uni => uni.country)
      .filter(Boolean)
      .filter((country, index, arr) => arr.indexOf(country) === index)
      .sort()
    return countries
  }

  const getUniqueStates = () => {
    const states = universities
      .map(uni => uni.state)
      .filter(Boolean)
      .filter((state, index, arr) => arr.indexOf(state) === index)
      .sort()
    return states
  }

  const getUniqueTypes = () => {
    const types = universities
      .map(uni => uni.type)
      .filter(Boolean)
      .filter((type, index, arr) => arr.indexOf(type) === index)
      .sort()
    return types
  }

  const getActiveFiltersCount = () => {
    let count = 0
    if (filters.country) count++
    if (filters.state) count++
    if (filters.type) count++
    if (filters.hasRanking) count++
    if (filters.hasPrograms) count++
    if (filters.minAcceptanceRate) count++
    if (filters.maxAcceptanceRate) count++
    if (filters.minTuition) count++
    if (filters.maxTuition) count++
    if (filters.minStudentPopulation) count++
    if (filters.maxStudentPopulation) count++
    if (filters.hasInternationalStudents) count++
    if (filters.hasFinancialAid) count++
    return count
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
      let programsArray = programs
      if (typeof programs === 'string') {
        programsArray = JSON.parse(programs)
      }
      
      if (Array.isArray(programsArray)) {
        return `${programsArray.length} programs available`
      }
      
      return 'Not available'
    } catch (e) {
      return 'Not available'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg font-medium">Loading universities...</p>
          <p className="text-muted-foreground">This may take a few moments</p>
        </div>
      </div>
    )
  }

  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Browse Universities</h1>
              <p className="text-muted-foreground">
                Explore universities from around the world
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                {filteredUniversities.length} Universities Found
              </Badge>
            </div>
          </div>
        </div>

        {/* Search and Filter Section */}
        <div className="mb-8">
          {/* Filter Controls Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Search & Filter</h2>
            <div className="flex items-center space-x-2">
              {getActiveFiltersCount() > 0 && (
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  Clear All Filters
                </Button>
              )}
            </div>
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-center justify-between mb-6">
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
                Sort by Name
              </Button>
            </div>
          </div>

          {/* Advanced Filters - Always Visible */}
          <div className="p-6 bg-white rounded-lg border shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Filters</h3>
              {getActiveFiltersCount() > 0 && (
                <Badge variant="secondary" className="bg-primary text-primary-foreground">
                  {getActiveFiltersCount()} Active
                </Badge>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Location Filters */}
              <div className="space-y-4">
                <h4 className="font-medium text-sm text-muted-foreground">Location</h4>
                <div>
                  <label className="text-sm font-medium mb-2 block">Country</label>
                  <select
                    value={filters.country}
                    onChange={(e) => handleFilterChange('country', e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="">All Countries</option>
                    {getUniqueCountries().map(country => (
                      <option key={country} value={country}>{country}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">State/Province</label>
                  <select
                    value={filters.state}
                    onChange={(e) => handleFilterChange('state', e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="">All States</option>
                    {getUniqueStates().map(state => (
                      <option key={state} value={state}>{state}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">University Type</label>
                  <select
                    value={filters.type}
                    onChange={(e) => handleFilterChange('type', e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="">All Types</option>
                    {getUniqueTypes().map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Academic Filters */}
              <div className="space-y-4">
                <h4 className="font-medium text-sm text-muted-foreground">Academic</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Min Acceptance Rate (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={filters.minAcceptanceRate}
                      onChange={(e) => handleFilterChange('minAcceptanceRate', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Max Acceptance Rate (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={filters.maxAcceptanceRate}
                      onChange={(e) => handleFilterChange('maxAcceptanceRate', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="100"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Min Tuition ($)</label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={filters.minTuition}
                      onChange={(e) => handleFilterChange('minTuition', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Max Tuition ($)</label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={filters.maxTuition}
                      onChange={(e) => handleFilterChange('maxTuition', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="100000"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Min Students</label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={filters.minStudentPopulation}
                      onChange={(e) => handleFilterChange('minStudentPopulation', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Max Students</label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={filters.maxStudentPopulation}
                      onChange={(e) => handleFilterChange('maxStudentPopulation', e.target.value)}
                      className="w-full p-2 border rounded-md text-sm"
                      placeholder="100000"
                    />
                  </div>
                </div>
              </div>

              {/* Features Filters */}
              <div className="space-y-4">
                <h4 className="font-medium text-sm text-muted-foreground">Features</h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="hasRanking"
                      checked={filters.hasRanking}
                      onChange={(e) => handleFilterChange('hasRanking', e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="hasRanking" className="text-sm">Has Rankings</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="hasPrograms"
                      checked={filters.hasPrograms}
                      onChange={(e) => handleFilterChange('hasPrograms', e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="hasPrograms" className="text-sm">Has Programs</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="hasInternationalStudents"
                      checked={filters.hasInternationalStudents}
                      onChange={(e) => handleFilterChange('hasInternationalStudents', e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="hasInternationalStudents" className="text-sm">International Students</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="hasFinancialAid"
                      checked={filters.hasFinancialAid}
                      onChange={(e) => handleFilterChange('hasFinancialAid', e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="hasFinancialAid" className="text-sm">Financial Aid Available</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <p className="text-muted-foreground">
            Browse through our comprehensive database of universities worldwide.
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
            <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No universities found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search terms or filters
            </p>
            <Button onClick={clearFilters}>
              Clear All Filters
            </Button>
          </div>
        )}

        {/* Action Section */}
        <div className="mt-12 text-center">
          <Card className="gradient-bg text-white border-0">
            <CardContent className="pt-8 pb-8">
              <h3 className="text-xl font-bold mb-2">Want Personalized Matches?</h3>
              <p className="text-white/90 mb-6">
                Get AI-powered recommendations based on your personality and preferences
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button variant="secondary" asChild>
                  <Link href="/universities">
                    View My Matches
                  </Link>
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white hover:text-primary" asChild>
                  <Link href="/questionnaire">
                    Take Questionnaire
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
} 