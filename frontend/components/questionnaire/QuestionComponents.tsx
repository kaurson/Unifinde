'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { CheckCircle, XCircle, Minus, Plus } from 'lucide-react'
import { Question } from '@/lib/api'

interface QuestionComponentProps {
  question: Question
  answer: any
  onAnswer: (answer: any) => void
}

// Boolean (True/False) Question Component
export function BooleanQuestion({ question, answer, onAnswer }: QuestionComponentProps) {
  // Extract options from question text
  // Format: "Would you rather A or B?" -> ["A", "B"]
  let options = ['Option 1', 'Option 2']
  
  if (question.question_text.includes('Would you rather')) {
    // Handle "Would you rather A or B?" format
    const match = question.question_text.match(/Would you rather (.+?) or (.+?)\??$/)
    if (match) {
      options = [match[1].trim(), match[2].trim()]
    }
  } else if (question.question_text.includes(' or ')) {
    // Handle other "A or B" formats
    const parts = question.question_text.split(' or ')
    if (parts.length >= 2) {
      // Clean up the parts
      const firstPart = parts[0].replace(/^.*\?/, '').trim()
      const secondPart = parts[1].replace(/\?.*$/, '').trim()
      if (firstPart && secondPart) {
        options = [firstPart, secondPart]
      }
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <Button
        variant={answer === options[0] ? "default" : "outline"}
        size="lg"
        className={`h-16 text-lg transition-all ${
          answer === options[0] 
            ? 'bg-primary text-primary-foreground' 
            : 'hover:bg-primary/10'
        }`}
        onClick={() => onAnswer(options[0])}
      >
        <CheckCircle className="h-5 w-5 mr-2" />
        {options[0]}
      </Button>
      
      <Button
        variant={answer === options[1] ? "default" : "outline"}
        size="lg"
        className={`h-16 text-lg transition-all ${
          answer === options[1] 
            ? 'bg-primary text-primary-foreground' 
            : 'hover:bg-primary/10'
        }`}
        onClick={() => onAnswer(options[1])}
      >
        <XCircle className="h-5 w-5 mr-2" />
        {options[1]}
      </Button>
    </div>
  )
}

// Text Question Component
export function TextQuestion({ question, answer, onAnswer }: QuestionComponentProps) {
  return (
    <div className="space-y-4">
      <Textarea
        placeholder="Type your answer here..."
        value={answer || ''}
        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onAnswer(e.target.value)}
        className="min-h-[120px] text-lg"
      />
    </div>
  )
}

// Number (Integer) Question Component
export function IntegerQuestion({ question, answer, onAnswer }: QuestionComponentProps) {
  return (
    <div className="space-y-4">
      <Input
        type="number"
        placeholder="Enter a number..."
        value={answer || ''}
        onChange={(e) => onAnswer(parseInt(e.target.value) || 0)}
        className="text-lg h-12"
      />
    </div>
  )
}

// Float Question Component
export function FloatQuestion({ question, answer, onAnswer }: QuestionComponentProps) {
  return (
    <div className="space-y-4">
      <Input
        type="number"
        step="0.1"
        placeholder="Enter a decimal number..."
        value={answer || ''}
        onChange={(e) => onAnswer(parseFloat(e.target.value) || 0)}
        className="text-lg h-12"
      />
    </div>
  )
}

// Scale (0-10) Question Component
export function ScaleQuestion({ question, answer, onAnswer }: QuestionComponentProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="text-3xl font-bold text-primary mb-2">
          {answer !== null && answer !== undefined ? answer : '?'}
        </div>
        <div className="text-sm text-muted-foreground">
          {answer !== null && answer !== undefined ? 
            (answer === 0 ? 'Not at all' : 
             answer <= 3 ? 'Very low' :
             answer <= 6 ? 'Moderate' :
             answer <= 8 ? 'High' : 'Very high') : 
            'Select a value'
          }
        </div>
      </div>
      
      <div className="px-4">
        <Slider
          value={[answer !== null && answer !== undefined ? answer : 5]}
          onValueChange={(value: number[]) => onAnswer(value[0])}
          max={10}
          min={0}
          step={1}
          className="w-full"
        />
      </div>
      
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>0</span>
        <span>5</span>
        <span>10</span>
      </div>
    </div>
  )
}

