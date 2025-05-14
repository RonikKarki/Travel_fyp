from django.urls import path
from .views import (
    AdminBookingListView, AdminBookingUpdateView, ContactMessageCreateView,
    CreateBookingView, CustomTokenObtainPairView, DestinationDetailAPIView,
    DestinationListAPIView, GuideAppointmentCreateView, GuideAppointmentListAdminView,
    GuideAppointmentUpdateAdminView, GuideListView, KhaltiInitiateView,
    KhaltiVerifyView, PackageDetailView, PasswordResetConfirmView,
    PasswordResetRequestView, RegisterView, ReviewCreateView, ReviewListView,
    TravelPackageListView, UserAppointmentHistory, UserBookingHistoryView,
    UserProfileUpdateView, cancel_booking
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Use CustomTokenObtainPairView here
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', PasswordResetRequestView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='reset-password'),
    path('packages/', TravelPackageListView.as_view(), name='package-list'),
    path('packages/<int:pk>/', PackageDetailView.as_view()),
    path('bookings/create/', CreateBookingView.as_view(), name='create-booking'),
    path('admin/bookings/', AdminBookingListView.as_view(), name='admin-bookings'),
    path('admin/bookings/<int:id>/update/', AdminBookingUpdateView.as_view(), name='admin-booking-update'),
    path('user/bookings/', UserBookingHistoryView.as_view(), name='user-bookings'),
    path('user/profile/', UserProfileUpdateView.as_view(), name='update-user-profile'),
    path('booking/<int:booking_id>/cancel/', cancel_booking, name='cancel-booking'),
    path('guides/', GuideListView.as_view(), name='guide-list'),
    path('guides/appointments/', GuideAppointmentCreateView.as_view(), name='guide-appointment'),
    path('admin/guides/appointments/', GuideAppointmentListAdminView.as_view(), name='admin-guide-appointments'),
    path('admin/guides/appointments/<int:pk>/', GuideAppointmentUpdateAdminView.as_view(), name='admin-update-guide-appointment'),
    path('my-appointments/', UserAppointmentHistory.as_view(), name='user-appointments'),
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', ReviewCreateView.as_view(), name='review-create'),
    path('destinations/', DestinationListAPIView.as_view(), name='destination-list'),
    path('destinations/<int:id>/', DestinationDetailAPIView.as_view(), name='destination-detail'),
    path('contact/', ContactMessageCreateView.as_view(), name='contact-message'),
    path('khalti/initiate/', KhaltiInitiateView.as_view(), name='khalti-initiate'),
    path('khalti/verify/', KhaltiVerifyView.as_view(), name='khalti-verify'),
]