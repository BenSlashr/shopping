import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Users, 
  Eye,
  AlertTriangle,
  RefreshCw,
  Calendar
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { analyticsApi, type DashboardResponse } from '../lib/api';
import { 
  formatNumber, 
  formatPercentage, 
  formatPosition, 
  formatRelativeTime,
  getTrendColor,
  getPositionColor,
  getChartColor
} from '../lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  color?: string;
  trend?: 'up' | 'down' | 'stable';
}

function MetricCard({ title, value, change, icon: Icon, color = 'primary', trend }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change !== undefined && (
            <div className={`flex items-center mt-2 text-sm ${getTrendColor(trend || 'stable')}`}>
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : trend === 'down' ? (
                <TrendingDown className="h-4 w-4 mr-1" />
              ) : null}
              {change > 0 ? '+' : ''}{change.toFixed(1)}%
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  );
}

interface DashboardProps {
  projectId: string;
}

export default function Dashboard({ projectId }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await analyticsApi.getDashboard(projectId);
      setDashboardData(response.data);
      setLastRefresh(new Date());
    } catch (err) {
      setError('Erreur lors du chargement des données');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-2 text-gray-600">Chargement des données...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-danger-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-danger-800">Erreur</h3>
            <p className="text-sm text-danger-700 mt-1">{error}</p>
            <button
              onClick={fetchDashboardData}
              className="btn-primary mt-3"
            >
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return <div>Aucune donnée disponible</div>;
  }

  const { metrics, top_keywords, top_competitors, recent_changes } = dashboardData;

  // Données pour le graphique Share of Voice
  const shareOfVoiceData = top_competitors.map((competitor, index) => ({
    name: competitor.name,
    share: competitor.share_of_voice,
    position: competitor.avg_position,
    fill: getChartColor(index)
  }));

  // Données pour le graphique des positions
  const positionsData = top_keywords.map(keyword => ({
    keyword: keyword.keyword.length > 15 
      ? keyword.keyword.substring(0, 15) + '...' 
      : keyword.keyword,
    position: keyword.position,
    volume: keyword.volume
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header avec informations du projet */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">{dashboardData.project_name}</h2>
          <p className="text-gray-600 mt-1">
            Dernière mise à jour: {formatRelativeTime(lastRefresh.toISOString())}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            className="btn-outline"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
          <button className="btn-primary">
            <Calendar className="h-4 w-4 mr-2" />
            Période
          </button>
        </div>
      </div>

      {/* Métriques principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Mots-clés surveillés"
          value={formatNumber(metrics.total_keywords)}
          icon={Target}
          color="primary"
        />
        <MetricCard
          title="Position moyenne"
          value={formatPosition(Math.round(metrics.average_position))}
          icon={TrendingUp}
          color="success"
        />
        <MetricCard
          title="Share of Voice"
          value={formatPercentage(metrics.share_of_voice)}
          icon={Eye}
          color="warning"
        />
        <MetricCard
          title="Score de visibilité"
          value={`${metrics.visibility_score.toFixed(1)}/100`}
          icon={Users}
          color="primary"
        />
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Share of Voice */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Share of Voice par concurrent</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={shareOfVoiceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, share }) => `${name}: ${share.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="share"
                >
                  {shareOfVoiceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Share of Voice']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Positions des mots-clés */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Top mots-clés</h3>
          </div>
          <div className="card-content">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={positionsData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="keyword" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis reversed domain={[1, 20]} />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    name === 'position' ? `Position #${value}` : formatNumber(value as number),
                    name === 'position' ? 'Position' : 'Volume'
                  ]}
                />
                <Legend />
                <Bar dataKey="position" fill="#3b82f6" name="Position" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Tableaux */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Keywords */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Mots-clés performants</h3>
          </div>
          <div className="card-content">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Mot-clé</th>
                    <th>Position</th>
                    <th>Volume</th>
                    <th>Tendance</th>
                  </tr>
                </thead>
                <tbody>
                  {top_keywords.map((keyword, index) => (
                    <tr key={index}>
                      <td className="font-medium">{keyword.keyword}</td>
                      <td>
                        <span className={getPositionColor(keyword.position)}>
                          {formatPosition(keyword.position)}
                        </span>
                      </td>
                      <td>{formatNumber(keyword.volume)}</td>
                      <td>
                        <span className={getTrendColor(keyword.trend)}>
                          {keyword.trend === 'up' ? '↗' : keyword.trend === 'down' ? '↘' : '→'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Top Competitors */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Concurrents principaux</h3>
          </div>
          <div className="card-content">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Concurrent</th>
                    <th>Share of Voice</th>
                    <th>Position moy.</th>
                  </tr>
                </thead>
                <tbody>
                  {top_competitors.map((competitor, index) => (
                    <tr key={index}>
                      <td>
                        <div>
                          <div className="font-medium">{competitor.name}</div>
                          <div className="text-sm text-gray-500">{competitor.domain}</div>
                        </div>
                      </td>
                      <td>{formatPercentage(competitor.share_of_voice)}</td>
                      <td>
                        <span className={getPositionColor(Math.round(competitor.avg_position))}>
                          {formatPosition(Math.round(competitor.avg_position))}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Changements récents */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">Changements récents</h3>
        </div>
        <div className="card-content">
          <div className="space-y-4">
            {recent_changes.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Aucun changement récent</p>
            ) : (
              recent_changes.map((change, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {change.change.startsWith('+') ? (
                        <TrendingUp className="h-5 w-5 text-success-600" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-danger-600" />
                      )}
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        {change.keyword}
                      </p>
                      <p className="text-sm text-gray-500">
                        Position {change.old_position} → {change.new_position}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      change.change.startsWith('+') ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'
                    }`}>
                      {change.change}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatRelativeTime(change.date)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 