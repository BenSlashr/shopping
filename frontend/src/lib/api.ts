import axios from 'axios';
import config from '../config';

// Configuration de base de l'API
const API_BASE_URL = config.apiUrl;

// Instance Axios configurée
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: config.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour les requêtes
apiClient.interceptors.request.use(
  (config) => {
    // Ajouter un token d'authentification si disponible
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour les réponses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Gérer l'expiration du token
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types pour les réponses API
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// Types pour les projets
export interface Project {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  competitors_count: number;
  keywords_count: number;
}

export interface CreateProjectRequest {
  name: string;
  description: string;
  main_brand_domain: string;
}

// Types pour les analytics
export interface DashboardMetrics {
  total_keywords: number;
  total_competitors: number;
  average_position: number;
  share_of_voice: number;
  total_opportunities: number;
  visibility_score: number;
  last_scrape_date?: string;
}

export interface DashboardResponse {
  project_id: string;
  project_name: string;
  metrics: DashboardMetrics;
  top_keywords: Array<{
    keyword: string;
    position: number;
    volume: number;
    trend: 'up' | 'down' | 'stable';
  }>;
  top_competitors: Array<{
    name: string;
    domain: string;
    share_of_voice: number;
    avg_position: number;
  }>;
  recent_changes: Array<{
    type: string;
    keyword: string;
    old_position?: number;
    new_position?: number;
    change: string;
    date: string;
  }>;
}

export interface ShareOfVoiceItem {
  competitor_id: string;
  competitor_name: string;
  domain: string;
  appearances: number;
  total_keywords: number;
  share_percentage: number;
  average_position: number;
  price_competitiveness?: number;
}

export interface ShareOfVoiceResponse {
  project_id: string;
  period_start: string;
  period_end: string;
  total_appearances: number;
  competitors: ShareOfVoiceItem[];
}

export interface PositionMatrixItem {
  keyword: string;
  keyword_id: string;
  search_volume?: number;
  competitors: Record<string, number | null>;
  best_position?: number;
  worst_position?: number;
  opportunity_score: number;
}

export interface PositionMatrixResponse {
  project_id: string;
  period_start: string;
  period_end: string;
  keywords: PositionMatrixItem[];
  competitor_domains: string[];
}

export interface OpportunityItem {
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

export interface OpportunitiesResponse {
  project_id: string;
  analysis_date: string;
  total_opportunities: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  opportunities: OpportunityItem[];
}

// API Functions

// Projets
export const projectsApi = {
  getAll: (page = 1, per_page = 20) =>
    apiClient.get<PaginatedResponse<Project>>('/projects', {
      params: { page, per_page },
    }),

  getById: (id: string) =>
    apiClient.get<Project>(`/projects/${id}`),

  create: (data: CreateProjectRequest) =>
    apiClient.post<Project>('/projects', data),

  update: (id: string, data: Partial<CreateProjectRequest>) =>
    apiClient.put<Project>(`/projects/${id}`, data),

  delete: (id: string) =>
    apiClient.delete(`/projects/${id}`),
};

// Analytics
export const analyticsApi = {
  getDashboard: (projectId: string) =>
    apiClient.get<DashboardResponse>(`/analytics/dashboard/${projectId}`),

  getShareOfVoice: (projectId: string, periodStart?: string, periodEnd?: string) =>
    apiClient.get<ShareOfVoiceResponse>(`/analytics/share-of-voice/${projectId}`, {
      params: { period_start: periodStart, period_end: periodEnd },
    }),

  getPositionMatrix: (projectId: string, periodStart?: string, periodEnd?: string) =>
    apiClient.get<PositionMatrixResponse>(`/analytics/position-matrix/${projectId}`, {
      params: { period_start: periodStart, period_end: periodEnd },
    }),

  getOpportunities: (projectId: string, periodStart?: string, periodEnd?: string) =>
    apiClient.get<OpportunitiesResponse>(`/analytics/opportunities/${projectId}`, {
      params: { period_start: periodStart, period_end: periodEnd },
    }),

  getTrends: (projectId: string, metricType: string = 'share_of_voice', periodType: string = 'day') =>
    apiClient.get(`/analytics/trends/${projectId}`, {
      params: { metric_type: metricType, period_type: periodType },
    }),
};

// Scraping
export const scrapingApi = {
  testDataForSEO: () =>
    apiClient.get('/test-dataforseo'),

  scrapeProject: (projectId: string) =>
    apiClient.post(`/scraping/projects/${projectId}/analyze`),

  scrapeKeyword: (projectId: string, keywordId: string) =>
    apiClient.post(`/scraping/projects/${projectId}/keywords/${keywordId}/analyze`),
};

// Competitors
export interface Competitor {
  id: string;
  name: string;
  domain: string;
  brand_name: string;
  is_main_brand: boolean;
  created_at: string;
}

export interface CreateCompetitorRequest {
  name: string;
  domain: string;
  brand_name: string;
  is_main_brand?: boolean;
}

export const competitorsApi = {
  getByProject: (projectId: string) =>
    apiClient.get<{ competitors: Competitor[], total: number }>(`/projects/${projectId}/competitors`),

  create: (projectId: string, data: CreateCompetitorRequest) =>
    apiClient.post<Competitor>(`/projects/${projectId}/competitors`, data),

  delete: (projectId: string, competitorId: string) =>
    apiClient.delete(`/projects/${projectId}/competitors/${competitorId}`),
};

// Health check
export const healthApi = {
  check: () => apiClient.get('/health'),
}; 