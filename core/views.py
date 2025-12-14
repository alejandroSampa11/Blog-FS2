from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.postgres.search import TrigramSimilarity
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View, FormView
from django.utils import timezone
from django.utils.text import slugify
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Post, Category, Tag, Comment, User, Image
from .forms import CommentForm, UserRegistrationForm, UserLoginForm, PostForm, CategoryForm, TagForm


class HomeView(TemplateView):
    """Página principal con posts destacados y recientes"""
    template_name = "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = Post.objects.filter(status='published', is_featured=True).select_related('author', 'category', 'featured_image')[:3]
        context['recent_posts'] = Post.objects.filter(status='published').select_related('author', 'category', 'featured_image')[:6]
        context['categories'] = Category.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0)[:5]
        context['popular_tags'] = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10]
        return context


class PostListView(ListView):
    """Lista de posts con paginación"""
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related('author', 'category', 'featured_image').prefetch_related('tags')
        return queryset.order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['popular_tags'] = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10]
        return context


class PostDetailView(DetailView):
    """Detalle de un post con comentarios"""
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Post.objects.filter(status='published').select_related('author', 'category', 'featured_image').prefetch_related('tags')
    
    def get_object(self):
        post = super().get_object()
        # Incrementar contador de vistas
        post.views_count += 1
        post.save(update_fields=['views_count'])
        return post
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['comments'] = Comment.objects.filter(post=post, is_approved=True, parent=None).select_related('user').prefetch_related('replies')
        context['comment_form'] = CommentForm()
        context['related_posts'] = Post.objects.filter(
            status='published',
            category=post.category
        ).exclude(id=post.id)[:3]
        return context


class PostByCategoryView(ListView):
    """Posts filtrados por categoría"""
    template_name = 'post_by_category.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.objects.filter(status='published', category=self.category).select_related('author', 'category', 'featured_image')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostByTagView(ListView):
    """Posts filtrados por tag"""
    template_name = 'post_by_tag.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Post.objects.filter(status='published', tags=self.tag).select_related('author', 'category', 'featured_image')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context


class SearchPostsView(ListView):
    """Búsqueda de posts usando PostgreSQL trigram similarity"""
    template_name = 'search_results.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        self.query = query
        
        if query:
            # Búsqueda usando trigram similarity
            posts = Post.objects.filter(
                status='published'
            ).annotate(
                similarity=TrigramSimilarity('title', query) + TrigramSimilarity('content', query)
            ).filter(similarity__gt=0.1).order_by('-similarity')
            
            # Fallback a búsqueda simple si no hay resultados
            if not posts.exists():
                posts = Post.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query) | Q(excerpt__icontains=query),
                    status='published'
                ).distinct()
            
            return posts
        return Post.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.query
        return context


class AddCommentView(LoginRequiredMixin, View):
    """Agregar comentario a un post"""
    
    def post(self, request, post_slug):
        post = get_object_or_404(Post, slug=post_slug, status='published')
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.is_approved = True  # Auto-aprobar comentarios
            
            # Si es una respuesta a otro comentario
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent_id = parent_id
            
            comment.save()
            messages.success(request, '¡Comentario agregado exitosamente!')
        
        return redirect('post_detail', slug=post_slug)


class UserRegisterView(FormView):
    """Registro de nuevos usuarios"""
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
        return super().form_valid(form)


class UserLoginView(FormView):
    """Login de usuarios"""
    template_name = 'registration/login.html'
    form_class = UserLoginForm
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'¡Bienvenido {user.username}!')
            next_url = self.request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(self.request, 'Email o contraseña incorrectos.')
            return self.form_invalid(form)


class UserLogoutView(View):
    """Logout de usuarios"""
    
    def get(self, request):
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('home')


