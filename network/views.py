from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import CustomRegisterForm, RouteForm, UserForm, PostForm, ProfileEditForm, CommentForm
from .models import Post, Route, Profile, Comment, FriendRequest
from django.contrib.auth.models import User


@login_required
def notifications(request):

    friends = request.user.profile.friends.all()

    friend_posts = Post.objects.filter(user__in=friends).order_by('-created_at')

    return render(request, 'network/notifications.html', {'friend_posts': friend_posts})
@login_required
@require_POST
def add_route_comment(request):
    route_id = request.POST.get('route_id')
    content = request.POST.get('content')

    try:
        route = Route.objects.get(id=route_id)
    except Route.DoesNotExist:
        return JsonResponse({'error': 'Маршрут не знайдено.'}, status=404)

    comment = Comment.objects.create(
        route=route,
        user=request.user,
        content=content
    )

    return JsonResponse({
        'username': comment.user.username,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
    })
@require_POST
@login_required
def add_comment(request):
    post_id = request.POST.get('post_id')
    content = request.POST.get('content')

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Пост не знайдено.'}, status=404)

    comment = Comment.objects.create(
        post=post,
        user=request.user,
        content=content
    )

    return JsonResponse({
        'username': comment.user.username,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
    })
def home(request):
    posts = Post.objects.all().order_by('-created_at')

    if request.method == 'POST' and 'comment_post_id' in request.POST:
        post_id = request.POST.get('comment_post_id')
        post = Post.objects.get(id=post_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('home')

    comment_forms = {post.id: CommentForm() for post in posts}
    return render(request, 'network/home.html', {'posts': posts, 'comment_forms': comment_forms})
# Лайк посту
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user.is_authenticated:
        if request.user in post.likes.all():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
    return redirect('home')

@login_required(login_url='login')
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'network/create_post.html', {'form': form})

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user)

    total_likes = sum(post.likes.count() for post in posts)

    return render(request, 'network/profile.html', {
        'user': user,
        'posts': posts,
        'total_likes': total_likes,
    })



@login_required
def edit_profile(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            return redirect('profile', username=user.username)
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'network/edit_profile.html', {'form': form})
def routes(request):
    route_list = Route.objects.all()
    paginator = Paginator(route_list, 10)
    page_number = request.GET.get('page')
    routes_page = paginator.get_page(page_number)
    return render(request, 'network/routes.html', {'routes': routes_page})

def site_settings(request):
    return render(request, 'network/settings.html')

def route_detail(request, route_id):
    route = get_object_or_404(Route, id=route_id)

    if request.method == 'POST':
        content = request.POST.get('comment', '').strip()
        if content and request.user.is_authenticated:
            Comment.objects.create(
                route=route,
                user=request.user,
                content=content
            )
            return redirect('route_detail', route_id=route.id)

    return render(request, 'network/route_detail.html', {
        'route': route
    })
def search(request):
    query = request.GET.get('q', '')
    posts = Post.objects.filter(Q(caption__icontains=query) | Q(user__username__icontains=query))
    routes = Route.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'network/search.html', {'posts': posts, 'routes': routes, 'query': query})

def register_view(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomRegisterForm()
    return render(request, 'network/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'network/login.html', {'form': form})



@login_required
def find_friends(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = User.objects.filter(username__icontains=query).exclude(id=request.user.id)

    sent_requests = FriendRequest.objects.filter(from_user=request.user).values_list('to_user_id', flat=True)
    friends = request.user.profile.friends.all()

    return render(request, 'network/find_friends.html', {
        'results': results,
        'sent_requests': sent_requests,
        'friends': friends
    })

@login_required
def add_friend(request, user_id):
    if request.method == 'POST':
        to_user = get_object_or_404(User, id=user_id)
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('find_friends')

@login_required
def friends_list(request):
    received_requests = FriendRequest.objects.filter(to_user=request.user)
    friends = request.user.profile.friends.all()
    return render(request, 'network/friends_list.html', {
        'received_requests': received_requests,
        'friends': friends
    })

@login_required
def accept_friend(request, user_id):
    from_user = get_object_or_404(User, id=user_id)
    friend_request = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()

    if friend_request:
        request.user.profile.friends.add(from_user)
        from_user.profile.friends.add(request.user)
        friend_request.delete()

    return redirect('friends')

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    request.user.profile.friends.remove(friend)
    friend.profile.friends.remove(request.user)
    messages.success(request, f"{friend.username} видалений з друзів.")
    return redirect('friends')

@login_required
def reject_friend(request, user_id):
    from_user = get_object_or_404(User, id=user_id)
    friend_request = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()
    if friend_request:
        friend_request.delete()
        messages.info(request, f"Запит від {from_user.username} відхилено.")
    return redirect('friends')

@login_required
def create_route(request):
    if request.method == 'POST':
        form = RouteForm(request.POST, request.FILES)
        if form.is_valid():
            route = form.save(commit=False)
            route.user = request.user
            route.save()
            return redirect('routes')
    else:
        form = RouteForm()
    return render(request, 'network/create_route.html', {'form': form})

@login_required
def routes(request):
    all_routes = Route.objects.select_related('user').order_by('-id')
    return render(request, 'network/routes.html', {'routes': all_routes})
