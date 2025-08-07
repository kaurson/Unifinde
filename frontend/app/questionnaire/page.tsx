'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, ArrowRight, Brain, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, Question, UserAnswer } from '@/lib/api'
import { QuestionComponent } from '@/components/questionnaire/QuestionComponents'

export default function QuestionnairePage() {
  const router = useRouter()
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<{ [key: string]: any }>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)

  // Check authentication on component mount
  useEffect(() => {
    const checkAuth = () => {
      const auth = api.isAuthenticated()
      setIsAuthenticated(auth)
      
      if (!auth) {
        toast.error('Please login to take the questionnaire')
        router.push('/login')
        return
      }
    }

    checkAuth()
  }, [router])

  // Fetch questions from database
  useEffect(() => {
    const fetchQuestions = async () => {
      if (isAuthenticated === null) return // Wait for auth check
      
      try {
        const fetchedQuestions = await api.getQuestions()
        setQuestions(fetchedQuestions.sort((a, b) => a.order_index - b.order_index))
      } catch (error) {
        console.error('Error fetching questions:', error)
        toast.error('Failed to load questions. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    // Only fetch questions if user is authenticated
    if (isAuthenticated) {
      fetchQuestions()
    }
  }, [isAuthenticated])

  const handleAnswer = (answer: any) => {
    const currentQ = questions[currentQuestion]
    if (currentQ) {
      setAnswers(prev => ({
        ...prev,
        [currentQ.id]: answer
      }))
    }
  }

  const handleNext = async () => {
    const currentQ = questions[currentQuestion]
    if (!currentQ) return

    if (answers[currentQ.id] === null || answers[currentQ.id] === undefined || answers[currentQ.id] === '') {
      toast.error('Please answer the question before continuing')
      return
    }

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
    } else {
      // Submit questionnaire and redirect to universities
      await handleSubmit()
    }
  }

  const handleSubmit = async () => {
    // Check authentication before submitting
    if (!api.isAuthenticated()) {
      toast.error('Please login to submit the questionnaire')
      router.push('/login')
      return
    }

    setIsSubmitting(true)
    
    try {
      // Convert answers to the format expected by the API
      const answerData: UserAnswer[] = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer_text: String(answer),
        answer_data: { value: answer }
      }))

      const submissionData = {
        answers: answerData,
        preferred_majors: [],
        preferred_locations: []
      }

      console.log('Submitting questionnaire:', submissionData)
      
      // Submit to API
      await api.submitQuestionnaire(submissionData)
      
      // Get current user profile to get the ID
      const userProfile = await api.getProfile()
      
      toast.success('Questionnaire completed! Redirecting to your summary...')
      
      // Redirect to summary page
      router.push(`/summary/${userProfile.id}`)
    } catch (error) {
      console.error('Error submitting questionnaire:', error)
      toast.error('Failed to submit questionnaire. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSkipQuestionnaire = async () => {
    // Check authentication before submitting
    if (!api.isAuthenticated()) {
      toast.error('Please login to submit the questionnaire')
      router.push('/login')
      return
    }

    setIsSubmitting(true)
    
    try {
      // Get actual questions from database to use real IDs
      const actualQuestions = await api.getQuestions()
      const sortedQuestions = actualQuestions.sort((a, b) => a.order_index - b.order_index)
      
      // Sample data for testing using real question IDs
      const sampleAnswers: UserAnswer[] = sortedQuestions.map((question, index) => {
        // Generate appropriate sample answers based on question type
        let sampleAnswer: any = ''
        
        switch (question.question_type) {
          case 'boolean':
            sampleAnswer = index % 2 === 0 ? true : false
            break
          case 'text':
            sampleAnswer = `Sample answer for question ${index + 1}: I am interested in learning and personal growth.`
            break
          case 'integer':
            sampleAnswer = Math.floor(Math.random() * 10) + 1
            break
          case 'float':
            sampleAnswer = (Math.random() * 10).toFixed(1)
            break
          case 'scale_0_10':
            sampleAnswer = Math.floor(Math.random() * 11)
            break
          case 'multiple_choice_3':
            sampleAnswer = ['breakfast', 'lunch', 'midnight snack'][index % 3]
            break
          case 'multiple_choice_5':
            sampleAnswer = ['Take turns chewing it', 'chew it together at the same time', 'take it yourself', 'throw it away (no one deserves it)', 'Give it to your friend'][index % 5]
            break
          default:
            sampleAnswer = `Sample answer for question ${index + 1}`
        }
        
        return {
          question_id: question.id,
          answer_text: String(sampleAnswer),
          answer_data: { value: sampleAnswer }
        }
      })

      const submissionData = {
        answers: sampleAnswers,
        preferred_majors: ["Computer Science", "Engineering", "Data Science"],
        preferred_locations: ["United States", "Canada", "United Kingdom"]
      }

      console.log('Submitting sample questionnaire data:', submissionData)
      
      // Submit to API
      await api.submitQuestionnaire(submissionData)
      
      // Get current user profile to get the ID
      const userProfile = await api.getProfile()
      
      toast.success('Sample questionnaire submitted! Redirecting to your summary...')
      
      // Redirect to summary page
      router.push(`/summary/${userProfile.id}`)
    } catch (error) {
      console.error('Error submitting sample questionnaire:', error)
      toast.error('Failed to submit sample questionnaire. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Show loading while checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-lg">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // Don't render anything if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-lg mb-4">Please login to access the questionnaire.</p>
          <Link href="/login" className="text-primary hover:underline">
            Go to Login
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-lg">Loading questions...</p>
        </div>
      </div>
    )
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-lg mb-4">No questions available.</p>
          <Link href="/" className="text-primary hover:underline">
            Return to home
          </Link>
        </div>
      </div>
    )
  }

  const currentQ = questions[currentQuestion]
  const hasAnswered = currentQ && (answers[currentQ.id] !== null && answers[currentQ.id] !== undefined && answers[currentQ.id] !== '')

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Back to Home */}
        <div className="mb-6">
          <Link 
            href="/" 
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Brain className="h-8 w-8 text-primary mr-2" />
            <span className="text-2xl font-bold gradient-text">Personality Questionnaire</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Help Us Understand You</h1>
          <p className="text-muted-foreground">
            Answer a few questions to help us find your perfect university match
          </p>
          
          {/* Skip Questionnaire Button for Testing */}
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSkipQuestionnaire}
              disabled={isSubmitting}
              className="text-xs"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Submitting...
                </>
              ) : (
                '🚀 Skip Questionnaire (Testing)'
              )}
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-muted-foreground">
              Question {currentQuestion + 1} of {questions.length}
            </span>
            <span className="text-sm font-medium">
              {Math.round(((currentQuestion + 1) / questions.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <Card className="shadow-lg border-0">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Question {currentQuestion + 1}</CardTitle>
            <CardDescription>
              Please answer honestly - there are no right or wrong answers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Question */}
            <div className="text-center">
              <p className="text-lg font-medium mb-6">{currentQ.question_text}</p>
            </div>

            {/* Question Component */}
            <QuestionComponent
              question={currentQ}
              answer={answers[currentQ.id]}
              onAnswer={handleAnswer}
            />

            <Separator />

            {/* Navigation */}
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                disabled={currentQuestion === 0}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>

              <Button
                onClick={handleNext}
                disabled={!hasAnswered || isSubmitting}
                className="min-w-[120px]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : currentQuestion === questions.length - 1 ? (
                  <>
                    Complete
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info Section */}
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground mb-4">
            Your answers help our AI understand your personality and preferences to find the best university matches.
          </p>
          <div className="flex justify-center space-x-6 text-xs text-muted-foreground">
            <div className="flex items-center">
              <Brain className="h-3 w-3 mr-1" />
              <span>AI Analysis</span>
            </div>
            <div className="flex items-center">
              <ArrowRight className="h-3 w-3 mr-1" />
              <span>University Matches</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 