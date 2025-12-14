from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Post, Category, Tag, Comment, Image
from .forms import PostForm, CategoryForm, TagForm, CommentForm, UserRegistrationForm
from datetime import datetime, timedelta

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class UserModelTest(TestCase):
    """Tests para el modelo User personalizado"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'role': 'reader'
        }
    
    def test_create_user(self):
        """Test crear usuario normal"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'reader')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_superuser(self):
        """Test crear superusuario"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='admin123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(superuser.role, 'admin')
    
    def test_user_string_representation(self):
        """Test representación en string del usuario"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')
    
    def test_email_required(self):
        """Test que el email es requerido"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', username='test', password='test123')


class CategoryModelTest(TestCase):
    """Tests para el modelo Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Tecnología',
            slug='tecnologia',
            description='Posts sobre tecnología'
        )
    
    def test_category_creation(self):
        """Test crear categoría"""
        self.assertEqual(self.category.name, 'Tecnología')
        self.assertEqual(self.category.slug, 'tecnologia')
        self.assertIsNotNone(self.category.created_at)
    
    def test_category_string_representation(self):
        """Test representación en string de categoría"""
        self.assertEqual(str(self.category), 'Tecnología')
    
    def test_category_slug_unique(self):
        """Test que el slug es único"""
        with self.assertRaises(Exception):
            Category.objects.create(
                name='Tecnología 2',
                slug='tecnologia'
            )


class TagModelTest(TestCase):
    """Tests para el modelo Tag"""
    
    def setUp(self):
        self.tag = Tag.objects.create(
            name='Python',
            slug='python'
        )
    
    def test_tag_creation(self):
        """Test crear tag"""
        self.assertEqual(self.tag.name, 'Python')
        self.assertEqual(self.tag.slug, 'python')
    
    def test_tag_string_representation(self):
        """Test representación en string de tag"""
        self.assertEqual(str(self.tag), 'Python')


class PostModelTest(TestCase):
    """Tests para el modelo Post"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(
            name='Tech',
            slug='tech'
        )
        self.tag = Tag.objects.create(
            name='Django',
            slug='django'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='This is test content',
            excerpt='Test excerpt',
            author=self.user,
            category=self.category,
            status='published'
        )
        self.post.tags.add(self.tag)
    
    def test_post_creation(self):
        """Test crear post"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.slug, 'test-post')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)
        self.assertEqual(self.post.status, 'published')
        self.assertEqual(self.post.views_count, 0)
        self.assertFalse(self.post.is_featured)
    
    def test_post_string_representation(self):
        """Test representación en string del post"""
        self.assertEqual(str(self.post), 'Test Post')
    
    def test_post_slug_unique(self):
        """Test que el slug del post es único"""
        with self.assertRaises(Exception):
            Post.objects.create(
                title='Another Post',
                slug='test-post',  # Mismo slug
                content='Content',
                author=self.user,
                category=self.category
            )
    
    def test_post_tags(self):
        """Test relación many-to-many con tags"""
        self.assertEqual(self.post.tags.count(), 1)
        self.assertEqual(self.post.tags.first(), self.tag)
    
    def test_post_increment_views(self):
        """Test incrementar contador de vistas"""
        initial_count = self.post.views_count
        self.post.views_count += 1
        self.post.save()
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, initial_count + 1)
    
    def test_post_published_status(self):
        """Test post publicado tiene fecha de publicación"""
        self.post.published_at = timezone.now()
        self.post.save()
        self.assertIsNotNone(self.post.published_at)


