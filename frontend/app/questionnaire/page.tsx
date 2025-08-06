'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, CheckCircle, XCircle, ArrowRight, Brain } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function QuestionnairePage() {
  const router = useRouter()
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<{ [key: number]: boolean | null }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Simple questionnaire with one true/false question for now
  const questions = [
    {
      id: 1,
      question: "Do you prefer working in teams rather than individually?",
      type: "true_false"
    }
  ]

  const handleAnswer = (answer: boolean) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion]: answer
    }))
  }

  const handleNext = async () => {
    if (answers[currentQuestion] === null || answers[currentQuestion] === undefined) {
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
    setIsSubmitting(true)
    
    try {
      // Here you would typically send the answers to your backend
      // For now, we'll just simulate the process
      console.log('Questionnaire answers:', answers)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      toast.success('Questionnaire completed! Redirecting to universities...')
      
      // Redirect to universities page
      router.push('/universities')
    } catch (error) {
      console.error('Error submitting questionnaire:', error)
      toast.error('Failed to submit questionnaire. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const currentQ = questions[currentQuestion]
  const hasAnswered = answers[currentQuestion] !== null && answers[currentQuestion] !== undefined

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
              <p className="text-lg font-medium mb-6">{currentQ.question}</p>
            </div>

            {/* Answer Options */}
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant={answers[currentQuestion] === true ? "default" : "outline"}
                size="lg"
                className={`h-16 text-lg transition-all ${
                  answers[currentQuestion] === true 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-primary/10'
                }`}
                onClick={() => handleAnswer(true)}
              >
                <CheckCircle className="h-5 w-5 mr-2" />
                True
              </Button>
              
              <Button
                variant={answers[currentQuestion] === false ? "default" : "outline"}
                size="lg"
                className={`h-16 text-lg transition-all ${
                  answers[currentQuestion] === false 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-primary/10'
                }`}
                onClick={() => handleAnswer(false)}
              >
                <XCircle className="h-5 w-5 mr-2" />
                False
              </Button>
            </div>

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
                  'Processing...'
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
              <CheckCircle className="h-3 w-3 mr-1" />
              <span>Personalized Results</span>
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