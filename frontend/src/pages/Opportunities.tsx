import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';
import { useProject } from '../contexts/ProjectContext';
import { TrendingUp, Target, AlertCircle, CheckCircle, Clock, Filter } from 'lucide-react';

interface OpportunityItem {
  type: 'keyword_gap' | 'price_advantage' | 'position_improvement' | 'new_competitor';
  title: string;
  description: string;
  keyword_id?: string;
  keyword?: string;
  competitor_domain?: string;
  current_position?: number;
  target_position?: number;
  potential_gain: number;
  priority: 'high' | 'medium' | 'low';
  action_items: string[];
}

interface OpportunitiesResponse {
  project_id: string;
  analysis_date: string;
  total_opportunities: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  opportunities: OpportunityItem[];
}

export default function Opportunities() {
  const { currentProject } = useProject();
  const [data, setData] = useState<OpportunitiesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterPriority, setFilterPriority] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [filterType, setFilterType] = useState<'all' | 'keyword_gap' | 'position_improvement' | 'price_advantage' | 'new_competitor'>('all');

  const fetchOpportunities = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/api/v1/analytics/opportunities/${projectId}`);
      setData(response.data);
    } catch (err: any) {
      console.error('Opportunities error:', err);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentProject?.id) {
      fetchOpportunities(currentProject.id);
    }
  }, [currentProject?.id]);

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Veuillez sélectionner un projet pour voir les opportunités.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="spinner h-8 w-8"></div>
        <span className="ml-3 text-gray-600">Analyse des opportunités en cours...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button 
          onClick={() => fetchOpportunities(currentProject.id)}
          className="btn-primary"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!data || !data.opportunities || data.opportunities.length === 0) {
    return (
      <div className="text-center py-12">
        <Target className="h-16 w-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune opportunité détectée</h3>
        <p className="text-gray-600">Aucune opportunité n'a été identifiée pour ce projet.</p>
        <p className="text-sm text-gray-500 mt-2">
          Lancez un scraping pour analyser les données et détecter des opportunités
        </p>
      </div>
    );
  }

  const opportunities = data.opportunities;
  const stats = data;

  // Filtrer les opportunités
  const filteredOpportunities = opportunities.filter(opp => 
    (filterPriority === 'all' || opp.priority === filterPriority) &&
    (filterType === 'all' || opp.type === filterType)
  );

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'keyword_gap': return <Target className="h-5 w-5 text-blue-500" />;
      case 'position_improvement': return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'price_advantage': return <CheckCircle className="h-5 w-5 text-purple-500" />;
      case 'new_competitor': return <AlertCircle className="h-5 w-5 text-orange-500" />;
      default: return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'keyword_gap': return 'Mot-clé manqué';
      case 'position_improvement': return 'Amélioration position';
      case 'price_advantage': return 'Avantage prix';
      case 'new_competitor': return 'Nouveau concurrent';
      default: return 'Autre';
    }
  };


  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Opportunités - {currentProject.name}</h2>
            <p className="text-gray-600 mt-1">Identification des opportunités d'amélioration SEO</p>
            <p className="text-sm text-purple-600 mt-2">
              🎯 {stats.total_opportunities} opportunités détectées • Dernière analyse: {new Date(stats.analysis_date).toLocaleDateString('fr-FR')}
            </p>
          </div>
        </div>
      </div>

      {/* Métriques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Opportunités</h3>
          <p className="text-3xl font-bold text-gray-900">{stats.total_opportunities}</p>
        </div>

        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Priorité Haute</h3>
          <p className="text-3xl font-bold text-red-600">{stats.high_priority}</p>
        </div>

        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Priorité Moyenne</h3>
          <p className="text-3xl font-bold text-yellow-600">{stats.medium_priority}</p>
        </div>

        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Priorité Basse</h3>
          <p className="text-3xl font-bold text-green-600">{stats.low_priority}</p>
        </div>
      </div>

      {/* Filtres */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">🔍 Filtres</h3>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Priorité</label>
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">Toutes les priorités</option>
                <option value="high">Priorité haute</option>
                <option value="medium">Priorité moyenne</option>
                <option value="low">Priorité basse</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Type d'opportunité</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">Tous les types</option>
                <option value="keyword_gap">Mots-clés manqués</option>
                <option value="position_improvement">Amélioration position</option>
                <option value="price_advantage">Avantage prix</option>
                <option value="new_competitor">Nouveau concurrent</option>
              </select>
            </div>

            <div className="flex items-end">
              <div className="text-sm text-gray-600">
                {filteredOpportunities.length} opportunité(s) affichée(s)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Liste des opportunités */}
      <div className="space-y-4">
        {filteredOpportunities.map((opportunity, index) => (
          <div key={index} className="card">
            <div className="card-content">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="flex-shrink-0 mt-1">
                    {getTypeIcon(opportunity.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{opportunity.title}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(opportunity.priority)}`}>
                        {opportunity.priority === 'high' ? 'Haute' : opportunity.priority === 'medium' ? 'Moyenne' : 'Basse'}
                      </span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {getTypeLabel(opportunity.type)}
                      </span>
                    </div>
                    
                    <p className="text-gray-600 mb-3">{opportunity.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      {opportunity.keyword && (
                        <div>
                          <span className="text-sm font-medium text-gray-500">Mot-clé:</span>
                          <p className="text-sm text-gray-900">{opportunity.keyword}</p>
                        </div>
                      )}
                      
                      {opportunity.current_position && (
                        <div>
                          <span className="text-sm font-medium text-gray-500">Position actuelle:</span>
                          <p className="text-sm text-gray-900">#{opportunity.current_position}</p>
                        </div>
                      )}
                      
                      {opportunity.target_position && (
                        <div>
                          <span className="text-sm font-medium text-gray-500">Position cible:</span>
                          <p className="text-sm text-gray-900">#{opportunity.target_position}</p>
                        </div>
                      )}
                      
                      {opportunity.competitor_domain && (
                        <div>
                          <span className="text-sm font-medium text-gray-500">Concurrent:</span>
                          <p className="text-sm text-gray-900">{opportunity.competitor_domain}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="mb-4">
                      <span className="text-sm font-medium text-gray-500 mb-2 block">Actions recommandées:</span>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {opportunity.action_items.map((action, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <span className="text-purple-500 mt-1">•</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                
                <div className="flex-shrink-0 text-right">
                  <div className="text-2xl font-bold text-purple-600 mb-1">
                    {opportunity.potential_gain.toFixed(1)}/100
                  </div>
                  <div className="text-xs text-gray-500 mb-2">Potentiel</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredOpportunities.length === 0 && (
        <div className="text-center py-12">
          <Target className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune opportunité trouvée</h3>
          <p className="text-gray-600">Aucune opportunité ne correspond aux filtres sélectionnés.</p>
        </div>
      )}
    </div>
  );
} 