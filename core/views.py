from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.postgres.search import TrigramSimilarity
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.utils.text import slugify
from django.http import JsonResponse
from .models import Post, Category, Tag, Comment, User, Image
from .forms import CommentForm, UserRegistrationForm, UserLoginForm, PostForm, CategoryForm, TagForm


def home(request):
    """Página principal con posts destacados y recientes"""
    featured_posts = Post.objects.filter(status='published', is_featured=True).select_related('author', 'category', 'featured_image')[:3]
    recent_posts = Post.objects.filter(status='published').select_related('author', 'category', 'featured_image')[:6]
    categories = Category.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0)[:5]
    popular_tags = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:10]
    
    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'categories': categories,
        'popular_tags': popular_tags,
    }
    return render(request, "home.html", context)


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


def post_by_category(request, slug):
    """Posts filtrados por categoría"""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(status='published', category=category).select_related('author', 'category', 'featured_image')
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'post_by_category.html', context)


def post_by_tag(request, slug):
    """Posts filtrados por tag"""
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(status='published', tags=tag).select_related('author', 'category', 'featured_image')
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'posts': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'post_by_tag.html', context)


def search_posts(request):
    """Búsqueda de posts usando PostgreSQL trigram similarity"""
    query = request.GET.get('q', '')
    posts = []
    
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
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'posts': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'search_results.html', context)


@login_required
def add_comment(request, post_slug):
    """Agregar comentario a un post"""
    post = get_object_or_404(Post, slug=post_slug, status='published')
    
    if request.method == 'POST':
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
    
    return redirect('post_detail', slug=post_slug)


def user_register(request):
    """Registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """Login de usuarios"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Email o contraseña incorrectos.')
    else:
        form = UserLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """Logout de usuarios"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')


@login_required
def admin_create_post(request):
    """Vista personalizada para que los administradores creen posts"""
    # Verificar que el usuario es administrador
    if not request.user.is_staff or request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            # Procesar la imagen subida
            uploaded_image = request.FILES.get('upload_image')
            if uploaded_image:
                # Crear nuevo objeto Image
                image = Image(
                    uploaded_by=request.user,
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
            
            messages.success(request, f'Post "{post.title}" creado exitosamente.')
            return redirect('admin_post_list')
    else:
        form = PostForm()
    
    context = {
        'form': form,
        'category_form': CategoryForm(),
        'tag_form': TagForm(),
        'title': 'Crear Nuevo Post'
    }
    return render(request, 'admin/create_post.html', context)


@login_required
def admin_post_list(request):
    """Vista para listar todos los posts (para administradores)"""
    # Verificar que el usuario es administrador
    if not request.user.is_staff or request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    posts = Post.objects.all().select_related('author', 'category', 'featured_image').prefetch_related('tags')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        posts = posts.filter(status=status_filter)
    
    search_query = request.GET.get('q')
    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    
    posts = posts.order_by('-created_at')
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'title': 'Gestión de Posts'
    }
    return render(request, 'admin/post_list.html', context)


@login_required
def admin_create_category(request):
    """Vista AJAX para crear categoría"""
    if not request.user.is_staff or request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
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
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def admin_create_tag(request):
    """Vista AJAX para crear tag"""
    if not request.user.is_staff or request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
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
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def admin_edit_post(request, slug):
    """Vista para editar un post existente"""
    # Verificar que el usuario es administrador
    if not request.user.is_staff or request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    post = get_object_or_404(Post, slug=slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            
            # Procesar la imagen subida
            uploaded_image = request.FILES.get('upload_image')
            if uploaded_image:
                # Crear nuevo objeto Image
                image = Image(
                    uploaded_by=request.user,
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
            
            messages.success(request, f'Post "{post.title}" actualizado exitosamente.')
            return redirect('admin_post_list')
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'category_form': CategoryForm(),
        'tag_form': TagForm(),
        'title': f'Editar Post: {post.title}'
    }
    return render(request, 'admin/edit_post.html', context)


@login_required
def admin_delete_post(request, slug):
    """Vista para eliminar un post"""
    # Verificar que el usuario es administrador
    if not request.user.is_staff or request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        post = get_object_or_404(Post, slug=slug)
        post_title = post.title
        post.delete()
        return JsonResponse({'success': True, 'message': f'Post "{post_title}" eliminado exitosamente.'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