# Mixin para verificar permisos de administrador
class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin para verificar que el usuario es administrador"""
    
    def test_func(self):
        return self.request.user.is_staff and self.request.user.role == 'admin'
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')


class AdminCreatePostView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Vista para que los administradores creen posts"""
    model = Post
    form_class = PostForm
    template_name = 'admin/create_post.html'
    success_url = reverse_lazy('admin_post_list')
    
    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        
        # Procesar la imagen subida
        uploaded_image = self.request.FILES.get('upload_image')
        if uploaded_image:
            # Crear nuevo objeto Image
            image = Image(
                uploaded_by=self.request.user,
                filename=uploaded_image.name,
                file_path=uploaded_image,
                file_size=uploaded_image.size,
                mime_type=uploaded_image.content_type
            )
            
            # Obtener nombre personalizado o usar el nombre del archivo
            image_name = form.cleaned_data.get('image_name')
            if image_name:
                image.original_filename = image_name
            else:
                image.original_filename = uploaded_image.name
            
            image.save()
            
            # Obtener dimensiones de la imagen
            try:
                from PIL import Image as PILImage
                with PILImage.open(image.file_path.path) as img:
                    image.width, image.height = img.size
                    image.save(update_fields=['width', 'height'])
            except Exception as e:
                print(f"Error obteniendo dimensiones: {e}")
            
            # Asignar la imagen al post
            post.featured_image = image
        
        # Generar slug único
        base_slug = slugify(post.title)
        slug = base_slug
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        post.slug = slug
        
        # Si el estado es 'published', establecer la fecha de publicación
        if post.status == 'published' and not post.published_at:
            post.published_at = timezone.now()
        
        post.save()
        
        # Guardar las tags (relación many-to-many)
        form.save_m2m()
        
        messages.success(self.request, f'Post "{post.title}" creado exitosamente.')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_form'] = CategoryForm()
        context['tag_form'] = TagForm()
        context['title'] = 'Crear Nuevo Post'
        return context


class AdminPostListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Vista para listar todos los posts (para administradores)"""
    model = Post
    template_name = 'admin/post_list.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def get_queryset(self):
        posts = Post.objects.all().select_related('author', 'category', 'featured_image').prefetch_related('tags')
        
        # Filtro por búsqueda de texto
        search_query = self.request.GET.get('q')
        if search_query:
            posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
        
        # Filtro por estado
        status_filter = self.request.GET.get('status')
        if status_filter:
            posts = posts.filter(status=status_filter)
        
        # Filtro por destacado
        featured_filter = self.request.GET.get('featured')
        if featured_filter == '1':
            posts = posts.filter(is_featured=True)
        elif featured_filter == '0':
            posts = posts.filter(is_featured=False)
        
        # Filtro por categoría
        category_filter = self.request.GET.get('category')
        if category_filter:
            posts = posts.filter(category_id=category_filter)
        
        # Filtro por autor
        author_filter = self.request.GET.get('author')
        if author_filter:
            posts = posts.filter(author_id=author_filter)
        
        # Filtro por tag
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            posts = posts.filter(tags__id=tag_filter)
        
        # Filtro por rango de fecha
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            posts = posts.filter(created_at__gte=date_from)
        if date_to:
            posts = posts.filter(created_at__lte=date_to)
        
        # Filtro por mes/año
        month_filter = self.request.GET.get('month')
        year_filter = self.request.GET.get('year')
        if month_filter and year_filter:
            posts = posts.filter(created_at__year=year_filter, created_at__month=month_filter)
        elif year_filter:
            posts = posts.filter(created_at__year=year_filter)
        
        return posts.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Gestión de Posts'
        context['categories'] = Category.objects.all().order_by('name')
        context['authors'] = User.objects.filter(role='admin').order_by('username')
        context['tags'] = Tag.objects.all().order_by('name')
        
        # Obtener años únicos de posts para el filtro
        from django.db.models.functions import ExtractYear
        context['years'] = Post.objects.annotate(year=ExtractYear('created_at')).values_list('year', flat=True).distinct().order_by('-year')
        
        # Pasar los filtros actuales al contexto
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'author': self.request.GET.get('author', ''),
            'tag': self.request.GET.get('tag', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'month': self.request.GET.get('month', ''),
            'year': self.request.GET.get('year', ''),
        }
        
        return context


class AdminCreateCategoryView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Vista AJAX para crear categoría"""
    
    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    def get(self, request):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class AdminCreateTagView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Vista AJAX para crear tag"""
    
    def post(self, request):
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            return JsonResponse({
                'success': True,
                'tag': {
                    'id': tag.id,
                    'name': tag.name
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    def get(self, request):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


class AdminEditPostView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Vista para editar un post existente"""
    model = Post
    form_class = PostForm
    template_name = 'admin/edit_post.html'
    success_url = reverse_lazy('admin_post_list')
    slug_field = 'slug'
    
    def form_valid(self, form):
        post = form.save(commit=False)
        
        # Procesar la imagen subida
        uploaded_image = self.request.FILES.get('upload_image')
        if uploaded_image:
            # Crear nuevo objeto Image
            image = Image(
                uploaded_by=self.request.user,
                filename=uploaded_image.name,
                file_path=uploaded_image,
                file_size=uploaded_image.size,
                mime_type=uploaded_image.content_type
            )
            
            # Obtener nombre personalizado o usar el nombre del archivo
            image_name = form.cleaned_data.get('image_name')
            if image_name:
                image.original_filename = image_name
            else:
                image.original_filename = uploaded_image.name
            
            image.save()
            
            # Obtener dimensiones de la imagen
            try:
                from PIL import Image as PILImage
                with PILImage.open(image.file_path.path) as img:
                    image.width, image.height = img.size
                    image.save(update_fields=['width', 'height'])
            except Exception as e:
                print(f"Error obteniendo dimensiones: {e}")
            
            # Asignar la imagen al post
            post.featured_image = image
        
        # Si el estado es 'published' y no tiene fecha de publicación, establecerla
        if post.status == 'published' and not post.published_at:
            post.published_at = timezone.now()
        
        post.save()
        
        # Guardar las tags (relación many-to-many)
        form.save_m2m()
        
        messages.success(self.request, f'Post "{post.title}" actualizado exitosamente.')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_form'] = CategoryForm()
        context['tag_form'] = TagForm()
        context['title'] = f'Editar Post: {self.object.title}'
        return context


