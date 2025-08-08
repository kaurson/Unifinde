'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { 
  Menu,
  X,
  Home,
  BookOpen,
  BarChart3,
  Settings,
  User,
  LogOut,
  GraduationCap
} from 'lucide-react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { api } from '@/lib/api'

interface AppLayoutProps {
  children: React.ReactNode
  title?: string
  showHeader?: boolean
}

export default function AppLayout({ children, title, showHeader = true }: AppLayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [userName, setUserName] = useState<string>('')

  // Handle keyboard events for sidebar
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [sidebarOpen])

  // Get user name on component mount
  useEffect(() => {
    const getUserName = async () => {
      try {
        const profile = await api.getProfile()
        setUserName(profile.name || profile.username || 'User')
      } catch (error) {
        console.log('Could not fetch user name, using default')
        setUserName('User')
      }
    }
    getUserName()
  }, [])

  const navigationItems = [
    { href: '/', icon: Home, label: 'Home' },
    { href: '/universities', icon: GraduationCap, label: 'My Matches' },
    { href: '/browse', icon: BookOpen, label: 'Browse Universities' },
    { href: '/dashboard', icon: BarChart3, label: 'Dashboard' },
    { href: '/profile', icon: User, label: 'Profile' },
    { href: '/settings', icon: Settings, label: 'Settings' },
  ]

  const isActiveRoute = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      {showHeader && (
        <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {/* Sidebar Toggle for Mobile */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="lg:hidden"
                  aria-label="Toggle navigation menu"
                  aria-expanded={sidebarOpen}
                >
                  <Menu className="h-5 w-5" />
                </Button>
                
                {/* Sidebar Collapse Toggle for Desktop */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="hidden lg:flex"
                  aria-label="Toggle sidebar collapse"
                >
                  <Menu className="h-5 w-5" />
                </Button>
                
                {/* Logo */}
                <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
                  <GraduationCap className="h-6 w-6 text-primary" />
                  <span className="text-lg font-bold gradient-text">UniFinder</span>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                {title && (
                  <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
                )}
                {/* User Name and Waving Character */}
                <div className="flex items-center space-x-3 bg-gradient-to-r from-blue-50 to-purple-50 px-4 py-2 rounded-full border shadow-sm">
                  <span className="text-sm font-medium text-gray-700">
                    Hi, {userName}!
                  </span>
                  {/* Waving Character */}
                  <div className="relative w-10 h-10 flex items-center justify-center">
                    <img 
                      src="/3d-male-character-waving-free-png.png" 
                      alt="Waving character" 
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        // Hide the broken image and show emoji fallback
                        e.currentTarget.style.display = 'none';
                        const fallback = e.currentTarget.parentElement?.querySelector('.fallback-emoji');
                        if (fallback) {
                          fallback.classList.remove('hidden');
                        }
                      }}
                    />
                    {/* Fallback emoji */}
                    <span className="fallback-emoji hidden text-2xl">👋</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Main Layout Container */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Sidebar */}
        <div 
          className={`fixed inset-y-0 left-0 z-50 bg-white shadow-lg transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } ${
            sidebarCollapsed ? 'w-16' : 'w-64'
          }`}
          role="navigation"
          aria-label="Main navigation"
        >
          <div className="flex flex-col h-full">
            {/* Sidebar Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <Link href="/" className="flex items-center space-x-2">
                <GraduationCap className="h-6 w-6 text-primary flex-shrink-0" />
                {!sidebarCollapsed && <span className="text-lg font-bold">UniFinder</span>}
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden"
                aria-label="Close navigation menu"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Navigation Menu */}
            <nav className="flex-1 p-4 space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon
                const isActive = isActiveRoute(item.href)
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive 
                        ? 'text-primary bg-primary/10' 
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </Link>
                )
              })}
            </nav>

            {/* Sidebar Footer */}
            <div className="p-4 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => api.logout().then(() => router.push('/login'))}
                className="w-full justify-start text-gray-700 hover:text-gray-900"
                title="Logout"
              >
                <LogOut className="h-5 w-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="ml-3">Logout</span>}
              </Button>
            </div>
          </div>
        </div>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </div>
  )
} 