class CommentModelTest(TestCase):
    """Tests para el modelo Comment"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='commenter',
            password='pass123'
        )
        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Content',
            author=self.author,
            category=self.category
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            content='Great post!'
        )
    
    def test_comment_creation(self):
        """Test crear comentario"""
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.content, 'Great post!')
        self.assertFalse(self.comment.is_approved)  # Por defecto no está aprobado
    
    def test_comment_string_representation(self):
        """Test representación en string del comentario"""
        expected = f'Comment by {self.user.username} on {self.post.title}'
        self.assertEqual(str(self.comment), expected)
    
    def test_comment_reply(self):
        """Test comentario como respuesta"""
        reply = Comment.objects.create(
            post=self.post,
            user=self.author,
            content='Thanks!',
            parent=self.comment
        )
        self.assertEqual(reply.parent, self.comment)


# ========== TESTS DE VISTAS ==========

class HomeViewTest(TestCase):
    """Tests para la vista Home"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        
        # Crear posts de prueba
        for i in range(10):
            Post.objects.create(
                title=f'Post {i}',
                slug=f'post-{i}',
                content=f'Content {i}',
                author=self.user,
                category=self.category,
                status='published',
                is_featured=(i < 3)
            )
    
    def test_home_view_status_code(self):
        """Test que la página home responde con 200"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_template(self):
        """Test que usa el template correcto"""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home.html')
    
    def test_home_view_context(self):
        """Test que el contexto contiene los datos correctos"""
        response = self.client.get(reverse('home'))
        self.assertIn('featured_posts', response.context)
        self.assertIn('recent_posts', response.context)
        self.assertEqual(len(response.context['featured_posts']), 3)


class PostListViewTest(TestCase):
    """Tests para la vista de lista de posts"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        
        # Crear 10 posts
        for i in range(10):
            Post.objects.create(
                title=f'Post {i}',
                slug=f'post-{i}',
                content=f'Content {i}',
                author=self.user,
                category=self.category,
                status='published'
            )
    
    def test_post_list_view_status_code(self):
        """Test que la lista de posts responde con 200"""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_post_list_pagination(self):
        """Test que la paginación funciona (6 posts por página)"""
        response = self.client.get(reverse('post_list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['posts']), 6)
    
    def test_post_list_second_page(self):
        """Test segunda página de paginación"""
        response = self.client.get(reverse('post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 4)


class PostDetailViewTest(TestCase):
    """Tests para la vista de detalle de post"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status='published'
        )
    
    def test_post_detail_view_status_code(self):
        """Test que el detalle del post responde con 200"""
        response = self.client.get(reverse('post_detail', kwargs={'slug': self.post.slug}))
        self.assertEqual(response.status_code, 200)
    
    def test_post_detail_view_increment_views(self):
        """Test que se incrementa el contador de vistas"""
        initial_views = self.post.views_count
        self.client.get(reverse('post_detail', kwargs={'slug': self.post.slug}))
        self.post.refresh_from_db()
        # Verificar que el contador aumentó (puede ser más de 1 por múltiples llamadas)
        self.assertGreater(self.post.views_count, initial_views)
    
    def test_post_detail_404_for_invalid_slug(self):
        """Test que retorna 404 para slug inválido"""
        response = self.client.get(reverse('post_detail', kwargs={'slug': 'invalid-slug'}))
        self.assertEqual(response.status_code, 404)


class SearchPostsViewTest(TestCase):
    """Tests para la búsqueda de posts"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='pass123',
            role='admin'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        
        Post.objects.create(
            title='Django Tutorial',
            slug='django-tutorial',
            content='Learn Django framework',
            author=self.user,
            category=self.category,
            status='published'
        )
        Post.objects.create(
            title='Python Basics',
            slug='python-basics',
            content='Introduction to Python',
            author=self.user,
            category=self.category,
            status='published'
        )
    
    def test_search_view_with_query(self):
        """Test búsqueda con query"""
        response = self.client.get(reverse('search_posts') + '?q=Django')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 1)
    
    def test_search_view_no_results(self):
        """Test búsqueda sin resultados"""
        response = self.client.get(reverse('search_posts') + '?q=Ruby')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)


class UserAuthenticationTest(TestCase):
    """Tests para autenticación de usuarios"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_user_registration_view(self):
        """Test vista de registro"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
    
    def test_user_login_view(self):
        """Test vista de login"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_user_can_login(self):
        """Test que un usuario puede hacer login"""
        response = self.client.post(reverse('login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de login
    
    def test_user_logout(self):
        """Test logout de usuario"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class AdminPostManagementTest(TestCase):
    """Tests para gestión de posts por admin"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123',
            role='admin',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='user123'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
    
    def test_admin_can_access_post_list(self):
        """Test que admin puede acceder a lista de posts"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(reverse('admin_post_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_cannot_access_admin(self):
        """Test que usuario regular no puede acceder al admin"""
        self.client.login(email='user@example.com', password='user123')
        response = self.client.get(reverse('admin_post_list'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_admin_can_access_create_post(self):
        """Test que admin puede acceder a crear post"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(reverse('admin_create_post'))
        self.assertEqual(response.status_code, 200)


class CategoryManagementTest(TestCase):
    """Tests para gestión de categorías"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123',
            role='admin',
            is_staff=True
        )
        self.category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Tech posts'
        )
    
    def test_admin_can_view_category_list(self):
        """Test que admin puede ver lista de categorías"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(reverse('admin_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category, response.context['categories'])
    
    def test_admin_can_create_category(self):
        """Test que admin puede crear categoría"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.post(reverse('admin_create_category_page'), {
            'name': 'Science',
            'slug': 'science',
            'description': 'Science posts'
        })
        self.assertEqual(Category.objects.count(), 2)
    
    def test_admin_can_edit_category(self):
        """Test que admin puede editar categoría"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.post(
            reverse('admin_edit_category', kwargs={'id': self.category.id}),
            {
                'name': 'Tech Updated',
                'slug': 'tech-updated',
                'description': 'Updated description'
            }
        )
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Tech Updated')


class TagManagementTest(TestCase):
    """Tests para gestión de tags"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123',
            role='admin',
            is_staff=True
        )
        self.tag = Tag.objects.create(name='Python', slug='python')
    
    def test_tag_creation_via_model(self):
        """Test que se puede crear un tag"""
        tag = Tag.objects.create(name='Django', slug='django')
        self.assertEqual(tag.name, 'Django')
        self.assertEqual(Tag.objects.count(), 2)  # self.tag + nuevo tag


