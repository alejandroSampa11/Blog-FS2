"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name='home'),
    path("posts/", views.PostListView.as_view(), name='post_list'),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name='post_detail'),
    path("post/<slug:post_slug>/comment/", views.add_comment, name='add_comment'),
    path("category/<slug:slug>/", views.post_by_category, name='post_by_category'),
    path("tag/<slug:slug>/", views.post_by_tag, name='post_by_tag'),
    path("search/", views.search_posts, name='search_posts'),
    path("register/", views.user_register, name='register'),
    path("login/", views.user_login, name='login'),
    path("logout/", views.user_logout, name='logout'),
    # Rutas de administración personalizadas
    path("admin-panel/posts/", views.admin_post_list, name='admin_post_list'),
    path("admin-panel/posts/create/", views.admin_create_post, name='admin_create_post'),
    path("admin-panel/posts/edit/<slug:slug>/", views.admin_edit_post, name='admin_edit_post'),
    path("admin-panel/posts/delete/<slug:slug>/", views.admin_delete_post, name='admin_delete_post'),
    path("admin-panel/category/create/", views.admin_create_category, name='admin_create_category'),
    path("admin-panel/tag/create/", views.admin_create_tag, name='admin_create_tag'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