class AdminDeletePostView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Vista para eliminar un post"""
    
    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        post_title = post.title
        post.delete()
        return JsonResponse({'success': True, 'message': f'Post "{post_title}" eliminado exitosamente.'})
    
    def get(self, request, slug):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ========== VISTAS DE ADMINISTRACIÓN DE CATEGORÍAS ==========

class AdminCategoryListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Lista de categorías con opciones de administración"""
    model = Category
    template_name = 'admin/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Category.objects.annotate(post_count=Count('posts')).order_by('-post_count', 'name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['total_categories'] = Category.objects.count()
        return context


class AdminCategoryCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Crear nueva categoría"""
    model = Category
    form_class = CategoryForm
    template_name = 'admin/category_form.html'
    success_url = reverse_lazy('admin_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" creada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Categoría'
        context['button_text'] = 'Crear Categoría'
        return context


class AdminCategoryEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Editar categoría existente"""
    model = Category
    form_class = CategoryForm
    template_name = 'admin/category_form.html'
    success_url = reverse_lazy('admin_category_list')
    pk_url_kwarg = 'id'
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Categoría: {self.object.name}'
        context['button_text'] = 'Actualizar Categoría'
        return context


class AdminCategoryDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Eliminar categoría"""
    model = Category
    success_url = reverse_lazy('admin_category_list')
    pk_url_kwarg = 'id'
    
    def post(self, request, *args, **kwargs):
        category = self.get_object()
        post_count = category.posts.count()
        
        if post_count > 0:
            return JsonResponse({
                'success': False, 
                'error': f'No se puede eliminar. Hay {post_count} post(s) asociado(s) a esta categoría.'
            })
        
        category_name = category.name
        category.delete()
        return JsonResponse({'success': True, 'message': f'Categoría "{category_name}" eliminada exitosamente.'})
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ========== VISTAS DE ADMINISTRACIÓN DE TAGS ==========

class AdminTagListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Lista de tags con opciones de administración"""
    model = Tag
    template_name = 'admin/tag_list.html'
    context_object_name = 'tags'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count', 'name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['total_tags'] = Tag.objects.count()
        return context


class AdminTagCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Crear nuevo tag"""
    model = Tag
    form_class = TagForm
    template_name = 'admin/tag_form.html'
    success_url = reverse_lazy('admin_tag_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Tag "{form.instance.name}" creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Tag'
        context['button_text'] = 'Crear Tag'
        return context


class AdminTagEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Editar tag existente"""
    model = Tag
    form_class = TagForm
    template_name = 'admin/tag_form.html'
    success_url = reverse_lazy('admin_tag_list')
    pk_url_kwarg = 'id'
    
    def form_valid(self, form):
        messages.success(self.request, f'Tag "{form.instance.name}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Tag: {self.object.name}'
        context['button_text'] = 'Actualizar Tag'
        return context


class AdminTagDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Eliminar tag"""
    model = Tag
    success_url = reverse_lazy('admin_tag_list')
    pk_url_kwarg = 'id'
    
    def post(self, request, *args, **kwargs):
        tag = self.get_object()
        post_count = tag.posts.count()
        
        if post_count > 0:
            return JsonResponse({
                'success': False, 
                'error': f'No se puede eliminar. Hay {post_count} post(s) asociado(s) a este tag.'
            })
        
        tag_name = tag.name
        tag.delete()
        return JsonResponse({'success': True, 'message': f'Tag "{tag_name}" eliminado exitosamente.'})
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