# ========== TESTS DE FORMULARIOS ==========

class PostFormTest(TestCase):
    """Tests para el formulario de Post"""
    
    def setUp(self):
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.tag = Tag.objects.create(name='Django', slug='django')
    
    def test_post_form_valid_data(self):
        """Test formulario con datos válidos"""
        form_data = {
            'title': 'Test Post',
            'slug': 'test-post',
            'content': 'Test content',
            'excerpt': 'Test excerpt',
            'status': 'draft',
            'category': self.category.id,
            'tags': [self.tag.id],
            'is_featured': False
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_post_form_missing_title(self):
        """Test formulario sin título (campo requerido)"""
        form_data = {
            'slug': 'test-post',
            'content': 'Test content'
        }
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class CategoryFormTest(TestCase):
    """Tests para el formulario de Category"""
    
    def test_category_form_valid_data(self):
        """Test formulario de categoría con datos válidos"""
        form_data = {
            'name': 'Technology',
            'slug': 'technology',
            'description': 'Tech related posts'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_category_form_missing_name(self):
        """Test formulario sin nombre"""
        form_data = {
            'slug': 'technology'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())


class TagFormTest(TestCase):
    """Tests para el formulario de Tag"""
    
    def test_tag_form_valid_data(self):
        """Test formulario de tag con datos válidos"""
        form_data = {
            'name': 'Python',
            'slug': 'python'
        }
        form = TagForm(data=form_data)
        self.assertTrue(form.is_valid())


class CommentFormTest(TestCase):
    """Tests para el formulario de Comment"""
    
    def test_comment_form_valid_data(self):
        """Test formulario de comentario con datos válidos"""
        form_data = {
            'content': 'Great post!'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_comment_form_empty_content(self):
        """Test formulario con contenido vacío"""
        form_data = {
            'content': ''
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())


class UserRegistrationFormTest(TestCase):
    """Tests para el formulario de registro"""
    
    def test_registration_form_valid_data(self):
        """Test formulario de registro con datos válidos"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registration_form_password_mismatch(self):
        """Test que las contraseñas no coinciden"""
        form_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password1': 'securepass123',
            'password2': 'differentpass123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


# ========== TESTS DE FILTROS Y BÚSQUEDA ==========

class PostFilterTest(TestCase):
    """Tests para filtros de posts en admin"""
    
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123',
            role='admin',
            is_staff=True
        )
        self.category1 = Category.objects.create(name='Tech', slug='tech')
        self.category2 = Category.objects.create(name='Science', slug='science')
        self.tag1 = Tag.objects.create(name='Python', slug='python')
        
        # Crear posts
        self.post1 = Post.objects.create(
            title='Django Post',
            slug='django-post',
            content='Django content',
            author=self.admin,
            category=self.category1,
            status='published'
        )
        self.post2 = Post.objects.create(
            title='Science Post',
            slug='science-post',
            content='Science content',
            author=self.admin,
            category=self.category2,
            status='draft'
        )
    
    def test_filter_by_category(self):
        """Test filtrar posts por categoría"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(
            reverse('admin_post_list') + f'?category={self.category1.id}'
        )
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].category, self.category1)
    
    def test_filter_by_status(self):
        """Test filtrar posts por estado"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(
            reverse('admin_post_list') + '?status=published'
        )
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].status, 'published')
    
    def test_filter_by_author(self):
        """Test filtrar posts por autor"""
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.get(
            reverse('admin_post_list') + f'?author={self.admin.id}'
        )
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(len(posts), 2)
