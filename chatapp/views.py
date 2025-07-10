from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Profile,Friend,Message,Blocked
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserUpdateForm 
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from axes.decorators import axes_dispatch

# Create your views here.

def welcome(request):
    return render(request,"chatapp/welcome.html")

def signup(request):
    if(request.method=='POST'):
        username=request.POST['username']
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']

        if(password==confirm_password):
            if(User.objects.filter(username=username).exists()):
                messages.info(request,"Usename taken")
                return redirect('signup')
            else:
                user=User.objects.create_user(username=username,password=password)
                # user.save()
                # login and redirect to settings page

                #create a profile object for the new user
                user_model=User.objects.get(username=username)
                new_profile=Profile.objects.create(user=user_model)
                # new_profile.save()
                messages.success(request, "User created successfully! Please log in.")
                return redirect('signup')

                # messages.success(request, "User created successfully! Please log in.")
                # return redirect('login')
        else:
            messages.info(request,"Passwords do not match.")
            return redirect('signup')
    # Your signup logic here
    else:
        return render(request, 'chatapp/signup.html')

@axes_dispatch  # Ensure that this view is protected by Axes
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)  # Use AuthenticationForm
        if form.is_valid():  # Validate the form
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)  # Pass request
            if user is not None:
                auth_login(request, user)  # Use the imported login function
                return redirect('index')  # Redirect to the index or home page
            else:
                messages.info(request, "Invalid credentials")  # Invalid login credentials
        else:
            messages.info(request, "Invalid form submission")  # Form errors
            return redirect('login')  # Redirect back to login on form error
    else:
        form = AuthenticationForm()  # Create an empty form for GET requests

    return render(request, "chatapp/login.html", {'form': form})  # Pass form to the template
    
def logout(request):
    auth_logout(request)
    return redirect('login')


@login_required(login_url='login')
def index(request):
    user_profile = request.user.profile

    # Get friends for the logged-in user, excluding blocked users
    friends = Friend.objects.filter(user=request.user) | Friend.objects.filter(friend=request.user)
    friend_profiles = {f.friend if f.user == request.user else f.user for f in friends}

    # Exclude users who have been blocked or have blocked the user
    blocked_users = Blocked.objects.filter(blocker=request.user).values_list('blocked', flat=True)
    blocked_by_others = Blocked.objects.filter(blocked=request.user).values_list('blocker', flat=True)
    friend_profiles = [friend for friend in friend_profiles if friend.id not in blocked_users and friend.id not in blocked_by_others]

    # Create a dictionary to hold the unread message counts for each friend
    unread_counts = {friend: Message.objects.filter(recipient=request.user, sender=friend, is_read=False).count() for friend in friend_profiles}

    # Identify friends with unread messages
    friends_with_unread_messages = [friend for friend, count in unread_counts.items() if count > 0]

    # Get all blocked friends
    blocked_friends = User.objects.filter(id__in=blocked_users)

    context = {
        "user": user_profile,
        "friends": friend_profiles,
        "unread_counts": unread_counts,
        "blocked_friends": blocked_friends,  # Pass blocked friends to the context
        "friends_with_unread_messages": friends_with_unread_messages,  # Pass friends with unread messages
    }
    return render(request, "chatapp/index.html", context)



@login_required(login_url='login')
def send_message(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    
    # Fetch existing messages between the users
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=friend)) | 
        (Q(sender=friend) & Q(recipient=request.user))
    ).order_by('timestamp')

    # Mark messages as read
    Message.objects.filter(recipient=request.user, sender=friend, is_read=False).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, recipient=friend, content=content)  # Save the message
            # Redirect to the same message page
            return redirect('send_message', friend_id=friend.id) 

    # Render the message page with the friend and messages
    return render(request, 'chatapp/message_page.html', {'friend': friend, 'messages': messages})


# @login_required
# def delete_message(request, message_id):
#     message = get_object_or_404(Message, id=message_id)
#     if request.user == message.sender:
#         message.delete()  # Delete the message
#     return redirect('send_message', friend_id=message.recipient.id)  # Redirect back to the message page



@login_required(login_url='login')
def settings(request):
    return render(request,"chatapp/settings.html")

@login_required(login_url='login')
def profile_settings(request):
    if request.method == 'POST':
        user = request.user
        name=request.POST.get('name')
        username = request.POST.get('username')
        profileimg = request.FILES.get('profileimg')  # Get the uploaded file if it exists

        # Update the username if it has changed
        if username and username != user.username:
            user.username = username
            user.save()
    
        # Update the name if it has been provided
        if name:  # This checks if name is not None or empty
            profile, created = Profile.objects.get_or_create(user=user)  # Get or create the profile
            profile.name = name  # Update the name field
            profile.save()  # Save the profile instance

        # Update the profile image if it has been uploaded
        if profileimg:
            profile, created = Profile.objects.get_or_create(user=user)  # Get or create the profile
            profile.profileimg = profileimg  # Assuming your Profile model has a field profileimg
            profile.save()  # Save the profile instance

        return redirect('index')  # Redirect to the index page after saving changes

    return render(request, 'chatapp/profile_settings.html')

