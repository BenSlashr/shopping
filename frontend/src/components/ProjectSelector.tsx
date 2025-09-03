import React, { useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { ChevronDown, Plus, Building, Globe, Check } from 'lucide-react';
import { cn } from '../lib/utils';

export default function ProjectSelector() {
  const { projects, currentProject, setCurrentProject, loading, createProject } = useProject();
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectSite, setNewProjectSite] = useState('');

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || !newProjectSite.trim()) return;
    
    setIsCreating(true);
    try {
      await createProject({
        name: newProjectName.trim(),
        reference_site: newProjectSite.trim(),
        description: `Monitoring SEO pour ${newProjectName.trim()}`
      });
      
      setNewProjectName('');
      setNewProjectSite('');
      setIsOpen(false);
    } catch (error) {
      console.error('Erreur création projet:', error);
    } finally {
      setIsCreating(false);
    }
  };

  if (loading || !currentProject) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-md animate-pulse">
        <Building className="h-4 w-4 text-gray-400" />
        <div className="h-4 w-32 bg-gray-300 rounded"></div>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors w-full max-w-xs",
          "bg-white border border-gray-200 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2",
          isOpen && "ring-2 ring-primary-500 ring-offset-2"
        )}
      >
        <Building className="h-4 w-4 text-gray-500 flex-shrink-0" />
        <div className="flex flex-col items-start min-w-0 flex-1">
          <span className="text-gray-900 truncate w-full text-left">
            {currentProject.name}
          </span>
          <span className="text-xs text-gray-500 truncate w-full text-left">
            {currentProject.reference_domain}
          </span>
        </div>
        <ChevronDown className={cn(
          "h-4 w-4 text-gray-400 transition-transform flex-shrink-0",
          isOpen && "transform rotate-180"
        )} />
      </button>

      {isOpen && (
        <>
          {/* Overlay pour fermer le dropdown */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown menu - Positionné à gauche avec largeur fixe */}
          <div className="absolute left-0 mt-2 w-96 bg-white rounded-md shadow-lg border border-gray-200 z-20">
            <div className="py-2">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-100">
                Projets disponibles
              </div>
              
              <div className="max-h-60 overflow-y-auto">
                {projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      setCurrentProject(project);
                      setIsOpen(false);
                    }}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-3 text-left hover:bg-gray-50 transition-colors",
                      currentProject.id === project.id && "bg-primary-50"
                    )}
                  >
                    <div className="flex items-center space-x-3 min-w-0 flex-1">
                      <div className={cn(
                        "flex-shrink-0 w-2 h-2 rounded-full",
                        project.is_active ? "bg-green-400" : "bg-gray-300"
                      )} />
                      
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {project.name}
                          </p>
                          {currentProject.id === project.id && (
                            <Check className="h-4 w-4 text-primary-600" />
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-1 mt-1">
                          <Globe className="h-3 w-3 text-gray-400" />
                          <p className="text-xs text-gray-500 truncate">
                            {project.reference_domain}
                          </p>
                        </div>
                        
                        {project.description && (
                          <p className="text-xs text-gray-400 truncate mt-1">
                            {project.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Formulaire de création de projet */}
              <div className="border-t border-gray-100 mt-2 p-3">
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Nom du projet
                    </label>
                    <input
                      type="text"
                      value={newProjectName}
                      onChange={(e) => setNewProjectName(e.target.value)}
                      placeholder="Ex: Mon E-commerce"
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Site web
                    </label>
                    <input
                      type="url"
                      value={newProjectSite}
                      onChange={(e) => setNewProjectSite(e.target.value)}
                      placeholder="https://monsite.com"
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    />
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCreateProject}
                      disabled={!newProjectName.trim() || !newProjectSite.trim() || isCreating}
                      className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 text-xs font-medium text-white bg-primary-600 rounded hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {isCreating ? (
                        <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Plus className="h-3 w-3" />
                      )}
                      <span>{isCreating ? 'Création...' : 'Créer'}</span>
                    </button>
                    
                    <button
                      onClick={() => {
                        setNewProjectName('');
                        setNewProjectSite('');
                      }}
                      className="px-3 py-2 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
} 