-- Script SQL para inicializar la base de datos PostgreSQL
-- Este script crea las extensiones necesarias antes de ejecutar las migraciones

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para búsqueda de texto con trigram similarity

-- Notas:
-- 1. Ejecutar este script antes de correr las migraciones de Django
-- 2. Las tablas serán creadas automáticamente por Django migrations
-- 3. El resto de la estructura será generada por los modelos de Django
