from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .models import Brand, Racket, Review
from .forms import ReviewForm

# Homepage view
def index(request):
    return render(request, 'home.html')

# Browse page view
def browse(request):
    brands = Brand.objects.all()
    return render(request, 'browse.html', {'brands': brands})


#Login page
def login(request):
    return render(request, 'login.html')


#Create account page
def create(request):
    return render (request, 'create.html')


#Redirect Page
def nologin(request):
    return render (request, 'nologin.html')

def brand_page(request, name):
    brand = get_object_or_404(Brand, name=name.lower())
    rackets = Racket.objects.filter(brand=brand)

    # Apply optional filter from query string
    game_type = request.GET.get("type_of_game")
    if game_type:
        rackets = rackets.filter(gametype=game_type)

    # Use a Python set to ensure uniqueness
    game_types_qs = Racket.objects.filter(brand=brand).values_list('gametype', flat=True)
    game_types = sorted(set(game_types_qs))

    context = {
        'brand': brand,
        'rackets': rackets,
        'game_types': game_types,
    }

    return render(request, 'brand_page.html', context)

# Racket detail view
def racket_detail(request, name, slug):
    racket = get_object_or_404(Racket, slug=slug)

    # Average scores grouped by user type
    avg_reviews = (
        Review.objects.filter(racket=racket)
        .values('user_type')
        .annotate(
            avg_power=Avg('power'),
            avg_control=Avg('control'),
            avg_comfort=Avg('comfort'),
            avg_maneuverability=Avg('agility'),
            avg_spin=Avg('spin'),
            avg_hard=Avg('hard'),
            avg_exit=Avg('exit'),
        )
    )

    # Initialize empty dicts
    user_scores = {'power': 0, 'control': 0, 'comfort': 0, 'agility': 0, 'spin': 0, 'hard': 0, 'exit': 0, 'total_reviews': 0}
    expert_scores = {'power': 0, 'control': 0, 'comfort': 0, 'agility': 0, 'spin': 0, 'hard': 0, 'exit': 0, 'total_reviews': 0}

    # Update with values from the aggregation
    for review in avg_reviews:
        if review['user_type'] == 'regular':
            user_scores.update(review)
        elif review['user_type'] == 'expert':
            expert_scores.update(review)

    # Add total review counts
    user_scores['total_reviews'] = Review.objects.filter(racket=racket, user_type='regular').count()
    expert_scores['total_reviews'] = Review.objects.filter(racket=racket, user_type='expert').count()

    # Comments
    latest_comment = Review.objects.filter(racket=racket).order_by('-created_at').first()
    comments = Review.objects.filter(racket=racket).order_by('-created_at')

    context = {
        'racket': racket,
        'user_scores': user_scores,
        'expert_scores': expert_scores,
        'comments': comments,
        'latest_comment': latest_comment,
        'media_urls': racket.media_urls,
        'store_links': racket.store_links,
    }

    return render(request, 'racket_detail.html', context)


# Add a review (only available to logged-in users)
@login_required
def add_review(request, racket_id):
    racket = get_object_or_404(Racket, id=racket_id)
    
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.racket = racket
            review.user = request.user
            review.user_type = request.user.user_type
            review.save()
            return redirect('racket_detail', name=racket.brand.name.lower(), slug=racket.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'add_review.html', {'form': form, 'racket': racket})

# Review view for a specific user
@login_required
def review_view(request, slug=None):
    brands = Brand.objects.all()
    review = None
    racket = None

    # Get brand from URL parameter (if available)
    brand_from_url = None
    if request.GET.get('brand_id'):
        brand_from_url = Brand.objects.get(id=request.GET.get('brand_id'))

    # If a racket slug is provided, fetch the racket and its review
    if slug:
        racket = get_object_or_404(Racket, slug=slug)  # Make sure to use 'slug' here instead of 'id'
        review = Review.objects.filter(user=request.user, racket=racket).first()

    form = ReviewForm(instance=review)

    return render(request, 'review.html', {'brands': brands, 'form': form, 'racket': racket, 'brand_from_url': brand_from_url})


