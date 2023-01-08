from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .models import Follow, Group, Post
from .forms import CommentForm, PostForm


def paginate_page(request, post):
    paginator = Paginator(post, settings.NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    """В переменную posts будет сохранена выборка из 10 объектов модели Post,
    отсортированных по полю pub_date по убыванию
    (от больших значений к меньшим).
    В словаре context отправляем информацию в шаблон."""
    post = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': paginate_page(request, post),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View-функция для страницы сообщества.
    Функция get_object_or_404 получает по заданным критериям объект
    из базы данных или возвращает сообщение об ошибке, если объект не найден.
    В нашем случае в переменную group будут переданы объекты модели Group,
    поле slug у которых соответствует значению slug в запросе."""
    group = get_object_or_404(Group, slug=slug)
    post = group.posts.select_related('author', 'group')
    context = {
        'group': group,
        'page_obj': paginate_page(request, post),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.posts.select_related('author', 'group')
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': paginate_page(request, post),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {
        'form': form,
        'is_edit': False,
    }
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginate_page(request, post),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
