import React, { useState, useEffect } from 'react';
import { competitorsApi, Competitor } from '../lib/api';
import { useProject } from '../contexts/ProjectContext';
import { Plus, Search, Globe, TrendingUp, TrendingDown, Minus, Edit, Trash2, ExternalLink, BarChart3 } from 'lucide-react';

interface CompetitorWithMetrics extends Competitor {
  // Métriques calculées
  total_keywords?: number;
  avg_position?: number;
  share_of_voice?: number;
  trend?: 'up' | 'down' | 'stable';
}

interface CompetitorsResponse {
  project_id: string;
  competitors: Competitor[];
  total: number;
}

export default function Competitors() {
  const { currentProject } = useProject();
  const [competitors, setCompetitors] = useState<CompetitorWithMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCompetitor, setNewCompetitor] = useState({
    name: '',
    domain: '',
    brand_name: ''
  });
  const [isAdding, setIsAdding] = useState(false);

  const fetchCompetitors = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await competitorsApi.getByProject(projectId);
      setCompetitors(response.data.competitors || []);
    } catch (err: any) {
      console.error('Competitors error:', err);
      setError('Erreur lors du chargement des concurrents');
      
      // Données simulées en cas d'erreur API
      const mockCompetitors: CompetitorWithMetrics[] = [
        {
          id: '1',
          name: 'Amazon France',
          domain: 'amazon.fr',
          brand_name: 'Amazon',
          is_main_brand: false,
          created_at: '2024-01-15T10:00:00Z',
          total_keywords: 45,
          avg_position: 3.2,
          share_of_voice: 24.5,
          trend: 'up'
        },
        {
          id: '2',
          name: 'Fnac',
          domain: 'fnac.com',
          brand_name: 'Fnac',
          is_main_brand: false,
          created_at: '2024-01-10T14:30:00Z',
          total_keywords: 38,
          avg_position: 5.8,
          share_of_voice: 18.7,
          trend: 'stable'
        },
        {
          id: '3',
          name: 'Cdiscount',
          domain: 'cdiscount.com',
          brand_name: 'Cdiscount',
          is_main_brand: false,
          created_at: '2024-01-08T09:15:00Z',
          total_keywords: 32,
          avg_position: 7.1,
          share_of_voice: 15.3,
          trend: 'down'
        },
        {
          id: '4',
          name: 'Darty',
          domain: 'darty.com',
          brand_name: 'Darty',
          is_main_brand: false,
          created_at: '2024-01-05T16:45:00Z',
          total_keywords: 28,
          avg_position: 8.9,
          share_of_voice: 12.8,
          trend: 'up'
        },
        {
          id: '5',
          name: 'Boulanger',
          domain: 'boulanger.com',
          brand_name: 'Boulanger',
          is_main_brand: false,
          created_at: '2024-01-03T11:20:00Z',
          total_keywords: 22,
          avg_position: 11.2,
          share_of_voice: 9.4,
          trend: 'stable'
        }
      ];
      setCompetitors(mockCompetitors);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCompetitor = async () => {
    if (!newCompetitor.name.trim() || !newCompetitor.domain.trim()) return;
    
    setIsAdding(true);
    try {
      const competitorData = {
        name: newCompetitor.name.trim(),
        domain: newCompetitor.domain.trim().replace(/^https?:\/\//, '').replace(/^www\./, ''),
        brand_name: newCompetitor.brand_name.trim() || newCompetitor.name.trim(),
        is_main_brand: false
      };
      
      const response = await competitorsApi.create(currentProject!.id, competitorData);
      
      setCompetitors(prev => [...prev, response.data]);
      setNewCompetitor({ name: '', domain: '', brand_name: '' });
      setShowAddForm(false);
    } catch (err: any) {
      console.error('Erreur ajout concurrent:', err);
      alert('Erreur lors de l\'ajout du concurrent');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteCompetitor = async (competitorId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce concurrent ?')) return;
    
    try {
      await competitorsApi.delete(currentProject!.id, competitorId);
      setCompetitors(prev => prev.filter(c => c.id !== competitorId));
    } catch (err: any) {
      console.error('Erreur suppression concurrent:', err);
      alert('Erreur lors de la suppression du concurrent');
    }
  };

  useEffect(() => {
    if (currentProject?.id) {
      fetchCompetitors(currentProject.id);
    }
  }, [currentProject?.id]);

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Veuillez sélectionner un projet pour gérer les concurrents.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="spinner h-8 w-8"></div>
        <span className="ml-3 text-gray-600">Chargement des concurrents...</span>
      </div>
    );
  }

  // Filtrer les concurrents
  const filteredCompetitors = competitors.filter(comp =>
    comp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    comp.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (comp.brand_name && comp.brand_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getPositionColor = (position?: number) => {
    if (!position) return 'text-gray-500';
    if (position <= 3) return 'text-green-600';
    if (position <= 10) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-lg border border-orange-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Concurrents - {currentProject.name}</h2>
            <p className="text-gray-600 mt-1">Gestion et analyse des concurrents</p>
            <p className="text-sm text-orange-600 mt-2">
              🏆 {competitors.length} concurrent(s) surveillé(s)
            </p>
          </div>
        </div>
      </div>

      {/* Barre d'actions */}
      <div className="card">
        <div className="card-content">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher un concurrent..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            
            <button
              onClick={() => setShowAddForm(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Ajouter un concurrent</span>
            </button>
          </div>
        </div>
      </div>

      {/* Formulaire d'ajout */}
      {showAddForm && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">➕ Ajouter un nouveau concurrent</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom du concurrent *
                </label>
                <input
                  type="text"
                  value={newCompetitor.name}
                  onChange={(e) => setNewCompetitor(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ex: Amazon France"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Domaine *
                </label>
                <input
                  type="text"
                  value={newCompetitor.domain}
                  onChange={(e) => setNewCompetitor(prev => ({ ...prev, domain: e.target.value }))}
                  placeholder="amazon.fr"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Marque (optionnel)
                </label>
                <input
                  type="text"
                  value={newCompetitor.brand_name}
                  onChange={(e) => setNewCompetitor(prev => ({ ...prev, brand_name: e.target.value }))}
                  placeholder="Amazon"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-4">
              <button
                onClick={handleAddCompetitor}
                disabled={!newCompetitor.name.trim() || !newCompetitor.domain.trim() || isAdding}
                className="btn-primary flex items-center space-x-2"
              >
                {isAdding ? (
                  <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                <span>{isAdding ? 'Ajout...' : 'Ajouter'}</span>
              </button>
              
              <button
                onClick={() => {
                  setShowAddForm(false);
                  setNewCompetitor({ name: '', domain: '', brand_name: '' });
                }}
                className="btn-secondary"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Liste des concurrents */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">🏆 Liste des concurrents</h3>
          <p className="text-sm text-gray-600 mt-1">
            {filteredCompetitors.length} concurrent(s) affiché(s)
          </p>
        </div>
        <div className="card-content">
          {filteredCompetitors.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th className="text-left">Concurrent</th>
                    <th className="text-center">Mots-clés</th>
                    <th className="text-center">Position Moy.</th>
                    <th className="text-center">Share of Voice</th>
                    <th className="text-center">Tendance</th>
                    <th className="text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCompetitors.map((competitor) => (
                    <tr key={competitor.id} className="hover:bg-gray-50">
                      <td>
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                              <Globe className="h-4 w-4 text-orange-600" />
                            </div>
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">{competitor.name}</div>
                            <div className="text-sm text-gray-500 flex items-center space-x-1">
                              <span>{competitor.domain}</span>
                              <a 
                                href={`https://${competitor.domain}`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-orange-500 hover:text-orange-700"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            </div>
                            {competitor.brand_name && competitor.brand_name !== competitor.name && (
                              <div className="text-xs text-gray-400">
                                Marque: {competitor.brand_name}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      
                      <td className="text-center">
                        <span className="text-gray-900 font-medium">
                          {competitor.total_keywords || 0}
                        </span>
                      </td>
                      
                      <td className="text-center">
                        <span className={`font-medium ${getPositionColor(competitor.avg_position)}`}>
                          {competitor.avg_position ? `#${competitor.avg_position.toFixed(1)}` : 'N/A'}
                        </span>
                      </td>
                      
                      <td className="text-center">
                        <div className="flex items-center justify-center space-x-1">
                          <span className="text-gray-900 font-medium">
                            {competitor.share_of_voice ? `${competitor.share_of_voice.toFixed(1)}%` : 'N/A'}
                          </span>
                          <BarChart3 className="h-3 w-3 text-gray-400" />
                        </div>
                      </td>
                      
                      <td className="text-center">
                        <div className={`flex items-center justify-center space-x-1 ${getTrendColor(competitor.trend)}`}>
                          {getTrendIcon(competitor.trend)}
                          <span className="text-xs font-medium">
                            {competitor.trend === 'up' ? 'Hausse' : competitor.trend === 'down' ? 'Baisse' : 'Stable'}
                          </span>
                        </div>
                      </td>
                      
                      <td className="text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={() => alert('Fonctionnalité à venir')}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                            title="Modifier"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteCompetitor(competitor.id)}
                            className="text-red-400 hover:text-red-600 transition-colors"
                            title="Supprimer"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Globe className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'Aucun concurrent trouvé' : 'Aucun concurrent ajouté'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchTerm 
                  ? 'Aucun concurrent ne correspond à votre recherche.'
                  : 'Commencez par ajouter vos premiers concurrents à surveiller.'
                }
              </p>
              {!searchTerm && (
                <button
                  onClick={() => setShowAddForm(true)}
                  className="btn-primary flex items-center space-x-2 mx-auto"
                >
                  <Plus className="h-4 w-4" />
                  <span>Ajouter un concurrent</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Note</h3>
              <div className="mt-2 text-sm text-yellow-700">
                Les données affichées sont simulées. L'API des concurrents sera bientôt disponible.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 