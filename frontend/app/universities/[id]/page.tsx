'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  ArrowLeft, 
  MapPin, 
  GraduationCap, 
  Star, 
  Users, 
  DollarSign,
  Globe,
  Phone,
  Mail,
  Calendar,
  Building,
  Award,
  BookOpen,
  Heart,
  ExternalLink,
  Clock,
  UserCheck
} from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { apiService, University } from '@/lib/api'

export default function UniversityDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [university, setUniversity] = useState<University | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isFavorite, setIsFavorite] = useState(false)

  const universityId = parseInt(params.id as string)

  useEffect(() => {
    const loadUniversity = async () => {
      if (!universityId || isNaN(universityId)) {
        toast.error('Invalid university ID')
        router.push('/universities')
        return
      }

      setIsLoading(true)
      try {
        const data = await apiService.getUniversity(universityId)
        setUniversity(data)
        toast.success('University details loaded successfully!')
      } catch (error) {
        console.error('Error loading university:', error)
        toast.error('Failed to load university details')
        router.push('/universities')
      } finally {
        setIsLoading(false)
      }
    }

    loadUniversity()
  }, [universityId, router])

  const toggleFavorite = () => {
    setIsFavorite(!isFavorite)
    toast.success(isFavorite ? 'Removed from favorites' : 'Added to favorites')
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
          <p className="text-lg font-medium">Loading university details...</p>
          <p className="text-muted-foreground">This may take a few moments</p>
        </div>
      </div>
    )
  }

  if (!university) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <GraduationCap className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">University not found</h3>
          <p className="text-muted-foreground mb-4">
            The university you're looking for doesn't exist or has been removed.
          </p>
          <Button asChild>
            <Link href="/universities">
              Back to Universities
            </Link>
          </Button>
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
                href="/universities" 
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Universities
              </Link>
              <div className="flex items-center space-x-2">
                <GraduationCap className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold">{university.name}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleFavorite}
                className={`p-2 ${isFavorite ? 'text-red-500' : 'text-muted-foreground'}`}
              >
                <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
              </Button>
              {university.website && (
                <Button variant="outline" size="sm" asChild>
                  <a href={university.website} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Visit Website
                  </a>
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* University Overview */}
        <div className="mb-8">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Main Info */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-2xl">{university.name}</CardTitle>
                  <CardDescription className="flex items-center text-base">
                    <MapPin className="h-4 w-4 mr-2" />
                    {formatLocation(university)}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {university.description && (
                    <p className="text-muted-foreground leading-relaxed">
                      {university.description}
                    </p>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {university.world_ranking && (
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">#{university.world_ranking}</div>
                        <div className="text-sm text-muted-foreground">World Ranking</div>
                      </div>
                    )}
                    {university.national_ranking && (
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">#{university.national_ranking}</div>
                        <div className="text-sm text-muted-foreground">National Ranking</div>
                      </div>
                    )}
                    {university.acceptance_rate && (
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{formatAcceptanceRate(university.acceptance_rate)}</div>
                        <div className="text-sm text-muted-foreground">Acceptance Rate</div>
                      </div>
                    )}
                    {university.student_population && (
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{university.student_population.toLocaleString()}</div>
                        <div className="text-sm text-muted-foreground">Students</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Stats */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Quick Facts</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {university.founded_year && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Founded</span>
                      <span className="font-medium">{university.founded_year}</span>
                    </div>
                  )}
                  {university.type && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Type</span>
                      <Badge variant="secondary">{university.type}</Badge>
                    </div>
                  )}
                  {university.faculty_count && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Faculty</span>
                      <span className="font-medium">{university.faculty_count.toLocaleString()}</span>
                    </div>
                  )}
                  {university.tuition_domestic && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Domestic Tuition</span>
                      <span className="font-medium">${university.tuition_domestic.toLocaleString()}</span>
                    </div>
                  )}
                  {university.tuition_international && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">International Tuition</span>
                      <span className="font-medium">${university.tuition_international.toLocaleString()}</span>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Contact Info */}
              {(university.phone || university.email || university.website) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Contact Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {university.phone && (
                      <div className="flex items-center space-x-2">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{university.phone}</span>
                      </div>
                    )}
                    {university.email && (
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{university.email}</span>
                      </div>
                    )}
                    {university.website && (
                      <div className="flex items-center space-x-2">
                        <Globe className="h-4 w-4 text-muted-foreground" />
                        <a 
                          href={university.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          Visit Website
                        </a>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Information Tabs */}
        <Tabs defaultValue="programs" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="programs">Programs</TabsTrigger>
            <TabsTrigger value="facilities">Facilities</TabsTrigger>
            <TabsTrigger value="about">About</TabsTrigger>
            <TabsTrigger value="admissions">Admissions</TabsTrigger>
          </TabsList>

          <TabsContent value="programs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BookOpen className="h-5 w-5 mr-2" />
                  Academic Programs
                </CardTitle>
              </CardHeader>
              <CardContent>
                {university.programs && university.programs.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {university.programs.map((program) => (
                      <Card key={program.id} className="p-4">
                        <div className="space-y-2">
                          <h4 className="font-semibold">{program.name}</h4>
                          {program.level && (
                            <Badge variant="outline">{program.level}</Badge>
                          )}
                          {program.field && (
                            <Badge variant="secondary">{program.field}</Badge>
                          )}
                          {program.duration && (
                            <div className="flex items-center text-sm text-muted-foreground">
                              <Clock className="h-4 w-4 mr-1" />
                              {program.duration}
                            </div>
                          )}
                          {program.tuition && (
                            <div className="flex items-center text-sm text-muted-foreground">
                              <DollarSign className="h-4 w-4 mr-1" />
                              ${program.tuition.toLocaleString()}/year
                            </div>
                          )}
                          {program.description && (
                            <p className="text-sm text-muted-foreground">{program.description}</p>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No program information available.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="facilities" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Building className="h-5 w-5 mr-2" />
                  Campus Facilities
                </CardTitle>
              </CardHeader>
              <CardContent>
                {university.facilities && university.facilities.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {university.facilities.map((facility) => (
                      <Card key={facility.id} className="p-4">
                        <div className="space-y-2">
                          <h4 className="font-semibold">{facility.name}</h4>
                          {facility.type && (
                            <Badge variant="outline">{facility.type}</Badge>
                          )}
                          {facility.capacity && (
                            <div className="flex items-center text-sm text-muted-foreground">
                              <Users className="h-4 w-4 mr-1" />
                              Capacity: {facility.capacity.toLocaleString()}
                            </div>
                          )}
                          {facility.description && (
                            <p className="text-sm text-muted-foreground">{facility.description}</p>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No facility information available.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="about" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2">
              {university.mission_statement && (
                <Card>
                  <CardHeader>
                    <CardTitle>Mission Statement</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">
                      {university.mission_statement}
                    </p>
                  </CardContent>
                </Card>
              )}
              
              {university.vision_statement && (
                <Card>
                  <CardHeader>
                    <CardTitle>Vision Statement</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">
                      {university.vision_statement}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="admissions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <UserCheck className="h-5 w-5 mr-2" />
                  Admissions Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <h4 className="font-semibold">Key Statistics</h4>
                    <div className="space-y-2">
                      {university.acceptance_rate && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Acceptance Rate</span>
                          <span className="font-medium">{formatAcceptanceRate(university.acceptance_rate)}</span>
                        </div>
                      )}
                      {university.student_population && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Total Students</span>
                          <span className="font-medium">{university.student_population.toLocaleString()}</span>
                        </div>
                      )}
                      {university.faculty_count && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Faculty Members</span>
                          <span className="font-medium">{university.faculty_count.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold">Financial Information</h4>
                    <div className="space-y-2">
                      {university.tuition_domestic && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Domestic Tuition</span>
                          <span className="font-medium">${university.tuition_domestic.toLocaleString()}/year</span>
                        </div>
                      )}
                      {university.tuition_international && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">International Tuition</span>
                          <span className="font-medium">${university.tuition_international.toLocaleString()}/year</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <Separator />
                
                <div className="text-center">
                  <Button size="lg" className="mr-4">
                    Apply Now
                  </Button>
                  <Button variant="outline" size="lg">
                    Request Information
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
} 