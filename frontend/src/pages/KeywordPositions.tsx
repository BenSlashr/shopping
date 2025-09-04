import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';
import { useProject } from '../contexts/ProjectContext';
import { ArrowUp, ArrowDown, Minus, Plus, ExternalLink, RefreshCw } from 'lucide-react';

interface KeywordPosition {
  keyword_id: string;
  keyword: string;
  search_volume: number;
  current_position: number | null;
  previous_position: number | null;
  trend: 'up' | 'down' | 'stable' | 'new' | 'lost';
  current_url: string | null;
  total_urls_positioned: number;
  last_scraped: string | null;
}

interface KeywordPositionsResponse {
  project_id: string;
  reference_site: string;
  total_keywords: number;
  positioned_keywords: number;
  keywords: KeywordPosition[];
}

const KeywordPositions: React.FC = () => {
  const { currentProject } = useProject();
  const [data, setData] = useState<KeywordPositionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'position' | 'keyword' | 'volume' | 'trend'>('position');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const fetchKeywordPositions = async (projectId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const timestamp = Date.now();
      const response = await apiClient.get(`/analytics/keywords-positions/${projectId}?_t=${timestamp}`);
      setData(response.data);
    } catch (err: any) {
      console.error('Keyword positions error:', err);
      setError('Erreur lors du chargement des positions des mots-clés');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentProject?.id) {
      fetchKeywordPositions(currentProject.id);
    }
  }, [currentProject?.id]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <ArrowUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <ArrowDown className="h-4 w-4 text-red-600" />;
      case 'new':
        return <Plus className="h-4 w-4 text-blue-600" />;
      case 'lost':
        return <Minus className="h-4 w-4 text-gray-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTrendText = (trend: string) => {
    switch (trend) {
      case 'up':
        return 'Amélioration';
      case 'down':
        return 'Dégradation';
      case 'new':
        return 'Nouveau';
      case 'lost':
        return 'Perdu';
      default:
        return 'Stable';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Jamais';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredAndSortedKeywords = React.useMemo(() => {
    if (!data?.keywords) return [];

    let filtered = data.keywords.filter(keyword =>
      keyword.keyword.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'position':
          aValue = a.current_position || 999;
          bValue = b.current_position || 999;
          break;
        case 'keyword':
          aValue = a.keyword.toLowerCase();
          bValue = b.keyword.toLowerCase();
          break;
        case 'volume':
          aValue = a.search_volume || 0;
          bValue = b.search_volume || 0;
          break;
        case 'trend':
          const trendOrder = { 'up': 1, 'new': 2, 'stable': 3, 'down': 4, 'lost': 5 };
          aValue = trendOrder[a.trend as keyof typeof trendOrder] || 6;
          bValue = trendOrder[b.trend as keyof typeof trendOrder] || 6;
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
  }, [data?.keywords, searchTerm, sortBy, sortOrder]);

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
          <p className="text-gray-600">Veuillez sélectionner un projet pour afficher les positions des mots-clés.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="spinner h-8 w-8"></div>
        <span className="ml-3 text-gray-600">Chargement des positions des mots-clés...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button 
          onClick={() => fetchKeywordPositions(currentProject.id)}
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
        <div className="text-gray-600">Aucune donnée de position disponible pour ce projet</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Suivi des Positions</h1>
          <p className="text-gray-600 mt-1">
            Positions détaillées pour <strong>{data.reference_site}</strong>
          </p>
        </div>
        <button
          onClick={() => fetchKeywordPositions(currentProject.id)}
          className="btn-primary flex items-center"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </button>
      </div>

      {/* Statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Mots-clés Total</h3>
          <p className="text-3xl font-bold text-gray-900">{data.total_keywords}</p>
        </div>
        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Positionnés</h3>
          <p className="text-3xl font-bold text-green-600">{data.positioned_keywords}</p>
        </div>
        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Taux de Positionnement</h3>
          <p className="text-3xl font-bold text-blue-600">
            {data.total_keywords > 0 ? Math.round((data.positioned_keywords / data.total_keywords) * 100) : 0}%
          </p>
        </div>
        <div className="card card-content">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Améliorations</h3>
          <p className="text-3xl font-bold text-green-600">
            {filteredAndSortedKeywords.filter(k => k.trend === 'up').length}
          </p>
        </div>
      </div>

      {/* Filtres et recherche */}
      <div className="card card-content">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Rechercher un mot-clé..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="position">Position</option>
              <option value="keyword">Mot-clé</option>
              <option value="volume">Volume</option>
              <option value="trend">Tendance</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      {/* Tableau des positions */}
      <div className="card card-content overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mot-clé
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Volume
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position Actuelle
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position Précédente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tendance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  URL
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  URLs Positionnées
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SERP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dernière MAJ
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedKeywords.map((keyword) => (
                <tr key={keyword.keyword_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{keyword.keyword}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {keyword.search_volume.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {keyword.current_position ? (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        keyword.current_position <= 3 ? 'bg-green-100 text-green-800' :
                        keyword.current_position <= 10 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        #{keyword.current_position}
                      </span>
                    ) : (
                      <span className="text-gray-400">Non positionné</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {keyword.previous_position ? `#${keyword.previous_position}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getTrendIcon(keyword.trend)}
                      <span className="ml-2 text-sm text-gray-600">
                        {getTrendText(keyword.trend)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {keyword.current_url ? (
                      <a
                        href={keyword.current_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-800 flex items-center"
                      >
                        <span className="truncate max-w-48">{keyword.current_url}</span>
                        <ExternalLink className="h-3 w-3 ml-1 flex-shrink-0" />
                      </a>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {keyword.total_urls_positioned}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {keyword.last_scraped ? (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        keyword.last_scraped && new Date(keyword.last_scraped) > new Date(Date.now() - 24 * 60 * 60 * 1000) 
                          ? 'bg-green-100 text-green-800' 
                          : keyword.last_scraped && new Date(keyword.last_scraped) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {formatDate(keyword.last_scraped)}
                      </span>
                    ) : (
                      <span className="text-gray-400">Jamais vérifié</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(keyword.last_scraped)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {filteredAndSortedKeywords.length === 0 && searchTerm && (
        <div className="text-center py-8 text-gray-500">
          Aucun mot-clé trouvé pour "{searchTerm}"
        </div>
      )}
    </div>
  );
};

export default KeywordPositions; 