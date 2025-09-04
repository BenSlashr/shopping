import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { apiClient } from '../lib/api';

export interface Project {
  id: string;
  name: string;
  description: string;
  reference_site: string;
  reference_domain: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface ProjectContextType {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  setCurrentProject: (project: Project) => void;
  refreshProjects: () => Promise<void>;
  createProject: (projectData: Partial<Project>) => Promise<Project>;
  updateProject: (id: string, projectData: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

interface ProjectProviderProps {
  children: ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProjectState] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Récupérer les projets depuis l'API
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Récupérer les vrais projets depuis l'API
      console.log('Calling API:', apiClient.defaults.baseURL + '/projects/');
      const response = await apiClient.get('/projects/');
      const realProjects = response.data.projects || [];
      
      setProjects(realProjects);
      
      // Si aucun projet courant ou s'il n'existe plus, sélectionner le premier
      const savedProjectId = localStorage.getItem('selectedProjectId');
      if (savedProjectId) {
        const savedProject = realProjects.find((p: Project) => p.id === savedProjectId);
        if (savedProject) {
          setCurrentProjectState(savedProject);
          return;
        }
      }
      
      // Sélectionner le premier projet disponible
      if (realProjects.length > 0) {
        setCurrentProjectState(realProjects[0]);
        localStorage.setItem('selectedProjectId', realProjects[0].id);
      }
      
    } catch (err) {
      console.error('Erreur lors de la récupération des projets:', err);
      setError('Erreur lors du chargement des projets');
      
      // Fallback vers les données simulées si l'API échoue
      const mockProjects: Project[] = [
        {
          id: 'e80d2fba-dcb7-418b-8868-404bf4d5d5c4', // ID réel de la base de données
          name: 'E-commerce Principal',
          description: 'Monitoring du site e-commerce principal avec focus sur l\'électronique',
          reference_site: 'https://monsite-ecommerce.fr',
          reference_domain: 'monsite-ecommerce.fr',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z'
        }
      ];
      
      setProjects(mockProjects);
      if (mockProjects.length > 0) {
        setCurrentProjectState(mockProjects[0]);
        localStorage.setItem('selectedProjectId', mockProjects[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  const setCurrentProject = (project: Project) => {
    setCurrentProjectState(project);
    localStorage.setItem('selectedProjectId', project.id);
  };

  const refreshProjects = async () => {
    await fetchProjects();
  };

  // Créer un nouveau projet
  const createProject = async (projectData: Partial<Project>): Promise<Project> => {
    try {
      setError(null);
      
      // Extraire le domaine de l'URL
      const extractDomain = (url: string): string => {
        try {
          const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
          return urlObj.hostname.replace('www.', '');
        } catch {
          return url.replace('www.', '').replace(/^https?:\/\//, '');
        }
      };
      
      const newProjectData = {
        name: projectData.name || '',
        description: projectData.description || '',
        reference_site: projectData.reference_site || '',
        reference_domain: extractDomain(projectData.reference_site || ''),
        is_active: true
      };
      
      // Appeler l'API pour créer le projet
      const response = await apiClient.post('/projects/', newProjectData);
      const newProject = response.data;
      
      // Mettre à jour la liste des projets
      const updatedProjects = [...projects, newProject];
      setProjects(updatedProjects);
      
      // Sélectionner le nouveau projet
      setCurrentProjectState(newProject);
      localStorage.setItem('selectedProjectId', newProject.id);
      
      return newProject;
    } catch (err: any) {
      console.error('Erreur lors de la création du projet:', err);
      const errorMessage = err.response?.data?.detail || 'Erreur lors de la création du projet';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const updateProject = async (id: string, projectData: Partial<Project>): Promise<Project> => {
    try {
      const updatedProject = { 
        ...projects.find(p => p.id === id)!, 
        ...projectData,
        updated_at: new Date().toISOString()
      };

      setProjects(prev => prev.map(p => p.id === id ? updatedProject : p));
      
      if (currentProject?.id === id) {
        setCurrentProjectState(updatedProject);
      }

      return updatedProject;
    } catch (err) {
      throw new Error('Erreur lors de la mise à jour du projet');
    }
  };

  const deleteProject = async (id: string): Promise<void> => {
    try {
      setProjects(prev => prev.filter(p => p.id !== id));
      
      if (currentProject?.id === id) {
        const remainingProjects = projects.filter(p => p.id !== id);
        if (remainingProjects.length > 0) {
          setCurrentProject(remainingProjects[0]);
        } else {
          setCurrentProjectState(null);
          localStorage.removeItem('selectedProjectId');
        }
      }
    } catch (err) {
      throw new Error('Erreur lors de la suppression du projet');
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const value: ProjectContextType = {
    projects,
    currentProject,
    loading,
    error,
    setCurrentProject,
    refreshProjects,
    createProject,
    updateProject,
    deleteProject
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}; 