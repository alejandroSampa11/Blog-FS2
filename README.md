# Blog Full Stack

Un sistema de blog completo desarrollado con Django que incluye gestión de posts, comentarios, categorías y sistema de autenticación.

## Tech Stack

### Backend
- **Django 4.2+** - Framework web principal
- **Python 3.11** - Lenguaje de programación
- **PostgreSQL 15** - Base de datos
- **Gunicorn** - Servidor WSGI para producción

### Frontend
- **Django Templates** - Sistema de plantillas
- **CKEditor** - Editor de texto enriquecido

### Librerías Principales
- **Pillow** - Procesamiento de imágenes
- **django-ckeditor** - Integración de CKEditor
- **django-taggit** - Sistema de etiquetas
- **python-slugify** - Generación de slugs
- **WhiteNoise** - Servicio de archivos estáticos
- **psycopg2-binary** - Adaptador PostgreSQL

### DevOps
- **Docker & Docker Compose** - Containerización
- **GitHub Actions** - CI/CD

## Características

- Sistema de autenticación de usuarios personalizado
- Creación, edición y eliminación de posts con editor enriquecido
- Sistema de comentarios anidados
- Categorías y etiquetas para posts
- Búsqueda de posts
- Panel de administración de Django
- Carga de imágenes
- Diseño responsive

## Requisitos Previos

- Docker y Docker Compose (recomendado)
- O Python 3.11+ y PostgreSQL 15 (para desarrollo local sin Docker)

## Instalación y Ejecución

### Opción 1: Con Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd Blog-FS2
   ```

2. **Crear archivo .env**
   
   Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```env
   # Django
   SECRET_KEY=tu-clave-secreta-aqui
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # PostgreSQL
   POSTGRES_DB=blogdb
   POSTGRES_USER=bloguser
   POSTGRES_PASSWORD=tu-password-seguro
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```

3. **Levantar los contenedores**
   ```bash
   docker-compose up -d
   ```

   Esto iniciará:
   - Base de datos PostgreSQL en el puerto interno
   - Aplicación Django en http://localhost:8000

4. **Crear superusuario (opcional)**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Cargar datos de ejemplo (opcional)**
   ```bash
   docker-compose exec web python create_sample_data.py
   ```

### Opción 2: Desarrollo Local sin Docker

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd Blog-FS2
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar PostgreSQL**
   
   Asegúrate de tener PostgreSQL instalado y ejecutándose. Crea una base de datos:
   ```sql
   CREATE DATABASE blogdb;
   CREATE USER bloguser WITH PASSWORD 'tu-password';
   GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
   ```

5. **Crear archivo .env**
   ```env
   SECRET_KEY=tu-clave-secreta-aqui
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   POSTGRES_DB=blogdb
   POSTGRES_USER=bloguser
   POSTGRES_PASSWORD=tu-password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

6. **Ejecutar migraciones**
   ```bash
   python manage.py migrate
   ```

7. **Recolectar archivos estáticos**
   ```bash
   python manage.py collectstatic
   ```

8. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

9. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

   La aplicación estará disponible en http://localhost:8000

## Comandos Útiles

### Con Docker

```bash
# Ver logs
docker-compose logs -f web

# Detener contenedores
docker-compose down

# Reconstruir contenedores
docker-compose up -d --build

# Ejecutar comandos de Django
docker-compose exec web python manage.py <comando>

# Acceder a shell de Django
docker-compose exec web python manage.py shell

# Ejecutar tests
docker-compose exec web python manage.py test
```

### Sin Docker

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Acceder a shell de Django
python manage.py shell

# Ejecutar tests
python manage.py test

# Crear superusuario
python manage.py createsuperuser
```

## Estructura del Proyecto

```
Blog-FS2/
├── config/              # Configuración de Django
│   ├── settings.py     # Settings principal
│   ├── urls.py         # URLs principales
│   └── wsgi.py         # Configuración WSGI
├── core/               # Aplicación principal
│   ├── models.py       # Modelos (User, Post, Comment, Category)
│   ├── views.py        # Vistas
│   ├── forms.py        # Formularios
│   ├── admin.py        # Configuración del admin
│   ├── templates/      # Plantillas HTML
│   └── tests.py        # Tests
├── media/              # Archivos subidos por usuarios
├── staticfiles/        # Archivos estáticos recolectados
├── .github/            # Configuración de GitHub Actions
├── docker-compose.yml  # Configuración de Docker Compose
├── Dockerfile          # Dockerfile para la aplicación
├── requirements.txt    # Dependencias de Python
├── manage.py          # Script de gestión de Django
└── create_sample_data.py  # Script para crear datos de ejemplo
```

## Panel de Administración

Accede al panel de administración en http://localhost:8000/admin/ usando las credenciales del superusuario que creaste.

Desde el panel puedes:
- Gestionar usuarios
- Crear y editar posts
- Moderar comentarios
- Administrar categorías

## Despliegue

El proyecto incluye configuración de GitHub Actions para despliegue automático. Consulta la carpeta `.github/workflows/` para más detalles.

Para producción, asegúrate de:
1. Configurar `DEBUG=False` en el archivo `.env`
2. Actualizar `ALLOWED_HOSTS` con tu dominio
3. Usar una `SECRET_KEY` segura y única
4. Configurar variables de entorno seguras para PostgreSQL
5. Configurar un servidor de archivos estáticos apropiado

## Tests

El proyecto incluye tests completos en `core/tests.py`. Para ejecutarlos:

```bash
# Con Docker
docker-compose exec web python manage.py test

# Sin Docker
python manage.py test
```
