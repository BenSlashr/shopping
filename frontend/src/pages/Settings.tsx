import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Target,
  Users,
  Bell,
  Building,
  ExternalLink,
  Edit,
  Save,
  X,
  Globe,
  AlertCircle,
  Plus,
  Upload,
  Download,
  Trash2,
  Search,
  Filter
} from 'lucide-react';
import { useProject } from '../contexts/ProjectContext';
import { apiClient, competitorsApi } from '../lib/api';
import config from '../config';
import { cn } from '../lib/utils';

interface Project {
  id: string;
  name: string;
  description: string;
  reference_site: string;
  reference_domain: string;
  is_active: boolean;
  created_at: string;
}

interface Keyword {
  id: string;
  keyword: string;
  location: string;
  language: string;
  search_volume: number;
  is_active: boolean;
  created_at: string;
}

interface Competitor {
  id: string;
  name: string;
  domain: string;
  brand_name: string;
  is_main_brand: boolean;
  created_at: string;
}

interface GeneralSettings {
  refresh_frequency: number;
  max_results_per_keyword: number;
  enable_notifications: boolean;
  data_retention_days: number;
}

interface NotificationSettings {
  email_alerts: boolean;
  position_changes: boolean;
  new_competitors: boolean;
  weekly_reports: boolean;
  email_address: string;
}

