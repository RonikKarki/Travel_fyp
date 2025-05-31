from django.conf import settings
from rest_framework.filters import SearchFilter
from rest_framework import generics, permissions
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import BookingSerializer, BookingStatusUpdateSerializer, ContactMessageSerializer, CustomTokenObtainPairSerializer, DestinationSerializer, GuideAppointmentSerializer, GuideSerializer, RegisterSerializer, ReviewSerializer, TravelPackageSerializer, UserSerializer
from .models import Booking, ContactMessage, CustomUser, Destination, Guide, GuideAppointment, Review, TravelPackage
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
import requests

token_generator = PasswordResetTokenGenerator()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            # Call get_user_model() to get the custom user model class
            User = get_user_model()
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"
            send_mail(
                'Reset Your Password',
                f'Click this link to reset your password: {reset_link}',
                'your_email@gmail.com',
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset link sent to your email.'})
        except User.DoesNotExist:  # Use the exception from the custom user model
            return Response({'error': 'User with this email does not exist.'}, status=404)

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            # Get the user model first
            User = get_user_model()
            
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            # Validate the token
            if token_generator.check_token(user, token):
                new_password = request.data.get('password')
                if not new_password:
                    return Response({'error': 'Password is required.'}, status=400)

                # Set the new password
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password reset successful.'}, status=200)
            else:
                return Response({'error': 'Invalid or expired token.'}, status=400)
        except (User.DoesNotExist, ValueError):
            return Response({'error': 'Invalid user ID or token.'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
class TravelPackageListView(ListAPIView):
    queryset = TravelPackage.objects.filter(is_active=True)
    serializer_class = TravelPackageSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description', 'destinations__name', 'duration', 'price']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Add the request object to the context
        return context

class PackageDetailView(generics.RetrieveAPIView):
    queryset = TravelPackage.objects.filter(is_active=True)
    serializer_class = TravelPackageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Add the request object to the context
        return context


class CreateBookingView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        package = serializer.validated_data['travel_package']
        count = serializer.validated_data['traveler_count']
        total_price = package.price * count
        serializer.save(user=self.request.user, total_price=total_price)


class AdminBookingListView(generics.ListAPIView):
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    permission_classes = [IsAdminUser]

class AdminBookingUpdateView(generics.UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def perform_update(self, serializer):
        booking = self.get_object()
        previous_status = booking.status
        updated_booking = serializer.save()

        user_email = booking.user.email
        user_name = booking.user.get_full_name() or booking.user.username
        package_name = booking.travel_package.title

        # Send email if status changed
        if previous_status != updated_booking.status:
            subject = f"Booking {updated_booking.status} - Shangrila Voyages"
            
            if updated_booking.status == 'Confirmed':
                message = f"Dear {user_name},\n\nYour booking for the package \"{package_name}\" has been confirmed. 🎉\n\nThank you for booking with Shangrila Voyages!\n\nBest Regards,\nShangrila Team"
            elif updated_booking.status == 'Cancelled':
                message = f"Dear {user_name},\n\nWe regret to inform you that your booking for the package \"{package_name}\" has been cancelled.\n\nFor any queries, contact our support.\n\nSincerely,\nShangrila Team"
            else:
                message = None
            
            if message:
                send_mail(
                    subject,
                    message,
                    None,  # uses DEFAULT_FROM_EMAIL
                    [user_email],
                    fail_silently=False
                )

class UserBookingHistoryView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        if booking.status == "confirmed":
            return Response({"error": "Cannot cancel a confirmed booking"}, status=400)
        booking.status = "cancelled"
        booking.save()
        return Response({"message": "Booking cancelled"})
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)
    

class GuideListView(generics.ListAPIView):
    queryset = Guide.objects.filter(available=True)
    serializer_class = GuideSerializer

class GuideAppointmentCreateView(generics.CreateAPIView):
    queryset = GuideAppointment.objects.all()
    serializer_class = GuideAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class KhaltiInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            data = request.data
            amount = data.get("amount")
            purchase_order_id = data.get("purchase_order_id")
            purchase_order_name = data.get("purchase_order_name")
            return_url = data.get("return_url")
            website_url = data.get("website_url")

            if not all([amount, purchase_order_id, purchase_order_name, return_url, website_url]):
                missing_fields = [field for field in ['amount', 'purchase_order_id', 'purchase_order_name', 'return_url', 'website_url'] 
                                if not data.get(field)]
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # SANDBOX ENDPOINT!
            KHALTI_API_URL = "https://dev.khalti.com/api/v2/epayment/initiate/"
            KHALTI_SECRET_KEY = "926dcc917dbe4c48a130432b1908ae25"  # Your sandbox secret key

            headers = {
                "Authorization": f"Key {KHALTI_SECRET_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "return_url": return_url,
                "website_url": website_url,
                "amount": int(amount),
                "purchase_order_id": purchase_order_id,
                "purchase_order_name": purchase_order_name
            }

            response = requests.post(
                KHALTI_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                return Response(response.json(), status=response.status_code)

            data = response.json()
            payment_url = data.get("payment_url")
            if not payment_url:
                return Response({"error": "Payment URL not received from Khalti"}, status=400)

            return Response({"payment_url": payment_url})

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class KhaltiVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pidx = request.data.get('pidx')
        if not pidx:
            return Response(
                {'error': 'pidx is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Authorization": "Key 926dcc917dbe4c48a130432b1908ae25",  # Your sandbox secret key
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://dev.khalti.com/api/v2/epayment/lookup/",  # SANDBOX URL
                json={"pidx": pidx},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'Completed':
                    # Update booking status to confirmed
                    booking = Booking.objects.filter(payment_id=pidx).first()
                    if booking:
                        booking.status = 'confirmed'
                        booking.save()
                return Response(data)
            else:
                return Response(response.json(), status=response.status_code)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GuideAppointmentListAdminView(generics.ListAPIView):
    queryset = GuideAppointment.objects.all().order_by('-created_at')
    serializer_class = GuideAppointmentSerializer
    permission_classes = [IsAdminUser]

class GuideAppointmentUpdateAdminView(generics.RetrieveUpdateAPIView):
    queryset = GuideAppointment.objects.all()
    serializer_class = GuideAppointmentSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        try:
            # Save the updated instance
            instance = serializer.save()
            subject = ''
            message = ''

            # Check the updated status and prepare the email
            if instance.status == 'confirmed':
                subject = 'Guide Appointment Confirmed'
                message = (
                    f'Hello {instance.user.username},\n\n'
                    f'Your guide appointment with {instance.guide.name} on {instance.travel_date} at {instance.travel_time} has been confirmed.\n\n'
                    f'Thank you for choosing Shangrila Voyages!'
                )
            elif instance.status == 'cancelled':
                subject = 'Guide Appointment Cancelled'
                message = (
                    f'Hello {instance.user.username},\n\n'
                    f'We regret to inform you that your guide appointment on {instance.travel_date} at {instance.travel_time} has been cancelled.\n\n'
                    f'If you have any questions, please contact our support team.'
                )

            # Send the email if subject and message are set
            if subject and message:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,  # Ensure EMAIL_HOST_USER is set in settings.py
                    [instance.user.email],
                    fail_silently=False,  # Set to False to raise errors if email fails
                )
        except ValidationError as e:
            raise ValidationError({"error": str(e)})
        except Exception as e:
            raise ValidationError({"error": "An unexpected error occurred while updating the appointment."})

    def update(self, request, *args, **kwargs):
        try:
            # Validate the status field
            status_value = request.data.get('status')
            if status_value not in ['confirmed', 'cancelled']:
                return Response(
                    {"error": "Invalid status value. Allowed values are 'confirmed' or 'cancelled'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Proceed with the update
            return super().update(request, *args, **kwargs)
        except GuideAppointment.DoesNotExist:
            return Response(
                {"error": "Guide appointment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UserAppointmentHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        appointments = GuideAppointment.objects.filter(user=user).order_by('-travel_date')
        serializer = GuideAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
class ReviewListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        reviews = Review.objects.filter(is_approved=True)  # Only show approved reviews
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Review submitted successfully!"}, status=201)
        return Response(serializer.errors, status=400)
    
class DestinationListAPIView(ListAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # Add the request object to the context
        return context

class DestinationDetailAPIView(generics.RetrieveAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    lookup_field = 'id'  # or 'pk'

class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        send_mail(
            subject='Thank you for contacting us!',
            message="We received your message. We'll get back to you soon!",
            from_email='ShangrilaVoyages@example.com',
            recipient_list=[instance.email],
            fail_silently=False,
        )

