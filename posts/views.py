from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required # Needs 'LOGIN_URL' param in settings.py
from django.core.exceptions import ObjectDoesNotExist
from .models import User, Post
from .forms import SignUpForm, LogInForm, PostForm, EditProfileForm
from django.contrib import messages

# Create your views here.

# Creating a decorator so that views that we should not be logged in for cannot be accessed when logged in
def login_prohibited(view_function):
    # Taking a view function and redirecting to feed if logged in, else execute it as normal
    def modified_view_function(request): # Wrapper function
        if request.user.is_authenticated:
            return redirect('feed')
        else:
            return view_function(request)
    return modified_view_function

# Function is returned by this function, can store in variable, execute it later etc. '@' decorator syntax runs the returned wrapper function



def home(request):
    user_count = User.objects.count()
    post_count = Post.objects.count()
    return render(request, 'home.html', {'user_count': user_count, 'post_count': post_count})

@login_prohibited
def sign_up(request):
    if request.method == 'POST':
        # Create sign up form with the data sent in the POST request
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Bound and correct format for values
            user = form.save()
            login(request, user)
            return redirect('feed')
    else:
        form = SignUpForm()

    # This line is executed in the case of a GET request, pass empty form to template
    return render(request, 'sign_up.html', {'form': form})

@login_prohibited
def log_in(request):
    if request.method == 'POST':
        form = LogInForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('feed')
        
        # If we got here, then details not found in database
        messages.add_message(request, messages.ERROR, "Invalid username or password. Please try again.")

    # For GET request, we do these
    form = LogInForm()
    return render(request, 'log_in.html', {'form': form})

def log_out(request):
    # Remove _auth_user_id from the session
    logout(request)
    return redirect('home')

@login_required
def feed(request):
    form = PostForm()
    posts = Post.objects.all().order_by('-posted_at') # 'order by' orders in ascending by default, '-' makes it descending
    return render(request, "feed.html", {'form': form, 'posts': posts})

@login_required
def new_post(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            current_user = request.user
            form = PostForm(request.POST, request.FILES) 
            # request.FILES is a dictionary-like object similar to request.POST
            # request.POST contains POST data, request.FILES contains file data we are sending
            if form.is_valid():
                title = form.cleaned_data.get('title')
                image = form.cleaned_data.get('image') # form.cleaned_data is a dictionary-like object as well
                body = form.cleaned_data.get('body')

                post = Post.objects.create(
                    author=current_user,
                    title=title,
                    image=image,
                    body=body
                )

                return redirect('feed')
            else:
                return render(request, 'feed.html', {'form': form}) # Form invalid so re-render the feed with form errors
        else:
            return redirect('log_in')
    else:
        return HttpResponseForbidden() # Got here means GET request


@login_required
def profile(request, username): # username taken from path in urls.py
    try:
        user = User.objects.get(username=username)
        posts = Post.objects.filter(author=user).order_by('-posted_at')
        following = request.user.is_following(user) # Check if logged in user is following target user, pass to template
        can_follow = (request.user != user) # Can't follow self
    except ObjectDoesNotExist:
        return redirect('feed')
    else:
        return render(request, 'profile.html', {'user': user, 'posts': posts, 'following': following, 'can_follow': can_follow}) # Dictionary passed during render is the context
    

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user) # Fill form with POST data and assign changes to current user
        if form.is_valid():
            form.save()
            return redirect('feed')
        else:
            return render(request, 'edit_profile.html', {'form': form})
    else: # GET request
        form = EditProfileForm(instance=request.user) # Fill in the form with data of current user
        return render(request, 'edit_profile.html', {'form': form})
    


@login_required
def follow_toggle(request, username):
    current_user = request.user # Current logged in user from request
    try:
        to_follow = User.objects.get(username=username)
        current_user.toggle_follow(to_follow)
    except ObjectDoesNotExist: # User get can throw this
        return redirect('feed')
    else:
        return redirect('profile', username=username) # If we end up following, redirect to same profile


