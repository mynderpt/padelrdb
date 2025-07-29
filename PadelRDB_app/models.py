from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import os
import math
import requests
import re
from django.core.files.storage import default_storage
from django.contrib.auth.models import AbstractUser


# Helper Functions
def racket_image_path(instance, filename):
    return os.path.join('brands', instance.brand.name, instance.name, filename)

def user_profile_image_path(instance, filename):
    return f'profile_pics/{instance.username}/{filename}'


# Models

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brand_logos/')

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Racket(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    core = models.CharField(max_length=255)
    surface = models.CharField(max_length=255)
    weight = models.CharField(max_length=255)
    shape = models.CharField(max_length=255)
    balance = models.CharField(max_length=255)
    gametype = models.CharField(max_length=255)
    finish = models.CharField(max_length=255)
    thumbnail = models.ImageField(upload_to=racket_image_path)
    media_urls = models.JSONField(default=list, blank=True)  # Stores a list of video URLs
    store_links = models.JSONField(default=dict, blank=True)  # Stores a list of store URLs

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Racket.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def categorized_links(self):
        # Ensure store_links is a dictionary
        if not isinstance(self.store_links, dict):
            return {"brand": [], "retailers": []}  # Return an empty valid structure

        categorized = {"brand": [], "retailers": []}
        for link in self.store_links.get("brand", []):
            categorized["brand"].append({"url": link, "store": "brand"})

        for retailer, links in self.store_links.get("retailers", {}).items():
            for link in links:
                categorized["retailers"].append({"url": link, "store": retailer})

        return categorized

    def get_video_details(self, video_url):
        video_info = {
            "title": None,
            "thumbnail": None,
            "creator": None,
            "url": video_url
        }

        if "youtube.com" in video_url or "youtu.be" in video_url:
            oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
            response = requests.get(oembed_url)

            if response.status_code == 200:
                data = response.json()
                video_id_match = re.search(r"v=([\w-]+)", video_url)
                video_id = video_id_match.group(1) if video_id_match else None

                video_info["title"] = data.get("title")
                video_info["creator"] = data.get("author_name")
                video_info["thumbnail"] = (
                    f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else data.get("thumbnail_url")
                )

        return video_info

    def get_media_details(self):
        return [self.get_video_details(url) for url in self.media_urls]
    
    
    def round_nearest_0_1(self, value):
        """Rounds value to the nearest 0.1 (e.g., 6.46 → 6.5, 6.44 → 6.4)."""
        if value is None:
            return 0.0
        return round(value, 1)  # Round to 1 decimal place


    def __str__(self):
        return self.name


class Review(models.Model):
    USER_TYPES = [('regular', 'Regular Player'), ('expert', 'Expert Player')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='regular')
    racket = models.ForeignKey(Racket, on_delete=models.CASCADE, related_name='reviews', blank=False)
    power = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    control = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    comfort = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    agility = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    spin = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    exit = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    hard = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    comment = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'racket'], name='unique_review')]       

   
   
    def __init__(self, *args, **kwargs):
        user = kwargs.get('user')
        super().__init__(*args, **kwargs)
        
        # Automatically set the user_type to the user's current type
        if user:
            self.user_type = user.user_type  # Set the user_type to the logged-in user's type


    def __str__(self):
        return f"{self.user.username} - {self.racket.name} Review"


class RacketImage(models.Model):
    racket = models.ForeignKey(Racket, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='racket_images/')


class CustomUser(AbstractUser):
    user_type_choices = [
        ('regular', 'Regular Player'),
        ('expert', 'Expert Player'),
    ]
    user_type = models.CharField(max_length=10, choices=user_type_choices, default='regular')
    profile_image = models.ImageField(
        upload_to='profile_pics/',  # ✅ This should NOT include 'media/'
        default='profile_pics/default_profile.png',
        blank=True,  # Allow empty field
        null=True     # Allow database null value
    )

    def remove_profile_image(self):
        """Deletes the current profile image and resets to default."""
        if self.profile_image and self.profile_image.name != 'profile_pics/default_profile.png':
            if default_storage.exists(self.profile_image.name):
                default_storage.delete(self.profile_image.name)  # Delete the file
            
            # Reset to default
            self.profile_image = 'profile_pics/default_profile.png'
            self.save()

    def delete(self, *args, **kwargs):
        """Delete user and their related reviews."""
        self.reviews.all().delete()  # Delete all reviews by the user
        super().delete(*args, **kwargs)
