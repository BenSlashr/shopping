-- Script d'initialisation pour Shopping Monitor PostgreSQL

-- Créer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configuration pour améliorer les performances
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Configuration pour les recherches textuelles
ALTER SYSTEM SET default_text_search_config = 'french';

-- Créer un utilisateur pour l'application avec les permissions appropriées
-- (déjà créé par les variables d'environnement Docker)

-- Accorder les permissions sur la base de données
GRANT ALL PRIVILEGES ON DATABASE shopping_monitor TO shopping_user;
GRANT ALL ON SCHEMA public TO shopping_user;

-- Message de confirmation
SELECT 'Base de données Shopping Monitor initialisée avec succès!' as message; 