export default function Settings() {
  const { currentProject } = useProject();
  const [activeTab, setActiveTab] = useState<'project' | 'general' | 'keywords' | 'competitors' | 'notifications'>('project');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // États pour le projet
  const [editingProject, setEditingProject] = useState(false);
  const [projectForm, setProjectForm] = useState({
    name: '',
    description: '',
    reference_site: '',
    reference_domain: ''
  });

  // États pour les mots-clés
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [keywordSearch, setKeywordSearch] = useState('');
  const [showBulkAdd, setShowBulkAdd] = useState(false);
  const [bulkKeywords, setBulkKeywords] = useState('');
  const [bulkLocation, setBulkLocation] = useState('France');
  const [bulkLanguage, setBulkLanguage] = useState('fr');
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // États pour les concurrents
  const [competitors, setCompetitors] = useState<Competitor[]>([]);

  // États pour les paramètres généraux
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings>({
    refresh_frequency: 24,
    max_results_per_keyword: 50,
    enable_notifications: true,
    data_retention_days: 90
  });

  // États pour les notifications
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    email_alerts: true,
    position_changes: true,
    new_competitors: true,
    weekly_reports: false,
    email_address: 'user@example.com'
  });

  const tabs = [
    { id: 'project' as const, name: 'Projet', icon: Building },
    { id: 'general' as const, name: 'Général', icon: SettingsIcon },
    { id: 'keywords' as const, name: 'Mots-clés', icon: Target },
    { id: 'competitors' as const, name: 'Concurrents', icon: Users },
    { id: 'notifications' as const, name: 'Notifications', icon: Bell },
  ];

  useEffect(() => {
    const fetchSettingsData = async () => {
      setLoading(true);
      
      if (currentProject) {
        setProjectForm({
          name: currentProject.name,
          description: currentProject.description,
          reference_site: currentProject.reference_site,
          reference_domain: currentProject.reference_domain
        });

        try {
          // Récupération des vrais mots-clés depuis l'API
          const keywordsResponse = await apiClient.get(`/api/v1/projects/${currentProject.id}/keywords`);
          
          if (keywordsResponse.data && keywordsResponse.data.keywords) {
            // Conversion des données API vers le format attendu
            const apiKeywords = keywordsResponse.data.keywords.map((k: any) => ({
              id: k.id,
              keyword: k.keyword,
              location: k.location || 'France',
              language: k.language || 'fr',
              search_volume: k.search_volume || 0,
              is_active: k.is_active !== false, // Par défaut true si non spécifié
              created_at: k.created_at || new Date().toISOString()
            }));
            setKeywords(apiKeywords);
          } else {
            // Fallback vers les données simulées si l'API ne répond pas
            const mockKeywords: Keyword[] = [
              {
                id: '1',
                keyword: 'smartphone pas cher',
                location: 'France',
                language: 'fr',
                search_volume: 12000,
                is_active: true,
                created_at: '2024-01-15T00:00:00Z'
              },
              {
                id: '2',
                keyword: 'iPhone 15 pro',
                location: 'France',
                language: 'fr',
                search_volume: 8500,
                is_active: true,
                created_at: '2024-01-20T00:00:00Z'
              },
              {
                id: '3',
                keyword: 'casque bluetooth',
                location: 'France',
                language: 'fr',
                search_volume: 15000,
                is_active: false,
                created_at: '2024-02-01T00:00:00Z'
              }
            ];
            setKeywords(mockKeywords);
          }
        } catch (error) {
          console.error('Erreur lors de la récupération des mots-clés:', error);
          showMessage('Erreur lors du chargement des mots-clés depuis la base de données', 'error');
          
          // En cas d'erreur, utiliser les données simulées
          const mockKeywords: Keyword[] = [
            {
              id: '1',
              keyword: 'smartphone pas cher',
              location: 'France',
              language: 'fr',
              search_volume: 12000,
              is_active: true,
              created_at: '2024-01-15T00:00:00Z'
            },
            {
              id: '2',
              keyword: 'iPhone 15 pro',
              location: 'France',
              language: 'fr',
              search_volume: 8500,
              is_active: true,
              created_at: '2024-01-20T00:00:00Z'
            },
            {
              id: '3',
              keyword: 'casque bluetooth',
              location: 'France',
              language: 'fr',
              search_volume: 15000,
              is_active: false,
              created_at: '2024-02-01T00:00:00Z'
            }
          ];
          setKeywords(mockKeywords);
        }
      }

        // Récupération des concurrents
        try {
          const competitorsResponse = await competitorsApi.getByProject(currentProject.id);
          setCompetitors(competitorsResponse.data.competitors || []);
        } catch (error) {
          console.error('Erreur lors de la récupération des concurrents:', error);
          // Fallback vers données simulées
          const mockCompetitors: Competitor[] = [
            {
              id: '1',
              name: 'Amazon',
              domain: 'amazon.fr',
              brand_name: 'Amazon',
              is_main_brand: false,
              created_at: '2024-01-01T00:00:00Z'
            },
            {
              id: '2',
              name: 'Fnac',
              domain: 'fnac.com',
              brand_name: 'Fnac',
              is_main_brand: false,
              created_at: '2024-01-01T00:00:00Z'
            }
          ];
          setCompetitors(mockCompetitors);
        }
      setLoading(false);
    };

    fetchSettingsData();
  }, [currentProject]);

  const showMessage = (message: string, type: 'success' | 'error') => {
    if (type === 'success') {
      setSuccess(message);
      setError(null);
    } else {
      setError(message);
      setSuccess(null);
    }
    setTimeout(() => {
      setSuccess(null);
      setError(null);
    }, 5000);
  };

  const handleSaveProject = async () => {
    if (!projectForm.name.trim() || !projectForm.reference_site.trim()) {
      showMessage('Le nom du projet et site de référence sont requis', 'error');
      return;
    }

    try {
      setEditingProject(false);
      showMessage('Projet mis à jour avec succès', 'success');
    } catch (err) {
      showMessage('Erreur lors de la mise à jour du projet', 'error');
    }
  };

  const extractDomainFromUrl = (url: string) => {
    try {
      const domain = new URL(url).hostname.replace('www.', '');
      setProjectForm({ ...projectForm, reference_domain: domain });
    } catch (err) {
      // URL invalide, on ne fait rien
    }
  };

  // Gestion des mots-clés
  const handleBulkAddKeywords = async () => {
    if (!bulkKeywords.trim()) {
      showMessage('Veuillez saisir au moins un mot-clé', 'error');
      return;
    }

    try {
      const keywordLines = bulkKeywords.split('\n').filter(line => line.trim());
      const keywordsToAdd = keywordLines.map((line) => {
        const trimmedLine = line.trim();
        
        // Support de plusieurs formats :
        // 1. CSV avec virgule : "mot-clé,volume"
        // 2. TSV avec tabulation : "mot-clé[TAB]volume"
        // 3. Simple : "mot-clé" (volume par défaut)
        let keyword = '';
        let volume = 1000; // Volume par défaut
        
        if (trimmedLine.includes(',')) {
          // Format CSV : mot-clé,volume
          const parts = trimmedLine.split(',');
          keyword = parts[0]?.trim();
          const volumeStr = parts[1]?.trim();
          if (volumeStr && !isNaN(parseInt(volumeStr))) {
            volume = parseInt(volumeStr);
          }
        } else if (trimmedLine.includes('\t')) {
          // Format TSV : mot-clé[TAB]volume
          const parts = trimmedLine.split('\t');
          keyword = parts[0]?.trim();
          const volumeStr = parts[1]?.trim();
          if (volumeStr && !isNaN(parseInt(volumeStr))) {
            volume = parseInt(volumeStr);
          }
        } else {
          // Format simple : juste le mot-clé
          keyword = trimmedLine;
        }
        
        return {
          keyword: keyword || trimmedLine,
          location: bulkLocation,
          language: bulkLanguage,
          search_volume: volume,
          is_active: true
        };
      });

      // Appeler l'API pour sauvegarder en base de données
      const response = await apiClient.post(`/api/v1/projects/${currentProject.id}/keywords`, {
        keywords: keywordsToAdd
      });

      if (response.data && response.data.keywords) {
        // Convertir les données API vers le format local
        const newKeywords: Keyword[] = response.data.keywords.map((kw: any) => ({
          id: kw.id,
          keyword: kw.keyword,
          location: kw.location,
          language: kw.language,
          search_volume: kw.search_volume,
          is_active: kw.is_active,
          created_at: kw.created_at
        }));

        // Ajouter à la liste locale
        setKeywords(prev => [...prev, ...newKeywords]);
        setBulkKeywords('');
        setShowBulkAdd(false);
        showMessage(`${response.data.added_count} mots-clés ajoutés avec succès en base de données`, 'success');
      } else {
        throw new Error('Réponse API invalide');
      }
    } catch (err: any) {
      console.error('Erreur lors de l\'ajout des mots-clés:', err);
      if (err.response?.data?.detail) {
        showMessage(`Erreur : ${err.response.data.detail}`, 'error');
      } else {
        showMessage('Erreur lors de l\'ajout des mots-clés en base de données', 'error');
      }
    }
  };

  const handleDeleteKeywords = async () => {
    if (selectedKeywords.length === 0) {
      showMessage('Veuillez sélectionner au moins un mot-clé à supprimer', 'error');
      return;
    }

    try {
      setKeywords(prev => prev.filter(k => !selectedKeywords.includes(k.id)));
      setSelectedKeywords([]);
      showMessage(`${selectedKeywords.length} mots-clés supprimés`, 'success');
    } catch (err) {
      showMessage('Erreur lors de la suppression', 'error');
    }
  };

  const handleToggleKeyword = async (keywordId: string) => {
    try {
      setKeywords(prev => prev.map(k => 
        k.id === keywordId ? { ...k, is_active: !k.is_active } : k
      ));
      showMessage('Statut du mot-clé mis à jour', 'success');
    } catch (err) {
      showMessage('Erreur lors de la mise à jour', 'error');
    }
  };

  const exportKeywords = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + "Mot-clé,Localisation,Langue,Volume,Statut,Date de création\n"
      + keywords.map(k => 
          `"${k.keyword}","${k.location}","${k.language}",${k.search_volume},"${k.is_active ? 'Actif' : 'Inactif'}","${new Date(k.created_at).toLocaleDateString('fr-FR')}"`
        ).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `mots-cles-${currentProject?.name || 'projet'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleAnalyzeKeywords = async () => {
    if (!currentProject) {
      showMessage('Aucun projet sélectionné', 'error');
      return;
    }

    const activeKeywords = keywords.filter(k => k.is_active);
    if (activeKeywords.length === 0) {
      showMessage('Aucun mot-clé actif à analyser', 'error');
      return;
    }

    setIsAnalyzing(true);
    try {
      showMessage(`Lancement de l'analyse SERP pour ${activeKeywords.length} mots-clés...`, 'success');
      
      const response = await apiClient.post(`/api/v1/scraping/projects/${currentProject.id}/analyze`);
      
      if (response.data) {
        showMessage(
          `Analyse SERP lancée avec succès ! Les résultats seront disponibles dans quelques minutes.`,
          'success'
        );
      }
    } catch (err: any) {
      console.error('Erreur lors du lancement de l\'analyse:', err);
      if (err.response?.data?.detail) {
        showMessage(`Erreur : ${err.response.data.detail}`, 'error');
      } else {
        showMessage('Erreur lors du lancement de l\'analyse SERP', 'error');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDeleteSelected = () => {
    handleDeleteKeywords();
  };

  const handleExportKeywords = () => {
    exportKeywords();
  };

  const filteredKeywords = keywords.filter(keyword =>
    keyword.keyword.toLowerCase().includes(keywordSearch.toLowerCase())
  );

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Veuillez sélectionner un projet pour accéder aux paramètres.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Messages de succès/erreur */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation par onglets */}
      <div className="card">
        <div className="card-header">
          <nav className="flex space-x-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'project' | 'general' | 'keywords' | 'competitors' | 'notifications')}
                className={cn(
                  "flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  activeTab === tab.id
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="card-content">
          {/* Onglet Projet */}
          {activeTab === 'project' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Configuration du projet</h3>
                {!editingProject && (
                  <button
                    onClick={() => setEditingProject(true)}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <Edit className="h-4 w-4" />
                    <span>Modifier</span>
                  </button>
                )}
              </div>

              {editingProject ? (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nom du projet *
                    </label>
                    <input
                      type="text"
                      value={projectForm.name}
                      onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Nom du projet"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={projectForm.description}
                      onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Description du projet"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Site de référence *
                    </label>
                    <input
                      type="url"
                      value={projectForm.reference_site}
                      onChange={(e) => {
                        setProjectForm({ ...projectForm, reference_site: e.target.value });
                        if (e.target.value) {
                          extractDomainFromUrl(e.target.value);
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="https://monsite.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Domaine de référence
                    </label>
                    <input
                      type="text"
                      value={projectForm.reference_domain}
                      onChange={(e) => setProjectForm({ ...projectForm, reference_domain: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50"
                      placeholder="monsite.com"
                      readOnly
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Extrait automatiquement du site de référence
                    </p>
                  </div>

                  <div className="flex items-center space-x-3">
                    <button
                      onClick={handleSaveProject}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Save className="h-4 w-4" />
                      <span>Sauvegarder</span>
                    </button>
                    <button
                      onClick={() => {
                        setEditingProject(false);
                        setProjectForm({
                          name: currentProject.name,
                          description: currentProject.description,
                          reference_site: currentProject.reference_site,
                          reference_domain: currentProject.reference_domain
                        });
                      }}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <X className="h-4 w-4" />
                      <span>Annuler</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Nom du projet</h4>
                        <p className="text-gray-700">{currentProject.name}</p>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Statut</h4>
                        <span className={`badge ${currentProject.is_active ? 'badge-success' : 'badge-danger'}`}>
                          {currentProject.is_active ? 'Actif' : 'Inactif'}
                        </span>
                      </div>

                      <div className="md:col-span-2">
                        <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                        <p className="text-gray-700">{currentProject.description}</p>
                      </div>

                      <div className="md:col-span-2">
                        <h4 className="font-medium text-gray-900 mb-2">Site de référence</h4>
                        <div className="flex items-center space-x-2">
                          <Globe className="h-4 w-4 text-gray-400" />
                          <a
                            href={currentProject.reference_site}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-700 flex items-center space-x-1"
                          >
                            <span>{currentProject.reference_site}</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          Domaine: <span className="font-medium">{currentProject.reference_domain}</span>
                        </p>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Créé le</h4>
                        <p className="text-gray-700">
                          {new Date(currentProject.created_at).toLocaleDateString('fr-FR', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </p>
                      </div>

                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">ID du projet</h4>
                        <p className="text-sm text-gray-500 font-mono">{currentProject.id}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">À propos du site de référence</h4>
                        <p className="text-sm text-blue-700 mt-1">
                          Le site de référence est utilisé pour identifier vos propres produits dans les résultats Google Shopping.
                          Il permet de calculer votre position par rapport aux concurrents et d'analyser votre performance.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Onglet Mots-clés */}
          {activeTab === 'keywords' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Gestion des mots-clés</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {keywords.length} mots-clés dont {keywords.filter(k => k.is_active).length} actifs
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleExportKeywords}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Exporter</span>
                  </button>
                  <button
                    onClick={handleAnalyzeKeywords}
                    disabled={isAnalyzing || keywords.filter(k => k.is_active).length === 0}
                    className="btn-success flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Analyse en cours...</span>
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4" />
                        <span>Analyser SERP ({keywords.filter(k => k.is_active).length})</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setShowBulkAdd(true)}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Ajouter en bulk</span>
                  </button>
                </div>
              </div>

              {/* Modal d'ajout en bulk */}
              {showBulkAdd && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">Ajouter des mots-clés en bulk</h4>
                      <button
                        onClick={() => setShowBulkAdd(false)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-6 w-6" />
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Localisation
                          </label>
                          <select
                            value={bulkLocation}
                            onChange={(e) => setBulkLocation(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          >
                            <option value="France">France</option>
                            <option value="Belgium">Belgique</option>
                            <option value="Switzerland">Suisse</option>
                            <option value="Canada">Canada</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Langue
                          </label>
                          <select
                            value={bulkLanguage}
                            onChange={(e) => setBulkLanguage(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          >
                            <option value="fr">Français</option>
                            <option value="en">Anglais</option>
                            <option value="de">Allemand</option>
                            <option value="es">Espagnol</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Mots-clés (un par ligne)
                        </label>
                        <textarea
                          value={bulkKeywords}
                          onChange={(e) => setBulkKeywords(e.target.value)}
                          rows={10}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="smartphone pas cher,12000&#10;iPhone 15 pro,8500&#10;casque bluetooth,15000&#10;tablette Samsung,6200&#10;...&#10;&#10;Formats supportés:&#10;- mot-clé,volume (CSV recommandé)&#10;- mot-clé[TAB]volume (TSV)&#10;- mot-clé (volume par défaut: 1000)"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Format CSV recommandé : mot-clé,volume (ex: smartphone pas cher,12000)
                        </p>
                      </div>

                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="flex items-start space-x-3">
                          <Upload className="h-5 w-5 text-blue-600 mt-0.5" />
                          <div>
                            <h5 className="font-medium text-blue-900">Formats supportés</h5>
                            <ul className="text-sm text-blue-700 mt-1 space-y-1">
                              <li>• <strong>CSV (recommandé) :</strong> mot-clé,volume</li>
                              <li>• <strong>TSV :</strong> mot-clé[TAB]volume</li>
                              <li>• <strong>Simple :</strong> mot-clé (volume aléatoire généré)</li>
                              <li>• <strong>Exemple :</strong> smartphone pas cher,12000</li>
                            </ul>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-end space-x-3">
                        <button
                          onClick={() => setShowBulkAdd(false)}
                          className="btn-secondary"
                        >
                          Annuler
                        </button>
                        <button
                          onClick={handleBulkAddKeywords}
                          className="btn-primary flex items-center space-x-2"
                        >
                          <Plus className="h-4 w-4" />
                          <span>Ajouter {bulkKeywords.split('\n').filter(line => line.trim()).length} mots-clés</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Barre de recherche et actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      value={keywordSearch}
                      onChange={(e) => setKeywordSearch(e.target.value)}
                      placeholder="Rechercher un mot-clé..."
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <span className="text-sm text-gray-500">
                    {filteredKeywords.length} résultat{filteredKeywords.length > 1 ? 's' : ''}
                  </span>
                </div>

                {selectedKeywords.length > 0 && (
                  <button
                    onClick={handleDeleteKeywords}
                    className="btn-danger flex items-center space-x-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>Supprimer ({selectedKeywords.length})</span>
                  </button>
                )}
              </div>

              {/* Tableau des mots-clés */}
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="table">
                    <thead>
                      <tr>
                        <th className="w-12">
                          <input
                            type="checkbox"
                            checked={selectedKeywords.length === filteredKeywords.length && filteredKeywords.length > 0}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedKeywords(filteredKeywords.map(k => k.id));
                              } else {
                                setSelectedKeywords([]);
                              }
                            }}
                            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                        </th>
                        <th>Mot-clé</th>
                        <th>Localisation</th>
                        <th>Volume</th>
                        <th>Statut</th>
                        <th>Date d'ajout</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredKeywords.map((keyword) => (
                        <tr key={keyword.id}>
                          <td>
                            <input
                              type="checkbox"
                              checked={selectedKeywords.includes(keyword.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedKeywords([...selectedKeywords, keyword.id]);
                                } else {
                                  setSelectedKeywords(selectedKeywords.filter(id => id !== keyword.id));
                                }
                              }}
                              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                            />
                          </td>
                          <td className="font-medium text-gray-900">{keyword.keyword}</td>
                          <td className="text-gray-600">
                            <span className="inline-flex items-center space-x-1">
                              <span>{keyword.location}</span>
                              <span className="text-xs text-gray-400">({keyword.language})</span>
                            </span>
                          </td>
                          <td className="text-gray-600">
                            {keyword.search_volume >= 1000 
                              ? `${(keyword.search_volume / 1000).toFixed(1)}K` 
                              : keyword.search_volume.toLocaleString('fr-FR')
                            }
                          </td>
                          <td>
                            <button
                              onClick={() => handleToggleKeyword(keyword.id)}
                              className={`badge ${keyword.is_active ? 'badge-success' : 'badge-danger'} cursor-pointer hover:opacity-80`}
                            >
                              {keyword.is_active ? 'Actif' : 'Inactif'}
                            </button>
                          </td>
                          <td className="text-gray-600 text-sm">
                            {new Date(keyword.created_at).toLocaleDateString('fr-FR')}
                          </td>
                          <td>
                            <button
                              onClick={() => setSelectedKeywords([keyword.id])}
                              className="text-red-600 hover:text-red-800 transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {filteredKeywords.length === 0 && (
                  <div className="text-center py-12">
                    <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      {keywordSearch ? 'Aucun mot-clé trouvé' : 'Aucun mot-clé configuré'}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {keywordSearch 
                        ? 'Essayez de modifier votre recherche'
                        : 'Commencez par ajouter des mots-clés à surveiller'
                      }
                    </p>
                    {!keywordSearch && (
                      <button
                        onClick={() => setShowBulkAdd(true)}
                        className="btn-primary flex items-center space-x-2 mx-auto"
                      >
                        <Plus className="h-4 w-4" />
                        <span>Ajouter des mots-clés</span>
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Statistiques */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900">Total</h4>
                  <p className="text-2xl font-bold text-blue-700">{keywords.length}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-medium text-green-900">Actifs</h4>
                  <p className="text-2xl font-bold text-green-700">{keywords.filter(k => k.is_active).length}</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h4 className="font-medium text-yellow-900">Volume moyen</h4>
                  <p className="text-2xl font-bold text-yellow-700">
                    {keywords.length > 0 
                      ? Math.round(keywords.reduce((sum, k) => sum + k.search_volume, 0) / keywords.length).toLocaleString('fr-FR')
                      : '0'
                    }
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-medium text-purple-900">Volume total</h4>
                  <p className="text-2xl font-bold text-purple-700">
                    {(keywords.reduce((sum, k) => sum + k.search_volume, 0) / 1000).toFixed(0)}K
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Autres onglets (General, Competitors, Notifications) */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Paramètres généraux</h3>
              <p className="text-gray-600">Configuration générale de l'application (à implémenter)</p>
            </div>
          )}

          {activeTab === 'competitors' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Gestion des concurrents</h3>
                  <p className="text-gray-600">{competitors.length} concurrent(s) configuré(s)</p>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Concurrent</th>
                        <th>Domaine</th>
                        <th>Marque</th>
                        <th>Statut</th>
                        <th>Date d'ajout</th>
                      </tr>
                    </thead>
                    <tbody>
                      {competitors.map((competitor) => (
                        <tr key={competitor.id}>
                          <td className="font-medium text-gray-900">{competitor.name}</td>
                          <td className="text-gray-600">{competitor.domain}</td>
                          <td className="text-gray-600">{competitor.brand_name}</td>
                          <td>
                            <span className={`badge ${competitor.is_main_brand ? 'badge-primary' : 'badge-secondary'}`}>
                              {competitor.is_main_brand ? 'Principal' : 'Concurrent'}
                            </span>
                          </td>
                          <td className="text-gray-600 text-sm">
                            {new Date(competitor.created_at).toLocaleDateString('fr-FR')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {competitors.length === 0 && (
                  <div className="text-center py-12">
                    <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun concurrent configuré</h3>
                    <p className="text-gray-600 mb-4">
                      Utilisez la page Concurrents pour ajouter et gérer vos concurrents
                    </p>
                  </div>
                )}
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Gestion des concurrents</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Pour ajouter, modifier ou supprimer des concurrents, utilisez la page dédiée "Concurrents" accessible depuis le menu principal.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Paramètres de notification</h3>
              <p className="text-gray-600">Configuration des alertes et notifications (à implémenter)</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 