from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from yatube.settings import MAX_LENGHT_POSTS

from .models import Post, Group, User
from .forms import PostForm


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    page_number = request.GET.get('page')
    paginator = Paginator(posts, MAX_LENGHT_POSTS)

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = ('posts/group_list.html')
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    paginator = Paginator(posts, MAX_LENGHT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author')
    page_number = request.GET.get('page')
    paginator = Paginator(posts, MAX_LENGHT_POSTS)
    page_obj = paginator.get_page(page_number)
    count_posts = posts.count()

    context = {
        'username': author,
        'page_obj': page_obj,
        'count_posts': count_posts,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    title = 'Создание нового поста '
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(f"/profile/{post.author}/")
    else:
        form = PostForm()
    context = {
        'form': form,
        'title': title,
    }
    return render(request, 'posts/create_post.html', context)


def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = PostForm(request.POST or None, instance=post)
    template = "posts/create_post.html"
    if request.user == author:
        if request.method == "POST" and form.is_valid:
            post = form.save()
            return redirect("posts:post_detail", post_id)
        context = {
            "form": form,
            "is_edit": is_edit,
            "post": post,
        }
        return render(request, template, context)
    return redirect("posts:post_detail", post_id)
