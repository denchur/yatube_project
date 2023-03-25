from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import paginate

User = get_user_model()


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': paginate(request, posts),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': paginate(request, posts),
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author')
    following = request.user.is_authenticated and author.following.filter(
        user=request.user).exists()
    context = {
        'username': author,
        'page_obj': paginate(request, posts),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            username = post.author.username
            return redirect("posts:profile", username)
    if request.method != 'POST':
        form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    template = "posts/create_post.html"
    if request.user == author:
        form = PostForm(
            request.POST or None,
            instance=post,
            files=request.FILES or None,
        )
        if request.method == "POST" and form.is_valid:
            post = form.save()
            return redirect("posts:post_detail", post_id)
        context = {
            "form": form,
            "is_edit": True,
            "post": post,
        }
        return render(request, template, context)
    if request.user != author:
        return redirect("posts:post_detail", post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user
    )
    context = {
        'page_obj': paginate(request, posts),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = request.user
    follow = Follow.objects.filter(user=follower, author=author)
    if not follow and follower != author:
        Follow.objects.create(user=follower, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = get_object_or_404(User, username=request.user)
    Follow.objects.filter(user=follower, author=author).delete()
    return redirect('posts:profile', username)
