from django.contrib import admin
from .models import Brand, Racket, RacketImage, Review

class RacketImageInline(admin.TabularInline):
    model = RacketImage
    extra = 3  # Show 3 empty slots for images by default

class RacketAdmin(admin.ModelAdmin):
    inlines = [RacketImageInline]  # Attach showcase images to each racket

admin.site.register(Brand)
admin.site.register(Racket, RacketAdmin)
admin.site.register(RacketImage)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('racket', 'user', 'power', 'control', 'comfort', 'agility', 'spin', 'hard', 'exit', 'created_at')
    list_filter = ('racket', 'user', 'created_at')
    search_fields = ('racket__name', 'user__username', 'comment')

from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('racket', 'user', 'control', 'power', 'agility', 'comfort', 'spin', 'hard', 'exit', 'created_at')
    list_filter = ('racket', 'user', 'created_at')
    search_fields = ('racket__name', 'user__username', 'comment')


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('User Type', {'fields': ('user_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Type', {'fields': ('user_type',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
