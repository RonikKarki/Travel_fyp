from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('traveler', 'Traveler'),
        ('guide', 'Guide'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='traveler')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

class TravelPackage(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in days")
    destinations = models.ManyToManyField('Destination', related_name='packages') 
    image = models.ImageField(upload_to='package_images/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
User = get_user_model()

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    travel_package = models.ForeignKey(TravelPackage, on_delete=models.CASCADE)
    travel_date = models.DateField()
    traveler_count = models.PositiveIntegerField()
    special_request = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(default='Pending', max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.travel_package.title} ({self.travel_date})"
    
class Guide(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=200)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='guides/', blank=True)

    def __str__(self):
        return self.name

class GuideAppointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE)
    travel_date = models.DateField()
    travel_time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)  # 1 to 5 scale
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)  # Admin can approve or reject the review

    def __str__(self):
        return f"Review by {self.user.username} - {self.rating}/5"
    

class Destination(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    highlights = models.TextField()
    best_time_to_visit = models.CharField(max_length=100)
    cover_image = models.ImageField(upload_to="destination_images/")

    def __str__(self):
        return self.name
    
class Itinerary(models.Model):
    destination = models.ForeignKey(Destination, related_name='itineraries', on_delete=models.CASCADE)
    day = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.destination.name} - Day {self.day}: {self.title}"
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"
