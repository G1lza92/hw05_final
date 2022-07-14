from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_page_context(queryset, request):
    paginator = Paginator(queryset, settings.PAGIN)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    page_obj = get_page_context(Post.objects.select_related('group').all(),
                                request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_page_context(posts, request)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = get_page_context(posts, request)
    following = False
    if request.user != author:
        Follow.objects.filter(user__id=request.user.id, author=author).exists()
        following = True
    context = {
        'page_obj': page_obj,
        'posts': posts,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {'form': form}
    if request.method != 'POST':
        return render(request, 'posts/create_post.html', context)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method != 'POST':
        return render(request, 'posts/create_post.html', context)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


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
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_context(posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = get_page_context(posts, request)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': True
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    Follow.objects.filter(user=request.user, author=author).delete()
    page_obj = get_page_context(posts, request)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': False
    }
    return render(request, 'posts/profile.html', context)
