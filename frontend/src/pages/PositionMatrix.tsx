import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';
import { useProject } from '../contexts/ProjectContext';
import { Search, Filter, Download, Target } from 'lucide-react';

interface PositionMatrixItem {
  keyword: string;
  keyword_id: string;
  search_volume?: number;
  competitors: Record<string, number | null>;
  best_position?: number;
  worst_position?: number;
  opportunity_score: number;
}

interface PositionMatrixResponse {
  project_id: string;
  period_start: string;
  period_end: string;
  keywords: PositionMatrixItem[];
  competitor_domains: string[];
}

export default function PositionMatrix() {
  const { currentProject } = useProject();
  const [data, setData] = useState<PositionMatrixResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'keyword' | 'volume' | 'opportunity'>('opportunity');
  const [filterPosition, setFilterPosition] = useState<'all' | 'top10' | 'top20' | 'below20'>('all');

  const fetchPositionMatrix = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/analytics/position-matrix/${projectId}`);
      setData(response.data);
    } catch (err: any) {
      console.error('Position Matrix error:', err);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentProject?.id) {
      fetchPositionMatrix(currentProject.id);
    }
  }, [currentProject?.id]);

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Veuillez sélectionner un projet pour voir la matrice de positions.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="spinner h-8 w-8"></div>
        <span className="ml-3 text-gray-600">Chargement de la matrice de positions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button 
          onClick={() => fetchPositionMatrix(currentProject.id)}
          className="btn-primary"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!data || !data.keywords || data.keywords.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-600">Aucune donnée de matrice de positions disponible pour ce projet</div>
        <p className="text-sm text-gray-500 mt-2">
          Lancez un scraping pour collecter les données de positions
        </p>
      </div>
    );
  }

  const keywords = data.keywords;
  const competitors = data.competitor_domains;

  // Calculer la position de notre site (utiliser le site de référence du projet)
  const getOurPosition = (keyword: PositionMatrixItem) => {
    if (!currentProject?.reference_domain) return null;
    // Chercher notre domaine dans les concurrents
    const ourDomain = Object.keys(keyword.competitors).find(domain => 
      domain.includes(currentProject.reference_domain.replace('www.', ''))
    );
    return ourDomain ? keyword.competitors[ourDomain] : null;
  };

  // Filtrer et trier les mots-clés
  const filteredKeywords = keywords
    .filter(kw => {
      const ourPos = getOurPosition(kw);
      return kw.keyword.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (filterPosition === 'all' ||
         (filterPosition === 'top10' && ourPos && ourPos <= 10) ||
         (filterPosition === 'top20' && ourPos && ourPos <= 20) ||
         (filterPosition === 'below20' && (!ourPos || ourPos > 20)));
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'keyword':
          return a.keyword.localeCompare(b.keyword);
        case 'volume':
          return (b.search_volume || 0) - (a.search_volume || 0);
        case 'opportunity':
          return b.opportunity_score - a.opportunity_score;
        default:
          return 0;
      }
    });

  const getPositionColor = (position?: number) => {
    if (!position) return 'bg-gray-100 text-gray-500';
    if (position <= 3) return 'bg-green-100 text-green-800';
    if (position <= 10) return 'bg-yellow-100 text-yellow-800';
    if (position <= 20) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const getOpportunityColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    if (score >= 40) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Matrice de Positions - {currentProject.name}</h2>
            <p className="text-gray-600 mt-1">Analyse comparative des positions par mot-clé</p>
            <p className="text-sm text-blue-600 mt-2">
              🎯 {keywords.length} mots-clés analysés • {competitors.length} concurrents
            </p>
          </div>
        </div>
      </div>

      {/* Filtres et recherche */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">🔍 Filtres et Recherche</h3>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Recherche */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher un mot-clé..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Tri */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="opportunity">Trier par opportunité</option>
              <option value="volume">Trier par volume</option>
              <option value="keyword">Trier par mot-clé</option>
            </select>

            {/* Filtre position */}
            <select
              value={filterPosition}
              onChange={(e) => setFilterPosition(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Toutes positions</option>
              <option value="top10">Top 10</option>
              <option value="top20">Top 20</option>
              <option value="below20">Au-delà de 20</option>
            </select>

            {/* Export */}
            <button className="btn-secondary flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Exporter</span>
            </button>
          </div>
        </div>
      </div>

      {/* Matrice */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">📊 Matrice de Positions</h3>
          <p className="text-sm text-gray-600 mt-1">
            {filteredKeywords.length} résultats • Positions dans le top 20 des SERP
          </p>
        </div>
        <div className="card-content">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="text-left">Mot-clé</th>
                  <th className="text-center">Volume</th>
                  <th className="text-center">Notre Position</th>
                  {competitors.map(domain => (
                    <th key={domain} className="text-center text-xs">
                      {domain.replace('.com', '').replace('.fr', '')}
                    </th>
                  ))}
                  <th className="text-center">Opportunité</th>
                </tr>
              </thead>
              <tbody>
                {filteredKeywords.map((keyword, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="font-medium text-gray-900">
                      <div className="flex items-center space-x-2">
                        <Target className="h-4 w-4 text-gray-400" />
                        <span>{keyword.keyword}</span>
                      </div>
                    </td>
                    <td className="text-center text-gray-600">
                      {keyword.search_volume && keyword.search_volume >= 1000 
                        ? `${(keyword.search_volume / 1000).toFixed(1)}K` 
                        : keyword.search_volume || 'N/A'}
                    </td>
                    <td className="text-center">
                      {(() => {
                        const ourPos = getOurPosition(keyword);
                        return (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(ourPos || undefined)}`}>
                            {ourPos ? `#${ourPos}` : 'N/A'}
                          </span>
                        );
                      })()}
                    </td>
                    {competitors.map(domain => (
                      <td key={domain} className="text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPositionColor(keyword.competitors[domain] || undefined)}`}>
                          {keyword.competitors[domain] ? `#${keyword.competitors[domain]}` : 'N/A'}
                        </span>
                      </td>
                    ))}
                    <td className="text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getOpportunityColor(keyword.opportunity_score)}`}>
                        {keyword.opportunity_score}/100
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredKeywords.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Target className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Aucun mot-clé ne correspond aux filtres sélectionnés</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 