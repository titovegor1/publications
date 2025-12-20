from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Post, Category
from .forms import PostForm, CategoryForm
from .managers import get_published_posts


def index(request):
    posts = get_published_posts()
    posts = posts.select_related('author').prefetch_related('categories')
    posts = posts.order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post_queryset = Post.objects.filter(pk=pk)
    published_posts = get_published_posts(post_queryset)

    if not published_posts.exists():
        raise Http404("Post not found")

    post = published_posts.select_related('author').prefetch_related('categories', 'comments__user').first()

    return render(request, 'blog/post_detail.html', {'post': post})


def category_posts(request, pk):
    category = get_object_or_404(Category, pk=pk)
    posts = get_published_posts()
    posts = posts.filter(categories=category)
    posts = posts.select_related('author').prefetch_related('categories')
    posts = posts.order_by('-pub_date')

    return render(request, 'blog/category_posts.html', {
        'category': category,
        'posts': posts
    })


def user_posts(request, pk):
    user = get_object_or_404(User, pk=pk)
    posts = get_published_posts()
    posts = posts.filter(author=user)
    posts = posts.select_related('author').prefetch_related('categories')
    posts = posts.order_by('-pub_date')

    return render(request, 'blog/user_posts.html', {
        'author': user,
        'posts': posts
    })


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()

    return render(request, 'blog/post_form.html', {'form': form})


def search(request):
    query = request.GET.get('q', '')
    posts = get_published_posts()

    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(text__icontains=query)
        )

    posts = posts.select_related('author').prefetch_related('categories')
    posts = posts.order_by('-pub_date')

    return render(request, 'blog/search.html', {
        'posts': posts,
        'query': query
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.author = request.user
            category.save()
            return redirect('category_posts', pk=category.pk)
    else:
        form = CategoryForm()

    return render(request, 'blog/category_form.html', {'form': form})