def all_rackets(request):
    game_type = request.GET.get("type_of_game")
    rackets = Racket.objects.all()
    
    if game_type:
        rackets = rackets.filter(gametype=game_type)
    
    # Ensure unique game types
    game_types_qs = Racket.objects.values_list('gametype', flat=True)
    game_types = sorted(set(game_types_qs))

    return render(request, 'brand_page.html', {
        'rackets': rackets,
        'brand': {'name': 'All Rackets'},
        'game_types': game_types,
    })




# Submit review (after form submission)
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Review, Racket

@login_required
def submit_review(request):
    if request.method == 'POST':
        user = request.user
        racket_id = request.POST.get('racket_id')
        power = int(request.POST.get('power', 0))
        control = int(request.POST.get('control', 0))
        comfort = int(request.POST.get('comfort', 0))
        agility = int(request.POST.get('agility', 0))
        spin = int(request.POST.get('spin', 0))
        hard = int(request.POST.get('hard', 0))
        exit = int(request.POST.get('exit', 0))
        comment = request.POST.get('comment', '')

        # Get the racket object based on the provided racket_id
        racket = Racket.objects.get(id=racket_id)

        # Ensure the user_type is set to the current logged-in user's user_type
        user_type = user.user_type  # Get the user type ('regular' or 'expert')

        # Create or update the review, ensuring we set the user_type
        review, created = Review.objects.update_or_create(
            user=user,
            racket=racket,
            defaults={
                'power': power,
                'control': control,
                'comfort': comfort,
                'agility': agility,
                'spin': spin,
                'hard': agility,
                'exit': spin,
                'comment': comment,
                'user_type': user_type  # Set the user_type field here
            }
        )

        # The `review` object returned here is the updated or created Review instance.
        # You can use it directly without needing to refer to 'instance'.
        
        # Redirect to the profile page after submitting the review
        return redirect('profile')  # Change this to the appropriate URL name for the profile page

    # If method is not POST, redirect to the review page
    return redirect('review')



# Get models for a specific brand
def get_models(request):
    brand_id = request.GET.get('brand_id')

    if brand_id:
        models = Racket.objects.filter(brand_id=brand_id).values('id', 'name')
        return JsonResponse(list(models), safe=False)

    return JsonResponse({'error': 'No brand selected'}, status=400)

# Get racket details via AJAX
def get_racket(request, model_id):
    try:
        racket = Racket.objects.get(id=model_id)
        return JsonResponse({
            'thumbnail': racket.thumbnail.url if racket.thumbnail else '',
            'name': racket.name,
        })
    except Racket.DoesNotExist:
        return JsonResponse({'error': 'Racket not found'}, status=404)

# Profile view for logged-in user
@login_required
def profile_view(request):
    user_reviews = (
        Review.objects.filter(user=request.user)
        .select_related('racket__brand')  # Optimizes queries
        .order_by('racket__brand__name', 'racket__name')  # Sort by brand then racket name
    )

    # Group reviews by brand
    reviews_by_brand = {}
    for review in user_reviews:
        brand_name = review.racket.brand.name
        if brand_name not in reviews_by_brand:
            reviews_by_brand[brand_name] = []
        reviews_by_brand[brand_name].append(review)

    return render(request, 'profile.html', {'user': request.user, 'reviews': reviews_by_brand})

