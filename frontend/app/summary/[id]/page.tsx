'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { 
  ArrowLeft, 
  Brain, 
  GraduationCap, 
  MapPin, 
  Star,
  CheckCircle,
  Sparkles,
  User,
  Target,
  Lightbulb,
  ArrowRight
} from 'lucide-react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, User as UserType } from '@/lib/api'

export default function SummaryPage() {
  const params = useParams()
  const router = useRouter()
  const [user, setUser] = useState<UserType | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const userId = params.id as string

  useEffect(() => {
    const loadUserSummary = async () => {
      if (!api.isAuthenticated()) {
        toast.error('Please login to view the summary')
        router.push('/login')
        return
      }

      try {
        const profileData = await api.getProfile()
        setUser(profileData)
      } catch (error) {
        console.error('Error loading user summary:', error)
        toast.error('Failed to load summary')
      } finally {
        setIsLoading(false)
      }
    }

    loadUserSummary()
  }, [userId, router])

  const handleContinueToMatches = () => {
    router.push('/universities')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg">Loading your personality summary...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Summary not found</h3>
          <p className="text-muted-foreground mb-4">
            Unable to load your personality summary.
          </p>
          <Button asChild>
            <Link href="/questionnaire">
              Complete Questionnaire
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  if (!user.personality_summary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No summary available</h3>
          <p className="text-muted-foreground mb-4">
            Please complete the questionnaire to generate your personality summary.
          </p>
          <Button asChild>
            <Link href="/questionnaire">
              Complete Questionnaire
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
                href="/" 
                className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Home
              </Link>
              <div className="flex items-center space-x-2">
                <Brain className="h-6 w-6 text-primary" />
                <span className="text-lg font-bold">Your Personality Summary</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Success Message */}
        <div className="mb-8">
          <div className="flex items-center justify-center mb-4">
            <CheckCircle className="h-12 w-12 text-green-500 mr-4" />
            <div>
              <h1 className="text-3xl font-bold text-green-700">Questionnaire Complete!</h1>
              <p className="text-green-600">Your personality profile has been generated successfully.</p>
            </div>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Summary */}
          <div className="lg:col-span-2 space-y-6">
            {/* Personality Summary Card */}
            <Card className="shadow-lg border-0">
              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-center mb-2">
                  <Brain className="h-8 w-8 text-primary mr-2" />
                  <CardTitle className="text-2xl">Your Personality Summary</CardTitle>
                </div>
                <CardDescription className="text-base">
                  AI-generated insights based on your questionnaire responses
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 p-6 rounded-xl border-2 border-blue-100">
                  <div className="flex items-start space-x-3">
                    <Sparkles className="h-6 w-6 text-purple-500 mt-1 flex-shrink-0" />
                    <p className="text-lg text-gray-800 leading-relaxed italic">
                      "{user.personality_summary}"
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Personality Profile */}
            {user.personality_profile && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="h-5 w-5 mr-2" />
                    Detailed Personality Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Full Analysis Text */}
                  {user.personality_profile.analysis && (
                    <div className="space-y-4">
                      <Label className="text-sm font-medium text-muted-foreground">Complete Analysis</Label>
                      <div className="bg-gray-50 p-4 rounded-lg border">
                        <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                          {user.personality_profile.analysis}
                        </div>
                      </div>
                    </div>
                  )}

                  <Separator />

                  {/* Structured Data */}
                  <div className="grid gap-4 md:grid-cols-2">
                    {user.personality_profile.personality_type && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Personality Type</Label>
                        <Badge variant="secondary" className="text-sm">
                          {user.personality_profile.personality_type}
                        </Badge>
                      </div>
                    )}
                    {user.personality_profile.learning_style && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Learning Style</Label>
                        <Badge variant="secondary" className="text-sm">
                          {user.personality_profile.learning_style}
                        </Badge>
                      </div>
                    )}
                    {user.personality_profile.communication_style && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Communication Style</Label>
                        <Badge variant="secondary" className="text-sm">
                          {user.personality_profile.communication_style}
                        </Badge>
                      </div>
                    )}
                    {user.personality_profile.leadership_style && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Leadership Style</Label>
                        <Badge variant="secondary" className="text-sm">
                          {user.personality_profile.leadership_style}
                        </Badge>
                      </div>
                    )}
                  </div>

                  {user.personality_profile.strengths && user.personality_profile.strengths.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">Key Strengths</Label>
                      <div className="flex flex-wrap gap-2">
                        {user.personality_profile.strengths.map((strength: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-green-700 border-green-200 bg-green-50">
                            <Star className="h-3 w-3 mr-1" />
                            {strength}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {user.personality_profile.areas_for_development && user.personality_profile.areas_for_development.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">Areas for Development</Label>
                      <div className="flex flex-wrap gap-2">
                        {user.personality_profile.areas_for_development.map((area: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-blue-700 border-blue-200 bg-blue-50">
                            <Lightbulb className="h-3 w-3 mr-1" />
                            {area}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {user.personality_profile.confidence_score && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">Confidence Score</Label>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${user.personality_profile.confidence_score * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {Math.round(user.personality_profile.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Academic Preferences Summary */}
            {(user.preferred_majors || user.preferred_locations) && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <GraduationCap className="h-5 w-5 mr-2" />
                    Academic Preferences
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {user.preferred_majors && user.preferred_majors.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">Preferred Majors</Label>
                      <div className="flex flex-wrap gap-2">
                        {user.preferred_majors.map((major, index) => (
                          <Badge key={index} variant="secondary" className="text-sm">
                            {major}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {user.preferred_locations && user.preferred_locations.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">Preferred Locations</Label>
                      <div className="flex flex-wrap gap-2">
                        {user.preferred_locations.map((location, index) => (
                          <Badge key={index} variant="outline" className="text-sm">
                            <MapPin className="h-3 w-3 mr-1" />
                            {location}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Next Steps */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ArrowRight className="h-5 w-5 mr-2" />
                  Next Steps
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" onClick={handleContinueToMatches}>
                  <GraduationCap className="h-4 w-4 mr-2" />
                  View University Matches
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/profile">
                    <User className="h-4 w-4 mr-2" />
                    View Full Profile
                  </Link>
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/questionnaire">
                    <Brain className="h-4 w-4 mr-2" />
                    Retake Questionnaire
                  </Link>
                </Button>
              </CardContent>
            </Card>

            {/* Summary Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Summary Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Profile completion</span>
                  <span className="font-medium text-green-600">100%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Questions answered</span>
                  <span className="font-medium">
                    {user.questionnaire_answers ? Object.keys(user.questionnaire_answers).length : 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Generated at</span>
                  <span className="font-medium">
                    {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : 'Today'}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="h-5 w-5 mr-2" />
                  Tips
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm text-muted-foreground">
                  <p>• Use this summary to guide your university search</p>
                  <p>• Share it with academic advisors</p>
                  <p>• Consider it when writing application essays</p>
                  <p>• Revisit after gaining more experience</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
} 