// Multiple Choice (3 options) Question Component
export function MultipleChoice3Question({ question, answer, onAnswer }: QuestionComponentProps) {
  // Extract options from question text
  let options = ['Option 1', 'Option 2', 'Option 3']
  
  if (question.question_text.includes(' / ')) {
    // Handle "A / B / C" format
    options = question.question_text.split(' / ').map(option => option.trim())
  } else if (question.question_text.includes('breakfast / lunch / midnight snack')) {
    // Handle the specific beans question
    options = ['breakfast', 'lunch', 'midnight snack']
  }

  return (
    <div className="space-y-3">
      {options.map((option, index) => (
        <Button
          key={index}
          variant={answer === option ? "default" : "outline"}
          size="lg"
          className={`w-full h-14 text-left justify-start transition-all ${
            answer === option 
              ? 'bg-primary text-primary-foreground' 
              : 'hover:bg-primary/10'
          }`}
          onClick={() => onAnswer(option)}
        >
          <div className="flex items-center">
            <div className="w-6 h-6 rounded-full border-2 mr-3 flex items-center justify-center">
              {answer === option && <div className="w-3 h-3 rounded-full bg-current" />}
            </div>
            {option}
          </div>
        </Button>
      ))}
    </div>
  )
}

// Multiple Choice (5 options) Question Component
export function MultipleChoice5Question({ question, answer, onAnswer }: QuestionComponentProps) {
  // Extract options from question text
  let options = ['Option 1', 'Option 2', 'Option 3', 'Option 4', 'Option 5']
  
  if (question.question_text.includes(' / ')) {
    // Handle "A / B / C / D / E" format
    options = question.question_text.split(' / ').map(option => option.trim())
  } else if (question.question_text.includes('Take turns chewing it / chew it together at the same time / take it yourself / throw it away (no one deserves it) / Give it to your friend')) {
    // Handle the specific gum question
    options = [
      'Take turns chewing it',
      'chew it together at the same time',
      'take it yourself',
      'throw it away (no one deserves it)',
      'Give it to your friend'
    ]
  }

  return (
    <div className="space-y-3">
      {options.map((option, index) => (
        <Button
          key={index}
          variant={answer === option ? "default" : "outline"}
          size="lg"
          className={`w-full h-14 text-left justify-start transition-all ${
            answer === option 
              ? 'bg-primary text-primary-foreground' 
              : 'hover:bg-primary/10'
          }`}
          onClick={() => onAnswer(option)}
        >
          <div className="flex items-center">
            <div className="w-6 h-6 rounded-full border-2 mr-3 flex items-center justify-center">
              {answer === option && <div className="w-3 h-3 rounded-full bg-current" />}
            </div>
            {option}
          </div>
        </Button>
      ))}
    </div>
  )
}

// Main Question Component that renders the appropriate component based on type
export function QuestionComponent({ question, answer, onAnswer }: QuestionComponentProps) {
  switch (question.question_type) {
    case 'boolean':
      return <BooleanQuestion question={question} answer={answer} onAnswer={onAnswer} />
    case 'text':
      return <TextQuestion question={question} answer={answer} onAnswer={onAnswer} />
    case 'integer':
      return <IntegerQuestion question={question} answer={answer} onAnswer={onAnswer} />
    case 'float':
      return <FloatQuestion question={question} answer={answer} onAnswer={onAnswer} />
    case 'scale_0_10':
      return <ScaleQuestion question={question} answer={answer} onAnswer={onAnswer} />
    case 'multiple_choice_3':
      return <MultipleChoice3Question question={question} answer={answer} onAnswer={onAnswer} />
    case 'multiple_choice_5':
      return <MultipleChoice5Question question={question} answer={answer} onAnswer={onAnswer} />
    default:
      return <TextQuestion question={question} answer={answer} onAnswer={onAnswer} />
  }
} 