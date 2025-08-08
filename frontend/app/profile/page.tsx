'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { 
  User, 
  Mail, 
  Phone, 
  Calendar,
  DollarSign,
  MapPin,
  GraduationCap,
  Brain,
  Edit,
  Save,
  X
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { api, User as UserType } from '@/lib/api'
import AppLayout from '@/components/layout/AppLayout'

export default function ProfilePage() {
  const router = useRouter()
  const [user, setUser] = useState<UserType | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState<Partial<UserType>>({})

  useEffect(() => {
    const loadProfile = async () => {
      if (!api.isAuthenticated()) {
        toast.error('Please login to view your profile')
        router.push('/login')
        return
      }

      try {
        const profileData = await api.getProfile()
        setUser(profileData)
        setEditData({
          name: profileData.name,
          age: profileData.age,
          phone: profileData.phone,
          income: profileData.income,
          min_acceptance_rate: profileData.min_acceptance_rate,
          max_tuition: profileData.max_tuition,
          preferred_university_type: profileData.preferred_university_type
        })
      } catch (error) {
        console.error('Error loading profile:', error)
        toast.error('Failed to load profile')
      } finally {
        setIsLoading(false)
      }
    }

    loadProfile()
  }, [router])

  const handleSave = async () => {
    try {
      const updatedProfile = await api.updateProfile(editData)
      setUser(updatedProfile)
      setIsEditing(false)
      toast.success('Profile updated successfully!')
    } catch (error) {
      console.error('Error updating profile:', error)
      toast.error('Failed to update profile')
    }
  }

  const handleCancel = () => {
    setEditData({
      name: user?.name,
      age: user?.age,
      phone: user?.phone,
      income: user?.income,
      min_acceptance_rate: user?.min_acceptance_rate,
      max_tuition: user?.max_tuition,
      preferred_university_type: user?.preferred_university_type
    })
    setIsEditing(false)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg">Loading profile...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Profile not found</h3>
          <p className="text-muted-foreground mb-4">
            Unable to load your profile information.
          </p>
          <Button asChild>
            <Link href="/">
              Back to Home
            </Link>
          </Button>
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
              <h1 className="text-3xl font-bold mb-2">Your Profile</h1>
              <p className="text-muted-foreground">
                Manage your personal information and preferences
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {!isEditing ? (
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Profile
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button size="sm" onClick={handleSave}>
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleCancel}>
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Profile Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <User className="h-5 w-5 mr-2" />
                  Basic Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="username">Username</Label>
                    <Input id="username" value={user.username} disabled />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" value={user.email} disabled />
                  </div>
                  <div>
                    <Label htmlFor="name">Full Name</Label>
                    {isEditing ? (
                      <Input 
                        id="name" 
                        value={editData.name || ''} 
                        onChange={(e) => setEditData({...editData, name: e.target.value})}
                      />
                    ) : (
                      <Input id="name" value={user.name} disabled />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="age">Age</Label>
                    {isEditing ? (
                      <Input 
                        id="age" 
                        type="number"
                        value={editData.age || ''} 
                        onChange={(e) => setEditData({...editData, age: parseInt(e.target.value) || undefined})}
                      />
                    ) : (
                      <Input id="age" value={user.age || 'Not specified'} disabled />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    {isEditing ? (
                      <Input 
                        id="phone" 
                        value={editData.phone || ''} 
                        onChange={(e) => setEditData({...editData, phone: e.target.value})}
                      />
                    ) : (
                      <Input id="phone" value={user.phone || 'Not specified'} disabled />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="income">Annual Income</Label>
                    {isEditing ? (
                      <Input 
                        id="income" 
                        type="number"
                        value={editData.income || ''} 
                        onChange={(e) => setEditData({...editData, income: parseFloat(e.target.value) || undefined})}
                      />
                    ) : (
                      <Input id="income" value={user.income ? `$${user.income.toLocaleString()}` : 'Not specified'} disabled />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Personality Summary */}
            {user.personality_summary && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Brain className="h-5 w-5 mr-2" />
                    Your Personality Summary
                  </CardTitle>
                  <CardDescription>
                    AI-generated summary based on your questionnaire responses
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
                    <p className="text-gray-700 leading-relaxed italic">
                      "{user.personality_summary}"
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Academic Preferences */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <GraduationCap className="h-5 w-5 mr-2" />
                  Academic Preferences
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="min_acceptance_rate">Minimum Acceptance Rate (%)</Label>
                    {isEditing ? (
                      <Input 
                        id="min_acceptance_rate" 
                        type="number"
                        value={editData.min_acceptance_rate || ''} 
                        onChange={(e) => setEditData({...editData, min_acceptance_rate: parseFloat(e.target.value) || undefined})}
                      />
                    ) : (
                      <Input id="min_acceptance_rate" value={user.min_acceptance_rate || 'Not specified'} disabled />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="max_tuition">Maximum Tuition ($)</Label>
                    {isEditing ? (
                      <Input 
                        id="max_tuition" 
                        type="number"
                        value={editData.max_tuition || ''} 
                        onChange={(e) => setEditData({...editData, max_tuition: parseFloat(e.target.value) || undefined})}
                      />
                    ) : (
                      <Input id="max_tuition" value={user.max_tuition ? `$${user.max_tuition.toLocaleString()}` : 'Not specified'} disabled />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="preferred_university_type">Preferred University Type</Label>
                    {isEditing ? (
                      <Input 
                        id="preferred_university_type" 
                        value={editData.preferred_university_type || ''} 
                        onChange={(e) => setEditData({...editData, preferred_university_type: e.target.value})}
                      />
                    ) : (
                      <Input id="preferred_university_type" value={user.preferred_university_type || 'Not specified'} disabled />
                    )}
                  </div>
                </div>

                {user.preferred_majors && user.preferred_majors.length > 0 && (
                  <div>
                    <Label>Preferred Majors</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {user.preferred_majors.map((major, index) => (
                        <span key={index} className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm">
                          {major}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {user.preferred_locations && user.preferred_locations.length > 0 && (
                  <div>
                    <Label>Preferred Locations</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {user.preferred_locations.map((location, index) => (
                        <span key={index} className="bg-secondary/10 text-secondary-foreground px-3 py-1 rounded-full text-sm">
                          {location}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" asChild>
                  <Link href="/questionnaire">
                    Retake Questionnaire
                  </Link>
                </Button>
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/universities">
                    View Matches
                  </Link>
                </Button>
                <Button variant="outline" className="w-full">
                  Export Profile
                </Button>
              </CardContent>
            </Card>

            {/* Profile Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Profile Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Member since</span>
                  <span className="font-medium">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Last updated</span>
                  <span className="font-medium">
                    {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : 'Never'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Profile complete</span>
                  <span className="font-medium">
                    {user.personality_profile ? '100%' : 'Incomplete'}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
} 