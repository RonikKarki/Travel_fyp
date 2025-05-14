from rest_framework import serializers
from .models import Booking, ContactMessage, CustomUser, Destination, Guide, GuideAppointment, Itinerary, Review, TravelPackage, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['is_admin'] = user.is_staff  
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['is_admin'] = self.user.is_staff  
        return data
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password', 'password2', 'user_type']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'user_type']

class TravelPackageSerializer(serializers.ModelSerializer):
    destinations = serializers.StringRelatedField(many=True)  # Keep this if you only need the name
    image_url = serializers.SerializerMethodField()  # Add a custom field for the full image URL

    class Meta:
        model = TravelPackage
        fields = ['id', 'title', 'description', 'price', 'duration', 'destinations', 'image_url', 'is_active']

    def get_image_url(self, obj):
        request = self.context.get('request')  # Get the request object from the serializer context
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)  # Construct the full URL for the image
            return obj.image.url  # Return the relative URL if request is None
        return None  # Return None if no image is available

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    travel_package = serializers.PrimaryKeyRelatedField(queryset=TravelPackage.objects.all())  # Make it writable

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['user', 'total_price', 'created_at']

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status']

class GuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guide
        fields = '__all__'

class GuideAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideAppointment
        fields = '__all__'
        read_only_fields = ['user', 'status', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['user', 'rating', 'comment', 'created_at', 'is_approved']
        read_only_fields = ['user', 'created_at', 'is_approved']  # Mark user, created_at, and is_approved as read-only


class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = ['day', 'title', 'description']

class DestinationSerializer(serializers.ModelSerializer):
    itineraries = ItinerarySerializer(many=True, read_only=True)
    related_packages = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = ['id', 'name', 'location', 'highlights', 'best_time_to_visit', 'cover_image', 'itineraries', 'related_packages']

    def get_related_packages(self, obj):
        packages = TravelPackage.objects.filter(destinations=obj, is_active=True)
        request = self.context.get('request')  # Get the request object from the serializer context
        return TravelPackageSerializer(packages, many=True, context={'request': request}).data


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'