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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name='home'),
    path("posts/", views.PostListView.as_view(), name='post_list'),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name='post_detail'),
    path("post/<slug:post_slug>/comment/", views.AddCommentView.as_view(), name='add_comment'),
    path("category/<slug:slug>/", views.PostByCategoryView.as_view(), name='post_by_category'),
    path("tag/<slug:slug>/", views.PostByTagView.as_view(), name='post_by_tag'),
    path("search/", views.SearchPostsView.as_view(), name='search_posts'),
    path("register/", views.UserRegisterView.as_view(), name='register'),
    path("login/", views.UserLoginView.as_view(), name='login'),
    path("logout/", views.UserLogoutView.as_view(), name='logout'),
    # Rutas de administración personalizadas - Posts
    path("admin-panel/posts/", views.AdminPostListView.as_view(), name='admin_post_list'),
    path("admin-panel/posts/create/", views.AdminCreatePostView.as_view(), name='admin_create_post'),
    path("admin-panel/posts/edit/<slug:slug>/", views.AdminEditPostView.as_view(), name='admin_edit_post'),
    path("admin-panel/posts/delete/<slug:slug>/", views.AdminDeletePostView.as_view(), name='admin_delete_post'),
    # Rutas de administración de Categorías
    path("admin-panel/categories/", views.AdminCategoryListView.as_view(), name='admin_category_list'),
    path("admin-panel/categories/create/", views.AdminCategoryCreateView.as_view(), name='admin_create_category_page'),
    path("admin-panel/categories/edit/<int:id>/", views.AdminCategoryEditView.as_view(), name='admin_edit_category'),
    path("admin-panel/categories/delete/<int:id>/", views.AdminCategoryDeleteView.as_view(), name='admin_delete_category'),
    path("admin-panel/category/create/", views.AdminCreateCategoryView.as_view(), name='admin_create_category'),  # AJAX
    # Rutas de administración de Tags
    path("admin-panel/tags/", views.AdminTagListView.as_view(), name='admin_tag_list'),
    path("admin-panel/tags/create/", views.AdminTagCreateView.as_view(), name='admin_create_tag_page'),
    path("admin-panel/tags/edit/<int:id>/", views.AdminTagEditView.as_view(), name='admin_edit_tag'),
    path("admin-panel/tags/delete/<int:id>/", views.AdminTagDeleteView.as_view(), name='admin_delete_tag'),
    path("admin-panel/tag/create/", views.AdminCreateTagView.as_view(), name='admin_create_tag'),  # AJAX
    path('ckeditor/', include('ckeditor_uploader.urls')),
    # Servir archivos media en producción
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
