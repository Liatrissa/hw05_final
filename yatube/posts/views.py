from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def paginator_group(request, post_list):
    paginator = Paginator(post_list, settings.POST_PAGES)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_group(request, post_list)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """View-функция для страницы сообщества"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    template = 'posts/group_list.html'
    page_obj = paginator_group(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """View-функция для страницы профиля"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    page_obj = paginator_group(request, post_list)
    following = request.user.is_authenticated
    if following:
        following = author.following.filter(user=request.user).exists()
    template = 'posts/profile.html'
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """View-функция для страницы с информацией о посте"""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """View-функция для страницы создания поста"""
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        create_post = form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', request.user)
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """View-функция для страницы редактирования поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    template = 'posts/create_post.html'
    context = {'form': form, 'post': post, 'is_edit': True}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """View-функция для страницы добавление комментария"""
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
    """View-функция для страницы подписания """
    posts = Post.objects.filter(
        author__following__user=request.user)
    page_obj = paginator_group(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user_follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    user_follower.delete()
    return redirect('posts:profile', username)