@login_required(login_url='login')
def account_settings(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if the username has changed
        if username and username != request.user.username:
            # Check if the new username is already taken
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken. Please choose a different one.')
            else:
                request.user.username = username
                request.user.save()
                messages.success(request, 'Username updated successfully!')

        # Handle password change
        if password:
            if password == confirm_password:
                request.user.set_password(password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in after password change
                messages.success(request, 'Password changed successfully!')
                return redirect('index')  # Redirect to the index page
            else:
                messages.error(request, 'Passwords do not match.')

    return render(request, 'chatapp/account_settings.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        profileimg = request.FILES.get('profileimg')  # Get the uploaded file
        bio = request.POST.get('bio')
        name = request.POST.get('name')  # Get the name field from the form

        # Update the username if changed
        if username:
            user.username = username
            user.save()

        # Update the profile image if uploaded
        if profileimg:
            user.profile.profileimg = profileimg
            user.profile.save()

        # Update the bio if provided
        if bio is not None:
            user.profile.bio = bio
            user.profile.save()

        # Update the name if provided
        if name:
            user.profile.name = name
            user.profile.save()

        messages.success(request, 'Profile updated successfully!')    

        return redirect('index')  # Redirect to the index page after saving changes

    return render(request, 'chatapp/profile_settings.html')

def view_profile(request, pk):
    # Get the profile of the user by primary key (pk)
    user = get_object_or_404(User, pk=pk)
    
    # Render a template to display profile details
    return render(request, 'chatapp/view_profile.html', {'profile_user': user})

@login_required
def search_friends(request):
    query = request.GET.get('query', '')  # Default to an empty string if query is None
    if query:  # Check if the query is not empty
        friends = Profile.objects.filter(user__username__icontains=query)
    else:
        friends = Profile.objects.none()  # If query is empty, return no friends

    return render(request, 'chatapp/search_results.html', {'friends': friends})


@login_required
def add_friend(request):
    if request.method == 'POST':
        friend_id = request.POST.get('friend_id')  # Get the friend's user ID from the form
        
        if friend_id:  # Ensure friend_id is not None
            friend = get_object_or_404(User, id=friend_id)  # Retrieve the friend by ID
            
            # Check if the user has blocked this friend
            if Blocked.objects.filter(blocker=request.user, blocked=friend).exists():
                messages.error(request, "You cannot add this user as a friend because you have blocked this user.")
                return redirect('index')  # Redirect after error
            
            # Check if the friend has blocked the user
            if Blocked.objects.filter(blocker=friend, blocked=request.user).exists():
                messages.error(request, "You cannot add this user as a friend because they have blocked you.")
                return redirect('index')  # Redirect after error
            
            # Call your method to create the friendship
            if Friend.add_friend(request.user, friend):  # Check if friendship was created
                messages.success(request, "Friend added successfully.")
            else:
                messages.info(request, "You are already friends with this user.")
                
            return redirect('index')  # Redirect after adding
        else:
            messages.error(request, "Friend ID is required.")  # Provide error feedback
            
    return redirect('index')  # Redirect if the request method is not POST


@login_required(login_url='login')
def delete_account(request):
    if request.method == 'POST':
        try:
            user = request.user
            auth_logout(request) 
            user.delete()
            messages.info(request, 'Your account has been deleted.')
            return redirect('signup')  
        except Exception as e:
            messages.error(request, 'An error occurred while deleting your account.')
            return redirect('settings')  
    return render(request, 'chatapp/settings.html')
    

# views.py

@login_required
def remove_friend(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    
    # Check if the friendship exists
    try:
        friendship = Friend.objects.get(user=request.user, friend=friend)
        friendship1 = Friend.objects.get(user=friend, friend=request.user)
        friendship.delete()  # Remove the friendship
        friendship1.delete()  # Remove the friendship
        messages.success(request, f"You have removed {friend.username} from your friends.")
    except Friend.DoesNotExist:
        messages.error(request, "Friendship does not exist.")

    return redirect('index')  # Redirect back to the index page

def block_friend(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    Blocked.objects.get_or_create(blocker=request.user, blocked=friend)
    messages.success(request, f"You have blocked {friend.username}.")
    return redirect('index')

@login_required
def unblock_friend(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    # Check if the friend is in the user's blocked list
    Blocked.objects.filter(blocker=request.user, blocked=friend).delete()
    # Add a success message
    messages.success(request, f"You have unblocked {friend.username}.")
    return redirect('index')  # Redirect back to the index page