# Change password view via AJAX
@login_required
def change_password_ajax(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # Keeps user logged in
            return JsonResponse({'success': True, 'message': 'Password changed successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Delete a review
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect("profile")  # Redirect after deletion

# Upload profile photo view
@login_required
def upload_profile_photo(request):
    if request.method == 'POST' and request.FILES.get('profile_image'):
        user = request.user
        new_image = request.FILES['profile_image']
        
        # Delete old profile image if it exists (except default)
        if user.profile_image and not user.profile_image.name.startswith('profile_pics/default'):
            old_path = user.profile_image.path
            if os.path.exists(old_path):
                os.remove(old_path)

        # Save the new image
        file_path = f"profile_pics/{user.username}_{new_image.name}"
        user.profile_image.save(file_path, new_image, save=True)

        return JsonResponse({'success': True, 'image_url': user.profile_image.url})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

# Delete profile photo view
@login_required
def delete_profile_photo(request):
    if request.method == 'POST':
        user = request.user
        default_image_path = 'profile_pics/default_profile.png'  # Ensure this is correct

        # Prevent deletion if the current image is already the default
        if user.profile_image.name == default_image_path:
            return JsonResponse({'success': False, 'error': 'Cannot delete default profile picture.'})

        # Remove old profile image (if exists and is not the default)
        if user.profile_image and user.profile_image.name != default_image_path:
            old_path = os.path.join(settings.MEDIA_ROOT, user.profile_image.name)
            if os.path.exists(old_path):
                os.remove(old_path)  # ✅ Physically delete the image file

        # Reset to default image
        user.profile_image.name = default_image_path  
        user.save()

        return JsonResponse({'success': True, 'default_image_url': user.profile_image.url})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

from django.templatetags.static import static  # Import the static helper function

def get_review(request):
    racket_id = request.GET.get("racket_id")
    user = request.user  # Get logged-in user

    if not racket_id:
        return JsonResponse({"error": "No racket selected"}, status=400)

    try:
        racket = Racket.objects.get(id=racket_id)  # Fetch racket details
    except Racket.DoesNotExist:
        return JsonResponse({"error": "Racket not found"}, status=404)
    

    default_thumbnail_url = static("images/blank.png")  # Update with the correct path

    # Try to get the user's review
    review = Review.objects.filter(racket=racket, user=user).first()

    # Default response (even if no review exists)
    response_data = {
        "racket_name": racket.name,
        "thumbnail": racket.thumbnail.url if racket.thumbnail else "",
        "power": review.power if review else 0,
        "control": review.control if review else 0,
        "comfort": review.comfort if review else 0,
        "agility": review.agility if review else 0,
        "spin": review.spin if review else 0,
        "hard": review.agility if review else 0,
        "exit": review.spin if review else 0,
        "comment": review.comment if review else "",
        "message": "No previous review found." if not review else "",
    }

    return JsonResponse(response_data)



from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Review
import re

# List of banned words
BANNED_WORDS = [
    "badword1", "badword2", "merde", "schlecht", "puta", "mierda", "f***", "sh*t",
    "idiot", "stupid", "dumb", "asshole", "pendejo", "hijo de puta", "bitch", "fuck",
    "shit", "fucking", "sh!t", "f!ck", "nigga", "nigger", "nga", "niggers"
]

def contains_profanity(text):
    """ Check if a text contains banned words """
    text_lower = text.lower()
    return any(re.search(rf"\b{re.escape(word)}\b", text_lower) for word in BANNED_WORDS)

def submit_review(request):
    if request.method == "POST":
        comment = request.POST.get("comment", "").strip()

        # Check for profanity
        if contains_profanity(comment):
            return JsonResponse({"error": "Your comment contains inappropriate language."}, status=400)

        # Save review if it's valid
        review = Review.objects.create(
            racket_id=request.POST.get("racket_id"),
            power=request.POST.get("power"),
            control=request.POST.get("control"),
            comfort=request.POST.get("comfort"),
            agility=request.POST.get("agility"),
            spin=request.POST.get("spin"),
            hard=request.POST.get("hard"),
            exit=request.POST.get("exit"),
            comment=comment
        )
        review.save()
        return redirect("success_page")  # Redirect after successful submission

    return JsonResponse({"error": "Invalid request."}, status=400)



from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('profile')  # or any success URL



from django.shortcuts import redirect

def review_gate(request):
    if request.user.is_authenticated:
        return redirect('review')  # Or use 'review_view' if you meant the slug-based one
    else:
        return redirect('redirect')  # Goes to your "please log in" page


# views.py
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect anywhere after logout


from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest

def create_account(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        next_url = request.POST.get('next') or '/'

        # Basic validation
        if not username or not email or not password or password != confirm_password:
            return HttpResponseBadRequest("Invalid form submission.")

        # Check if username or email already exist
        if User.objects.filter(username=username).exists():
            return render(request, 'create.html', {'error': 'Username already taken'})
        if User.objects.filter(email=email).exists():
            return render(request, 'create.html', {'error': 'Email already used'})

        # Create and log in the user
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect(next_url)

    return render(request, 'create.html')


from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_redirect_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        return next_url or super().get_redirect_url()



from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib import messages

User = get_user_model()

def create_account(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('create')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('create')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('create')

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
        )
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'create.html')
