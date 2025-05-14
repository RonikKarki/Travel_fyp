from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Guide, Itinerary, Review, TravelPackage, Destination

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'phone', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone')}),
    )
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'user_type']

@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'duration', 'is_active')
    filter_horizontal = ('destinations',)
    search_fields = ['title', 'destinations__name']
    list_filter = ['is_active', 'duration']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'rating', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'rating']
    search_fields = ['user__username', 'comment']
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    reject_reviews.short_description = "Reject selected reviews"

class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 1

class DestinationAdmin(admin.ModelAdmin):
    inlines = [ItineraryInline]
    list_display = ('name', 'location', 'best_time_to_visit')

admin.site.register(Destination, DestinationAdmin)
admin.site.register(Guide)
admin.site.register(CustomUser, CustomUserAdmin)