'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { QuestionComponent } from '@/components/questionnaire/QuestionComponents'
import { ArrowLeft, ArrowRight, CheckCircle, Brain, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, Question } from '@/lib/api'

export default function QuestionnairePage() {
  const router = useRouter()
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Fetch questions from database
  useEffect(() => {
    const checkAuthAndLoadQuestions = async () => {
      setIsLoading(true)
      
      try {
        // Check authentication using the new cookie-based system
        const isAuth = await api.isAuthenticated()
        if (!isAuth) {
          toast.error('Please login to access the questionnaire')
          router.push('/login')
          return
        }
        
        // Load questions
        const questionsData = await api.getQuestions()
        setQuestions(questionsData.sort((a, b) => a.order_index - b.order_index))
      } catch (error) {
        console.error('Error loading questions:', error)
        toast.error('Failed to load questions')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuthAndLoadQuestions()
  }, [router])

  const handleAnswer = (answer: any) => {
    const questionId = questions[currentQuestion]?.id
    if (questionId) {
      setAnswers(prev => ({
        ...prev,
        [questionId]: answer
      }))
    }
  }

  const handleNext = () => {
    const questionId = questions[currentQuestion]?.id
    if (questionId && answers[questionId]) {
      if (currentQuestion < questions.length - 1) {
        setCurrentQuestion(prev => prev + 1)
      }
    } else {
      toast.error('Please answer the current question before proceeding')
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1)
    }
  }

  const handleSubmit = async () => {
    const questionId = questions[currentQuestion]?.id
    if (questionId && !answers[questionId]) {
      toast.error('Please answer the current question before submitting')
      return
    }

    setIsSubmitting(true)
    
    try {
      // Check authentication before submitting
      const isAuth = await api.isAuthenticated()
      if (!isAuth) {
        toast.error('Please login to submit the questionnaire')
        router.push('/login')
        return
      }

      console.log('Submitting questionnaire with answers:', answers)

      // Convert answers to the format expected by the API
      const submissionAnswers = Object.entries(answers).map(([question_id, answer]) => ({
        question_id,
        answer_text: typeof answer === 'string' ? answer : JSON.stringify(answer),
        answer_data: { value: answer }
      }))

      const submissionData = {
        answers: submissionAnswers,
        preferred_majors: ['Computer Science', 'Engineering'], // Default values
        preferred_locations: ['United States', 'Canada'] // Default values
      }

      console.log('Submitting data:', submissionData)

      // Get user profile first for the redirect
      const userProfile = await api.getProfile()
      console.log('User profile:', userProfile)
      
      // Immediately redirect to loading page
      toast.success('Questionnaire completed! Processing your results...')
      router.push(`/loading?userId=${userProfile.id}&redirectTo=/summary`)
      
      // Submit questionnaire in the background (don't await)
      api.submitQuestionnaire(submissionData)
        .then(result => {
          console.log('Questionnaire submission result:', result)
        })
        .catch(error => {
          console.error('Error submitting questionnaire:', error)
          // Note: We don't show error toast here since user is already on loading page
        })
        
    } catch (error) {
      console.error('Error in handleSubmit:', error)
      if (error instanceof Error) {
        toast.error(`Failed to submit questionnaire: ${error.message}`)
      } else {
        toast.error('Failed to submit questionnaire. Please try again.')
      }
      setIsSubmitting(false)
    }
  }

  const handleSkipQuestionnaire = async () => {
    setIsSubmitting(true)
    
    try {
      // Generate random answers for all questions and populate local state
      const randomAnswers: Record<string, any> = {}
      
      questions.forEach(question => {
        let randomAnswer: any = ''
        
        switch (question.question_type) {
          case 'boolean':
            randomAnswer = Math.random() > 0.5 ? true : false
            break
          case 'integer':
            randomAnswer = Math.floor(Math.random() * 10) + 1
            break
          case 'float':
            randomAnswer = parseFloat((Math.random() * 10 + 1).toFixed(2))
            break
          case 'scale_0_10':
            randomAnswer = Math.floor(Math.random() * 11)
            break
          case 'multiple_choice_3':
            const options3 = ['Strongly Agree', 'Neutral', 'Strongly Disagree']
            randomAnswer = options3[Math.floor(Math.random() * 3)]
            break
          case 'multiple_choice_5':
            const options5 = ['Very Important', 'Important', 'Neutral', 'Not Important', 'Not at All Important']
            randomAnswer = options5[Math.floor(Math.random() * 5)]
            break
          case 'text':
            const textOptions = [
              'I enjoy learning new things and exploring different subjects. I prefer hands-on learning experiences and working in collaborative environments.',
              'I am very organized and detail-oriented. I like to plan ahead and prefer structured learning environments with clear expectations.',
              'I enjoy creative problem-solving and thinking outside the box. I prefer flexible learning environments that allow for innovation.',
              'I am a natural leader and enjoy taking initiative. I prefer group projects and opportunities to guide others.',
              'I am analytical and enjoy research-based learning. I prefer quiet environments where I can focus deeply on complex topics.',
              'I am very social and enjoy working with others. I prefer interactive learning experiences and group discussions.',
              'I am independent and prefer self-directed learning. I like to work at my own pace and explore topics that interest me.',
              'I am practical and prefer learning that has real-world applications. I enjoy internships and hands-on experiences.',
              'I am curious and enjoy exploring diverse subjects. I prefer interdisciplinary approaches and connecting different fields.',
              'I am goal-oriented and prefer learning that helps me achieve my career objectives. I enjoy structured programs with clear outcomes.',
              'I am adaptable and enjoy learning in different environments. I prefer programs that offer flexibility and variety.',
              'I am passionate about making a difference. I prefer learning that helps me contribute to society and solve real problems.'
            ]
            randomAnswer = textOptions[Math.floor(Math.random() * textOptions.length)]
            break
          default:
            randomAnswer = 'I am interested in learning and growing academically. I prefer environments that challenge me and help me develop my skills.'
        }
        
        randomAnswers[question.id] = randomAnswer
      })
      
      // Update the answers state with random values
      setAnswers(randomAnswers)
      
      // Move to the last question to show completion
      setCurrentQuestion(questions.length - 1)
      
      toast.success('Random answers generated! You can review and submit them.')
    } catch (error) {
      console.error('Error generating random answers:', error)
      toast.error('Failed to generate random answers. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Show loading while checking authentication
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
            <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
              <Brain className="h-8 w-8 text-primary mr-2" />
              <span className="text-2xl font-bold gradient-text">UniFinder</span>
            </Link>
          </div>
          <h1 className="text-3xl font-bold mb-2">Help Us Understand You</h1>
          <p className="text-muted-foreground">
            Answer a few questions to help us find your perfect university match
          </p>
          
          {/* Generate Random Answers Button for Testing */}
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
                  Generating...
                </>
              ) : (
                '🎲 Generate Random Answers (Testing)'
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
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </Button>

              <Button
                onClick={currentQuestion === questions.length - 1 ? handleSubmit : handleNext}
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