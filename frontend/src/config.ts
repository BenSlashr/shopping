/**
 * Configuration de l'application frontend
 */

export const config = {
  // URL de l'API backend
  apiUrl: import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' 
    ? 'http://localhost:8000' 
    : '/shopping/api/v1'),
  
  // Mode de développement
  isDevelopment: import.meta.env.MODE === 'development',
  
  // Timeout par défaut pour les requêtes API (en millisecondes)
  apiTimeout: 30000,
  
  // ID de projet par défaut pour les tests
  defaultProjectId: '343a0815-1200-4b0b-961a-6250d7864228',
  
  // Configuration des graphiques
  chart: {
    colors: [
      '#3b82f6', // blue
      '#ef4444', // red
      '#22c55e', // green
      '#f59e0b', // amber
      '#8b5cf6', // violet
      '#06b6d4', // cyan
      '#f97316', // orange
      '#84cc16', // lime
      '#ec4899', // pink
      '#6b7280', // gray
    ],
    animationDuration: 300,
  },
  
  // Configuration de la pagination
  pagination: {
    defaultPageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
  },
  
  // Configuration du cache local
  cache: {
    // Durée de vie du cache en millisecondes
    ttl: 5 * 60 * 1000, // 5 minutes
  },
} as const;

export default config; 