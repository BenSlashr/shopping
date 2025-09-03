import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  BarChart3,
  Home,
  Settings,
  Menu,
  X,
  Search,
  Bell,
  List,
  Target,
  TrendingUp,
  Users
} from 'lucide-react';
import { cn } from '../lib/utils';
import ProjectSelector from './ProjectSelector';

interface LayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Share of Voice', href: '/share-of-voice', icon: BarChart3 },
  { name: 'Matrice Positions', href: '/position-matrix', icon: Target },
  { name: 'Opportunités', href: '/opportunities', icon: TrendingUp },
  { name: 'Concurrents', href: '/competitors', icon: Users },
  { name: 'Suivi des Positions', href: '/keyword-positions', icon: List },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Mettre à jour la navigation active
  const updatedNavigation = navigation.map(item => ({
    ...item,
    current: item.href === location.pathname
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar mobile */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">Shopping Monitor</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="rounded-md p-2 text-gray-400 hover:text-gray-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          {/* Sélecteur de projet mobile */}
          <div className="px-4 py-4 border-b border-gray-200">
            <ProjectSelector />
          </div>
          
          <nav className="flex-1 px-4 py-6 space-y-1">
            {updatedNavigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  item.current
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon
                  className={cn(
                    "mr-3 h-5 w-5 flex-shrink-0",
                    item.current ? "text-primary-500" : "text-gray-400 group-hover:text-gray-500"
                  )}
                />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Sidebar desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col bg-white border-r border-gray-200">
        <div className="flex h-16 items-center px-6 border-b border-gray-200">
          <BarChart3 className="h-8 w-8 text-primary-600" />
          <span className="ml-2 text-xl font-bold text-gray-900">Shopping Monitor</span>
        </div>
        
        {/* Sélecteur de projet desktop */}
        <div className="px-4 py-4 border-b border-gray-200">
          <ProjectSelector />
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-1">
          {updatedNavigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                item.current
                  ? "bg-primary-100 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0",
                  item.current ? "text-primary-500" : "text-gray-400 group-hover:text-gray-500"
                )}
              />
              {item.name}
            </Link>
          ))}
        </nav>
      </div>

      {/* Contenu principal */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden rounded-md p-2 text-gray-400 hover:text-gray-500"
            >
              <Menu className="h-6 w-6" />
            </button>
            
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-semibold text-gray-900">
                {updatedNavigation.find(item => item.current)?.name || 'Dashboard'}
              </h1>
              
              {/* Sélecteur de projet dans le header sur mobile */}
              <div className="lg:hidden">
                <ProjectSelector />
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Barre de recherche */}
            <div className="hidden md:block relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Rechercher..."
                className="block w-80 pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-sm"
              />
            </div>

            {/* Notifications */}
            <button className="relative rounded-full p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
              <Bell className="h-6 w-6" />
              <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-danger-400 ring-2 ring-white" />
            </button>

            {/* Avatar utilisateur */}
            <div className="relative">
              <button className="flex items-center space-x-3 rounded-full bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2">
                <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center">
                  <span className="text-white font-medium text-sm">U</span>
                </div>
                <span className="hidden lg:block text-gray-700 font-medium">Utilisateur</span>
              </button>
            </div>
          </div>
        </header>

        {/* Contenu de la page */}
        <main className="p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
} 