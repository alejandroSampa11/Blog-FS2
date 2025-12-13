"""
Script para crear datos de ejemplo en el blog
Ejecutar: python manage.py shell < create_sample_data.py
"""

from django.utils import timezone
from core.models import User, Category, Tag, Post
import uuid

# Crear usuario admin si no existe
admin_email = "admin@blog.com"
if not User.objects.filter(email=admin_email).exists():
    admin = User.objects.create_superuser(
        email=admin_email,
        username="admin",
        password="admin123",
        full_name="Administrador del Blog",
        role="admin"
    )
    print(f"✅ Usuario admin creado: {admin_email} / admin123")
else:
    admin = User.objects.get(email=admin_email)
    print(f"ℹ️ Usuario admin ya existe: {admin_email}")

# Crear categorías
categories_data = [
    {"name": "Tecnología", "description": "Posts sobre tecnología y programación"},
    {"name": "Ciencia", "description": "Descubrimientos y noticias científicas"},
    {"name": "Negocios", "description": "Mundo empresarial y startups"},
    {"name": "Deportes", "description": "Noticias deportivas"},
    {"name": "Entretenimiento", "description": "Cultura, cine y música"},
]

for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data["name"],
        defaults={"description": cat_data["description"]}
    )
    if created:
        print(f"✅ Categoría creada: {category.name}")

# Crear tags
tags_data = ["Python", "Django", "PostgreSQL", "Web Development", "AI", 
             "Machine Learning", "Docker", "Cloud", "Tutorial", "Guía"]

for tag_name in tags_data:
    tag, created = Tag.objects.get_or_create(name=tag_name)
    if created:
        print(f"✅ Tag creado: {tag.name}")

# Crear posts de ejemplo
posts_data = [
    {
        "title": "Introducción a Django y PostgreSQL",
        "excerpt": "Aprende a crear aplicaciones web modernas con Django y PostgreSQL",
        "content": """<h2>¿Qué es Django?</h2>
        <p>Django es un framework web de alto nivel escrito en Python que fomenta el desarrollo rápido y el diseño limpio y pragmático.</p>
        <h2>¿Por qué PostgreSQL?</h2>
        <p>PostgreSQL es una base de datos relacional robusta, con características avanzadas como búsqueda de texto completo, tipos de datos JSON, y extensiones como pg_trgm para búsquedas inteligentes.</p>
        <h2>Ventajas de esta combinación</h2>
        <ul>
        <li>Desarrollo rápido y eficiente</li>
        <li>Seguridad robusta</li>
        <li>Escalabilidad</li>
        <li>Gran comunidad y documentación</li>
        </ul>""",
        "category": "Tecnología",
        "tags": ["Python", "Django", "PostgreSQL", "Tutorial"],
        "is_featured": True,
    },
    {
        "title": "Cómo implementar búsqueda de texto completo en Django",
        "excerpt": "Guía paso a paso para implementar búsqueda avanzada usando PostgreSQL",
        "content": """<h2>Búsqueda de texto completo</h2>
        <p>PostgreSQL ofrece capacidades poderosas de búsqueda de texto completo. En este tutorial aprenderás a implementar búsqueda inteligente usando la extensión pg_trgm.</p>
        <h2>Trigram Similarity</h2>
        <p>La similitud de trigramas permite encontrar coincidencias aproximadas, muy útil para búsquedas con errores tipográficos.</p>
        <pre><code>from django.contrib.postgres.search import TrigramSimilarity
        
posts = Post.objects.annotate(
    similarity=TrigramSimilarity('title', query)
).filter(similarity__gt=0.1).order_by('-similarity')</code></pre>""",
        "category": "Tecnología",
        "tags": ["Django", "PostgreSQL", "Tutorial", "Web Development"],
        "is_featured": True,
    },
    {
        "title": "Docker para desarrolladores Python",
        "excerpt": "Containeriza tus aplicaciones Django con Docker",
        "content": """<h2>¿Por qué Docker?</h2>
        <p>Docker te permite empaquetar tu aplicación con todas sus dependencias en un contenedor portable.</p>
        <h2>Dockerfile básico</h2>
        <pre><code>FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application"]</code></pre>
        <h2>Docker Compose</h2>
        <p>Usa docker-compose.yml para orquestar múltiples servicios como tu aplicación web y base de datos.</p>""",
        "category": "Tecnología",
        "tags": ["Docker", "Python", "Django"],
        "is_featured": False,
    },
    {
        "title": "Desplegar Django en la nube",
        "excerpt": "Opciones para hospedar tu aplicación Django en producción",
        "content": """<h2>Opciones de despliegue</h2>
        <p>Existen múltiples opciones para desplegar aplicaciones Django:</p>
        <ul>
        <li>Heroku - Simple y rápido</li>
        <li>AWS - Flexible y escalable</li>
        <li>DigitalOcean - Económico y confiable</li>
        <li>Google Cloud - Potente infraestructura</li>
        </ul>
        <h2>Consideraciones importantes</h2>
        <p>No olvides configurar variables de entorno, usar DEBUG=False en producción, y configurar archivos estáticos correctamente.</p>""",
        "category": "Tecnología",
        "tags": ["Django", "Cloud", "Web Development"],
        "is_featured": False,
    },
]

for post_data in posts_data:
    # Verificar si el post ya existe
    if not Post.objects.filter(title=post_data["title"]).exists():
        category = Category.objects.get(name=post_data["category"])
        
        post = Post.objects.create(
            title=post_data["title"],
            excerpt=post_data["excerpt"],
            content=post_data["content"],
            category=category,
            author=admin,
            status="published",
            is_featured=post_data["is_featured"],
            published_at=timezone.now()
        )
        
        # Agregar tags
        for tag_name in post_data["tags"]:
            tag = Tag.objects.get(name=tag_name)
            post.tags.add(tag)
        
        print(f"✅ Post creado: {post.title}")
    else:
        print(f"ℹ️ Post ya existe: {post_data['title']}")

print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
print("\n📝 Puedes acceder al admin en: http://localhost:8000/admin/")
print(f"   Email: {admin_email}")
print("   Password: admin123")
