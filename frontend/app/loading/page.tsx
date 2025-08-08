'use client'

import React, { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'
import { 
  GraduationCap, 
  Brain, 
  Search, 
  Star, 
  Globe, 
  Users,
  Zap,
  Sparkles,
  Loader2
} from 'lucide-react'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

export default function LoadingPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [currentStep, setCurrentStep] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  
  const userId = searchParams.get('userId')
  const redirectTo = searchParams.get('redirectTo') || '/universities'

  const loadingSteps = [
    {
      icon: Brain,
      title: "Analyzing Your Personality",
      description: "Processing your questionnaire responses...",
      color: "text-blue-600"
    },
    {
      icon: Search,
      title: "Searching Universities",
      description: "Finding the perfect matches for you...",
      color: "text-green-600"
    },
    {
      icon: Star,
      title: "Calculating Match Scores",
      description: "Computing compatibility scores...",
      color: "text-yellow-600"
    },
    {
      icon: Globe,
      title: "Exploring Programs",
      description: "Discovering academic opportunities...",
      color: "text-purple-600"
    },
    {
      icon: Users,
      title: "Finalizing Results",
      description: "Preparing your personalized recommendations...",
      color: "text-pink-600"
    }
  ]

  // Loop through steps continuously
  useEffect(() => {
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % loadingSteps.length)
    }, 2000) // Change step every 2 seconds

    return () => clearInterval(stepInterval)
  }, [loadingSteps.length])

  // Handle API call and redirect
  useEffect(() => {
    const generateSuggestions = async () => {
      if (isGenerating) return
      
      setIsGenerating(true)
      
      try {
        console.log('Generating collection matches...')
        const matchesResponse = await api.generateCollectionMatches(20)
        console.log('Generated matches:', matchesResponse)
        
        // Wait a moment to show completion
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Redirect to the appropriate page
        if (userId && redirectTo === '/summary') {
          router.push(`/summary/${userId}`)
        } else {
          router.push(redirectTo)
        }
        
      } catch (error) {
        console.error('Error generating suggestions:', error)
        toast.error('Failed to generate suggestions. Please try again.')
        
        // Still redirect after error, but to universities page
        setTimeout(() => {
          router.push('/universities')
        }, 2000)
      } finally {
        setIsGenerating(false)
      }
    }

    generateSuggestions()
  }, [userId, redirectTo, router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <GraduationCap className="h-12 w-12 text-primary animate-bounce" />
              <Sparkles className="h-6 w-6 text-yellow-500 absolute -top-2 -right-2 animate-pulse" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Creating Your Perfect Matches
          </h1>
          <p className="text-lg text-muted-foreground">
            Our AI is working hard to find the best universities for you!
          </p>
        </div>

        {/* Loading Steps */}
        <div className="space-y-4">
          {loadingSteps.map((step, index) => {
            const Icon = step.icon
            const isActive = index === currentStep
            
            return (
              <Card 
                key={index} 
                className={`transition-all duration-700 ${
                  isActive 
                    ? 'ring-2 ring-primary shadow-lg scale-105 opacity-100' 
                    : 'opacity-30 scale-100'
                }`}
              >
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className={`relative ${step.color}`}>
                      <Icon className={`h-8 w-8 ${
                        isActive ? 'animate-pulse' : ''
                      }`} />
                    </div>
                    <div className="flex-1">
                      <h3 className={`font-semibold transition-colors duration-700 ${
                        isActive ? 'text-primary' : 'text-gray-700'
                      }`}>
                        {step.title}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {step.description}
                      </p>
                    </div>
                    {isActive && (
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Fun Facts */}
        <div className="mt-8 text-center">
          <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <Zap className="h-5 w-5 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Fun Fact</span>
              </div>
              <p className="text-sm text-yellow-700">
                {currentStep === 0 && "We're analyzing thousands of universities worldwide..."}
                {currentStep === 1 && "Did you know? There are over 20,000 universities globally!"}
                {currentStep === 2 && "Our AI considers 50+ factors to find your perfect match..."}
                {currentStep === 3 && "We're matching you with students who share your interests..."}
                {currentStep === 4 && "Almost there! Your personalized recommendations are ready..."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Loading Indicator */}
        {isGenerating && (
          <div className="mt-6 text-center">
            <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Generating your personalized matches...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 