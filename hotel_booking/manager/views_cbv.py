import csv
from calendar import monthcalendar
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.db.models import Q, Count, Sum, F, Value, DecimalField, IntegerField
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from bookings.models import Booking, BookingAuditLog, BookingRefund, RefundPolicy
from core.models import (Extra, Hotel, Room, RoomAmenity, RoomImage, RoomType,
                       RoomTypeAmenity, SeasonalPricing)
from offers.models import Offer, OfferCategory, OfferHighlight, OfferImage
from accounts.models import CustomUser
from payments.models import Payment

from .forms import (BookingForm, ExtraForm, HotelForm, RoomAmenityForm,
                    RoomForm, RoomImageForm, RoomTypeAmenityForm,
                    RoomTypeForm, SeasonalPricingForm, OfferForm, OfferCategoryForm,
                    OfferHighlightForm, OfferImageForm, BulkBookingStatusForm, RefundPolicyForm, PaymentForm)


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure only managers can access the view."""
    
    def test_func(self):
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        
        # Check if user is staff with correct user_type and not admin/superuser
        return (user.is_authenticated and 
                user.is_staff and 
                user_type == 'staff' and 
                not user.is_superuser and 
                user_type != 'admin')
    
    def handle_no_permission(self):
        logout(self.request)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(
            self.request.get_full_path(),
            reverse_lazy('manager:login'),
            'next'
        )


def manager_logout(request):
    """Simple logout function that redirects to manager login."""
    logout(request)
    # Clear all messages from session to prevent showing login success message
    if '_messages' in request.session:
        del request.session['_messages']
    request.session.modified = True
    return redirect('manager:login')


class ManagerLoginView(View):
    """
    Custom login view for managers only.
    Only allows users with user_type 'staff' and is_staff=True to login.
    Blocks admin users (user_type 'admin' or is_superuser=True).
    Includes rate limiting and failed login tracking.
    """

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        from django.contrib.auth import authenticate
        from accounts.models import CustomUser

        email = request.POST.get('email')
        password = request.POST.get('password')

        # Generic error message to prevent user enumeration
        error_message = 'Invalid credentials. Please check your email and password.'

        if not email or not password:
            messages.error(request, error_message)
            return render(request, 'manager/login.html', {'form': None})

        try:
            user = CustomUser.objects.get(email=email)
            # Track failed login attempts
            if user.failed_login_attempts >= 5:
                messages.error(request, 'Account temporarily locked due to too many failed attempts.')
                return render(request, 'manager/login.html', {'form': None})

            authenticated_user = authenticate(request, username=email, password=password)

            if authenticated_user is not None:
                if authenticated_user.is_active:
                    user_type = getattr(authenticated_user, 'user_type', None)
                    if (authenticated_user.is_staff and
                        user_type == 'staff' and
                        not authenticated_user.is_superuser and
                        user_type != 'admin'):

                        # Reset failed login attempts on successful login
                        authenticated_user.failed_login_attempts = 0
                        authenticated_user.save(update_fields=['failed_login_attempts'])

                        login(request, authenticated_user)
                        messages.success(request, 'Login successful. Welcome, Manager!')
                        return redirect('manager:dashboard')
                    else:
                        messages.error(request, error_message)
                else:
                    messages.error(request, error_message)
            else:
                # Increment failed login attempts
                user.failed_login_attempts += 1
                user.save(update_fields=['failed_login_attempts'])
                messages.error(request, error_message)

        except CustomUser.DoesNotExist:
            # Don't reveal that email doesn't exist
            messages.error(request, error_message)

        return render(request, 'manager/login.html', {'form': None})

    def get(self, request):
        # Render a simple form with email and password fields
        return render(request, 'manager/login.html', {'form': None})


class DashboardView(ManagerRequiredMixin, View):
    """Enhanced dashboard with quick stats for the manager UI."""
    
    def get(self, request):
        today = timezone.now().date()
        user = request.user
        # Booking stats
        total_bookings = Booking.objects.count()
        new_bookings = Booking.objects.filter(created_at__date=today).count()
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()
        upcoming = Booking.objects.filter(check_in_date__gte=today).count()
        recent_bookings = Booking.objects.order_by('-created_at')[:8]

        # Core entities
        hotels_count = Hotel.objects.count()
        rooms_count = Room.objects.count()
        extras_count = Extra.objects.count()
        roomtypes_count = RoomType.objects.count()
        roomamenities_count = RoomAmenity.objects.count()
        roomimages_count = RoomImage.objects.count()
        roomtypeamenities_count = RoomTypeAmenity.objects.count()
        seasonalpricing_count = SeasonalPricing.objects.count()

        # Offers related
        offers_count = Offer.objects.count()
        active_offers_count = Offer.objects.filter(is_active=True).count()
        featured_offers_count = Offer.objects.filter(is_featured=True).count()
        offer_categories_count = OfferCategory.objects.count()
        offer_highlights_count = OfferHighlight.objects.count()
        offer_images_count = OfferImage.objects.count()

        # Payments related
        total_payments = Payment.objects.count()
        completed_payments = Payment.objects.filter(status='completed').count()
        pending_payments = Payment.objects.filter(status='pending').count()
        failed_payments = Payment.objects.filter(status='failed').count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        recent_payments = Payment.objects.select_related('booking').order_by('-created_at')[:10]

        # Bookings related
        # Note: Old complex booking models simplified to single Booking model
        # bookingextras_count = BookingExtra.objects.count()
        # bookingguests_count = BookingGuest.objects.count()
        # bookinghistories_count = BookingHistory.objects.count()

        # Permissions for quick links
        perms = {
            'hotel': {
                'add': user.has_perm('core.add_hotel'),
                'view': user.has_perm('core.view_hotel'),
                'change': user.has_perm('core.change_hotel'),
            },
            'room': {
                'add': user.has_perm('core.add_room'),
                'view': user.has_perm('core.view_room'),
                'change': user.has_perm('core.change_room'),
            },
            'roomtype': {
                'add': user.has_perm('core.add_roomtype'),
                'view': user.has_perm('core.view_roomtype'),
                'change': user.has_perm('core.change_roomtype'),
            },
            'extra': {
                'add': user.has_perm('core.add_extra'),
                'view': user.has_perm('core.view_extra'),
                'change': user.has_perm('core.change_extra'),
            },
            'roomamenity': {
                'add': user.has_perm('core.add_roomamenity'),
                'view': user.has_perm('core.view_roomamenity'),
                'change': user.has_perm('core.change_roomamenity'),
            },
            'roomimage': {
                'add': user.has_perm('core.add_roomimage'),
                'view': user.has_perm('core.view_roomimage'),
                'change': user.has_perm('core.change_roomimage'),
            },
            'roomtypeamenity': {
                'add': user.has_perm('core.add_roomtypeamenity'),
                'view': user.has_perm('core.view_roomtypeamenity'),
                'change': user.has_perm('core.change_roomtypeamenity'),
            },
            'seasonalpricing': {
                'add': user.has_perm('core.add_seasonalpricing'),
                'view': user.has_perm('core.view_seasonalpricing'),
                'change': user.has_perm('core.change_seasonalpricing'),
            },
            'booking': {
                'add': user.has_perm('bookings.add_booking'),
                'view': user.has_perm('bookings.view_booking'),
                'change': user.has_perm('bookings.change_booking'),
            },
            'offer': {
                'add': user.has_perm('offers.add_offer'),
                'view': user.has_perm('offers.view_offer'),
                'change': user.has_perm('offers.change_offer'),
                'delete': user.has_perm('offers.delete_offer'),
            },
            'offercategory': {
                'add': user.has_perm('offers.add_offercategory'),
                'view': user.has_perm('offers.view_offercategory'),
                'change': user.has_perm('offers.change_offercategory'),
                'delete': user.has_perm('offers.delete_offercategory'),
            },
            'offerhighlight': {
                'add': user.has_perm('offers.add_offerhighlight'),
                'view': user.has_perm('offers.view_offerhighlight'),
                'change': user.has_perm('offers.change_offerhighlight'),
                'delete': user.has_perm('offers.delete_offerhighlight'),
            },
            'offerimage': {
                'add': user.has_perm('offers.add_offerimage'),
                'view': user.has_perm('offers.view_offerimage'),
                'change': user.has_perm('offers.change_offerimage'),
                'delete': user.has_perm('offers.delete_offerimage'),
            },
            'payment': {
                'add': user.has_perm('payments.add_payment'),
                'view': user.has_perm('payments.view_payment'),
                'change': user.has_perm('payments.change_payment'),
                'delete': user.has_perm('payments.delete_payment'),
            },
        }

        context = {
            'total_bookings': total_bookings,
            'new_bookings': new_bookings,
            'confirmed_bookings': confirmed_bookings,
            'upcoming': upcoming,
            'recent_bookings': recent_bookings,
            'hotels_count': hotels_count,
            'rooms_count': rooms_count,
            'extras_count': extras_count,
            'roomtypes_count': roomtypes_count,
            'roomamenities_count': roomamenities_count,
            'roomimages_count': roomimages_count,
            'roomtypeamenities_count': roomtypeamenities_count,
            'seasonalpricing_count': seasonalpricing_count,
            'offers_count': offers_count,
            'active_offers_count': active_offers_count,
            'featured_offers_count': featured_offers_count,
            'offer_categories_count': offer_categories_count,
            'offer_highlights_count': offer_highlights_count,
            'offer_images_count': offer_images_count,
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'total_revenue': total_revenue,
            'recent_payments': recent_payments,
            # Old booking related counts removed - using simplified booking model
            # 'bookingextras_count': bookingextras_count,
            # 'bookingguests_count': bookingguests_count,
            # 'bookinghistories_count': bookinghistories_count,
            'perms': perms,
            'request': request,
        }
        return render(request, 'manager/dashboard.html', context)
    

class ModelContextMixin:
    """Provide safe template-friendly model metadata in the context to avoid accessing _meta from templates."""
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = getattr(self, 'model', None)
        if model is not None:
            ctx['model_name'] = model._meta.model_name
            ctx['model_verbose_name'] = model._meta.verbose_name
            ctx['model_verbose_name_plural'] = model._meta.verbose_name_plural
            # expose field names and verbose names as plain dicts (no leading-underscore access in templates)
            ctx['model_fields'] = [
                {'name': f.name, 'verbose_name': str(getattr(f, 'verbose_name', f.name))}
                for f in model._meta.fields
            ]
        return ctx


class BaseListView(ModelContextMixin, ManagerRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 20

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to view this page.')
        return redirect('manager:dashboard')
    
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            filters = Q()
            field_names = [f.name for f in self.model._meta.fields]
            if 'name' in field_names:
                filters |= Q(name__icontains=q)
            if 'room_number' in field_names:
                filters |= Q(room_number__icontains=q)
            if 'booking_id' in field_names:
                filters |= Q(booking_id__icontains=q)
            if 'guest_first_name' in field_names:
                filters |= Q(guest_first_name__icontains=q)
            if 'guest_last_name' in field_names:
                filters |= Q(guest_last_name__icontains=q)
            if filters:
                qs = qs.filter(filters)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model_name = self.model._meta.model_name
        ctx['model_name'] = model_name
        ctx['add_url_name'] = f'manager:{model_name}_add'
        
        # Only set detail_url_name for models that have detail views
        # Currently only Booking has a detail view
        if model_name == 'booking':
            ctx['detail_url_name'] = f'manager:{model_name}_detail'
        else:
            ctx['detail_url_name'] = None
            
        ctx['model_verbose_name'] = self.model._meta.verbose_name
        ctx['model_verbose_name_plural'] = self.model._meta.verbose_name_plural
        # Permission flags for UI
        user = getattr(self.request, 'user', None)
        app_label = self.model._meta.app_label
        ctx['can_add'] = user.has_perm(f'{app_label}.add_{model_name}') if user else False
        ctx['can_change'] = user.has_perm(f'{app_label}.change_{model_name}') if user else False
        ctx['can_delete'] = user.has_perm(f'{app_label}.delete_{model_name}') if user else False
        ctx['can_view'] = user.has_perm(f'{app_label}.view_{model_name}') if user else False
        return ctx


class BulkActionMixin:
    """Mixin to provide bulk-delete and export endpoints for list views."""
    def post(self, request, *args, **kwargs):
        # handle bulk delete
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
            ids = data.get('ids', [])
        except Exception:
            ids = request.POST.getlist('ids')

        if not ids:
            return HttpResponse(status=400)

        qs = self.model.objects.filter(pk__in=ids)
        # permission check
        if not request.user.has_perm(f'{self.model._meta.app_label}.delete_{self.model._meta.model_name}'):
            return HttpResponse(status=403)

        qs.delete()
        return HttpResponse(status=204)

    def get(self, request, *args, **kwargs):
        # support export via ?id=1&id=2 or full export via path 'export/'
        if request.path.endswith('export/') or request.GET.get('export') is not None:
            ids = request.GET.getlist('id')
            if ids:
                qs = self.model.objects.filter(pk__in=ids)
            else:
                qs = self.model.objects.all()
            # fields: simple mapping to field names
            fields = [f.name for f in self.model._meta.fields]
            return export_as_csv(qs, fields)
        return super().get(request, *args, **kwargs)


class BaseCreateView(ModelContextMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Created successfully.')
            return response
        except Exception as e:
            # Handle database constraint violations gracefully
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                error_message = str(e)
                if 'unique constraint' in error_message.lower() or 'already exists' in error_message.lower():
                    form.add_error(None, 'A record with this information already exists. Please check your input.')
                else:
                    form.add_error(None, 'There was an error saving your data. Please try again.')
            else:
                form.add_error(None, f'An unexpected error occurred: {str(e)}')
            return self.form_invalid(form)


class BaseUpdateView(ModelContextMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Updated successfully.')
            return response
        except Exception as e:
            # Handle database constraint violations gracefully
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                error_message = str(e)
                if 'unique constraint' in error_message.lower() or 'already exists' in error_message.lower():
                    form.add_error(None, 'A record with this information already exists. Please check your input.')
                else:
                    form.add_error(None, 'There was an error saving your data. Please try again.')
            else:
                form.add_error(None, f'An unexpected error occurred: {str(e)}')
            return self.form_invalid(form)

    def get_success_url(self):
        # Default success URL to the list view of the model
        model_name = self.model._meta.model_name
        return reverse_lazy(f'manager:{model_name}s')


class BaseDeleteView(ModelContextMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Hotels
class HotelListView(BulkActionMixin, BaseListView):
    model = Hotel
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_hotel'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.user_type == 'staff':
            ctx['can_add'] = False
            ctx['can_delete'] = False
        return ctx



class RoomTypeListView(BulkActionMixin, BaseListView):
    model = RoomType
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_roomtype'


class RoomTypeCreateView(BaseCreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomtypes')
    permission_required = 'core.add_roomtype'


class RoomTypeUpdateView(BaseUpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomtypes')
    permission_required = 'core.change_roomtype'


class RoomTypeDeleteView(BaseDeleteView):
    model = RoomType
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:roomtypes')
    permission_required = 'core.delete_roomtype'


class RoomListView(BulkActionMixin, BaseListView):
    model = Room
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_room'


class RoomCreateView(BaseCreateView):
    model = Room
    form_class = RoomForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:rooms')
    permission_required = 'core.add_room'


class RoomUpdateView(BaseUpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:rooms')
    permission_required = 'core.change_room'


class RoomDeleteView(BaseDeleteView):
    model = Room
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:rooms')
    permission_required = 'core.delete_room'


class ExtraListView(BulkActionMixin, BaseListView):
    model = Extra
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_extra'


class ExtraCreateView(BaseCreateView):
    model = Extra
    form_class = ExtraForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:extras')
    permission_required = 'core.add_extra'


class ExtraUpdateView(BaseUpdateView):
    model = Extra
    form_class = ExtraForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:extras')
    permission_required = 'core.change_extra'


class ExtraDeleteView(BaseDeleteView):
    model = Extra
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:extras')
    permission_required = 'core.delete_extra'


def export_as_csv(queryset, fields):
    """Utility to export queryset to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in queryset:
        row = [getattr(obj, f) for f in fields]
        writer.writerow(row)
    return response


# Booking extras, guests, history - COMMENTED OUT
# These old complex booking views are no longer needed after simplification to single Booking model

# class BookingExtraListView(BulkActionMixin, BaseListView):
#     model = BookingExtra
#     template_name = 'manager/list.html'
#     context_object_name = 'objects'
#     permission_required = 'bookings.view_bookingextra'


# class BookingExtraCreateView(BaseCreateView):
#     model = BookingExtra
#     form_class = BookingExtraForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookingextras')
#     permission_required = 'bookings.add_bookingextra'


# class BookingExtraUpdateView(BaseUpdateView):
#     model = BookingExtra
#     form_class = BookingExtraForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookingextras')
#     permission_required = 'bookings.change_bookingextra'


# class BookingExtraDeleteView(BaseDeleteView):
#     model = BookingExtra
#     template_name = 'manager/confirm_delete.html'
#     success_url = reverse_lazy('manager:bookingextras')
#     permission_required = 'bookings.delete_bookingextra'


# class BookingExtraExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = 'bookings.view_bookingextra'
#     def get(self, request, *args, **kwargs):
#         qs = BookingExtra.objects.all()
#         fields = ['id', 'booking_id', 'extra_id', 'quantity', 'unit_price', 'total_price']
#         return export_as_csv(qs, fields)


# class BookingGuestListView(BulkActionMixin, BaseListView):
#     model = BookingGuest
#     template_name = 'manager/list.html'
#     context_object_name = 'objects'
#     permission_required = 'bookings.view_bookingguest'


# class BookingGuestCreateView(BaseCreateView):
#     model = BookingGuest
#     form_class = BookingGuestForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookingguests')
#     permission_required = 'bookings.add_bookingguest'


# class BookingGuestUpdateView(BaseUpdateView):
#     model = BookingGuest
#     form_class = BookingGuestForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookingguests')
#     permission_required = 'bookings.change_bookingguest'


# class BookingGuestDeleteView(BaseDeleteView):
#     model = BookingGuest
#     template_name = 'manager/confirm_delete.html'
#     success_url = reverse_lazy('manager:bookingguests')
#     permission_required = 'bookings.delete_bookingguest'


# class BookingHistoryListView(BulkActionMixin, BaseListView):
#     model = BookingHistory
#     template_name = 'manager/list.html'
#     context_object_name = 'objects'
#     permission_required = 'bookings.view_bookinghistory'


# class BookingHistoryCreateView(BaseCreateView):
#     model = BookingHistory
#     form_class = BookingHistoryForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookinghistories')
#     permission_required = 'bookings.add_bookinghistory'


# class BookingHistoryUpdateView(BaseUpdateView):
#     model = BookingHistory
#     form_class = BookingHistoryForm
#     template_name = 'manager/form.html'
#     success_url = reverse_lazy('manager:bookinghistories')
#     permission_required = 'bookings.change_bookinghistory'


# class BookingHistoryDeleteView(BaseDeleteView):
#     model = BookingHistory
#     template_name = 'manager/confirm_delete.html'
#     success_url = reverse_lazy('manager:bookinghistories')
#     permission_required = 'bookings.delete_bookinghistory'


# Room amenities
class RoomAmenityListView(BulkActionMixin, BaseListView):
    model = RoomAmenity
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_roomamenity'


class RoomAmenityCreateView(BaseCreateView):
    model = RoomAmenity
    form_class = RoomAmenityForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomamenities')
    permission_required = 'core.add_roomamenity'


class RoomAmenityUpdateView(BaseUpdateView):
    model = RoomAmenity
    form_class = RoomAmenityForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomamenities')
    permission_required = 'core.change_roomamenity'


class RoomAmenityDeleteView(BaseDeleteView):
    model = RoomAmenity
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:roomamenities')
    permission_required = 'core.delete_roomamenity'


# Room images
class RoomImageListView(BulkActionMixin, BaseListView):
    model = RoomImage
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_roomimage'


class RoomImageCreateView(BaseCreateView):
    model = RoomImage
    form_class = RoomImageForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomimages')
    permission_required = 'core.add_roomimage'


class RoomImageUpdateView(BaseUpdateView):
    model = RoomImage
    form_class = RoomImageForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomimages')
    permission_required = 'core.change_roomimage'


class RoomImageDeleteView(BaseDeleteView):
    model = RoomImage
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:roomimages')
    permission_required = 'core.delete_roomimage'


# RoomTypeAmenity
class RoomTypeAmenityListView(BulkActionMixin, BaseListView):
    model = RoomTypeAmenity
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_roomtypeamenity'


class RoomTypeAmenityCreateView(BaseCreateView):
    model = RoomTypeAmenity
    form_class = RoomTypeAmenityForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomtypeamenities')
    permission_required = 'core.add_roomtypeamenity'


class RoomTypeAmenityUpdateView(BaseUpdateView):
    model = RoomTypeAmenity
    form_class = RoomTypeAmenityForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:roomtypeamenities')
    permission_required = 'core.change_roomtypeamenity'


class RoomTypeAmenityDeleteView(BaseDeleteView):
    model = RoomTypeAmenity
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:roomtypeamenities')
    permission_required = 'core.delete_roomtypeamenity'


# Seasonal pricing
class SeasonalPricingListView(BulkActionMixin, BaseListView):
    model = SeasonalPricing
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'core.view_seasonalpricing'


class SeasonalPricingCreateView(BaseCreateView):
    model = SeasonalPricing
    form_class = SeasonalPricingForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:seasonalpricing')
    permission_required = 'core.add_seasonalpricing'


class SeasonalPricingUpdateView(BaseUpdateView):
    model = SeasonalPricing
    form_class = SeasonalPricingForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:seasonalpricing')
    permission_required = 'core.change_seasonalpricing'


class SeasonalPricingDeleteView(BaseDeleteView):
    model = SeasonalPricing
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:seasonalpricing')
    permission_required = 'core.delete_seasonalpricing'



class HotelCreateView(BaseCreateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:hotels')
    permission_required = 'core.add_hotel'

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type == 'staff':
            messages.error(request, 'You do not have permission to add hotels.')
            return redirect('manager:hotels')
        return super().dispatch(request, *args, **kwargs)


class HotelUpdateView(BaseUpdateView):
    model = Hotel
    form_class = HotelForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:hotels')
    permission_required = 'core.change_hotel'


class HotelDeleteView(BaseDeleteView):
    model = Hotel
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:hotels')
    permission_required = 'core.delete_hotel'

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type == 'staff':
            messages.error(request, 'You do not have permission to delete hotels.')
            return redirect('manager:hotels')
        return super().dispatch(request, *args, **kwargs)


# Bookings (basic list + detail)
class BookingListView(BulkActionMixin, BaseListView):
    model = Booking
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'bookings.view_booking'
    
    def get_queryset(self):
        """Optimize queryset with related data"""
        return super().get_queryset().select_related(
            'hotel', 'room', 'room__room_type', 'user'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add booking statistics
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        confirmed_bookings = Booking.objects.filter(status='confirmed').count()
        cancelled_bookings = Booking.objects.filter(status='cancelled').count()
        
        context.update({
            'stats': {
                'total': total_bookings,
                'pending': pending_bookings,
                'confirmed': confirmed_bookings,
                'cancelled': cancelled_bookings,
            },
            'status_choices': Booking.STATUS_CHOICES,
            'payment_status_choices': Booking.PAYMENT_STATUS_CHOICES,
        })
        
        return context


class BookingDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Booking
    template_name = 'manager/booking_detail.html'
    context_object_name = 'object'
    permission_required = 'bookings.view_booking'
    
    def get_object(self, queryset=None):
        """Get object with related data"""
        return super().get_object(
            queryset=self.get_queryset().select_related(
                'hotel', 'room', 'room__room_type', 'user'
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Add calculated fields for display
        context.update({
            'guest_full_name': booking.guest_full_name(),
            'guest_address_formatted': booking.guest_address_formatted(),
            'total_guests': booking.total_guests(),
            'tax_percentage': booking.tax_percentage(),
            'discount_percentage': booking.discount_percentage(),
            'can_be_cancelled': booking.can_be_cancelled(),
        })
        
        # Add permission context
        user = self.request.user
        context['can_change'] = user.has_perm('bookings.change_booking')
        context['can_delete'] = user.has_perm('bookings.delete_booking')
        
        return context


class BookingCreateView(BaseCreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'manager/form.html'
    permission_required = 'bookings.add_booking'
    
    def get_success_url(self):
        """Redirect to the created booking's detail page"""
        return reverse_lazy('manager:booking_detail', kwargs={'pk': self.object.pk})


class BookingUpdateView(BaseUpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'manager/form.html'
    permission_required = 'bookings.change_booking'
    
    def get_success_url(self):
        """Redirect to the updated booking's detail page"""
        return reverse_lazy('manager:booking_detail', kwargs={'pk': self.object.pk})


class BookingDeleteView(BaseDeleteView):
    model = Booking
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:bookings')
    permission_required = 'bookings.delete_booking'


class BookingExportView(ManagerRequiredMixin, View):
    """Export bookings to CSV"""
    
    def get(self, request):
        # Create HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings_export.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Booking ID', 'Guest Name', 'Email', 'Phone', 'Country',
            'Hotel', 'Room', 'Check-in Date', 'Check-out Date', 'Nights',
            'Adults', 'Children', 'Total Guests', 'Room Rate', 'Tax Amount',
            'Discount Amount', 'Total Amount', 'Status', 'Payment Status',
            'Special Requests', 'Created Date'
        ])
        
        # Get all bookings with related data
        bookings = Booking.objects.select_related(
            'hotel', 'room', 'room__room_type', 'user'
        ).order_by('-created_at')
        
        # Apply filters if provided
        status = request.GET.get('status')
        payment_status = request.GET.get('payment_status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if status:
            bookings = bookings.filter(status=status)
        if payment_status:
            bookings = bookings.filter(payment_status=payment_status)
        if date_from:
            bookings = bookings.filter(check_in_date__gte=date_from)
        if date_to:
            bookings = bookings.filter(check_out_date__lte=date_to)
        
        # Write data rows
        for booking in bookings:
            writer.writerow([
                booking.booking_id,
                booking.guest_full_name(),
                booking.guest_email,
                booking.guest_phone,
                booking.guest_country,
                booking.hotel.name,
                f"{booking.room.room_type.name} #{booking.room.room_number}",
                booking.check_in_date.strftime('%Y-%m-%d'),
                booking.check_out_date.strftime('%Y-%m-%d'),
                booking.nights,
                booking.adults,
                booking.children,
                booking.total_guests(),
                booking.room_rate,
                booking.tax_amount,
                booking.discount_amount,
                booking.total_amount,
                booking.get_status_display(),
                booking.get_payment_status_display(),
                booking.special_requests or '',
                booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


class GlobalSearchView(ManagerRequiredMixin, View):
    """Global search view that searches across multiple models with pagination"""
    
    def get(self, request):
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        import logging
        
        logger = logging.getLogger(__name__)
        query = request.GET.get('q', '').strip()
        page = request.GET.get('page', 1)
        
        if not query:
            return redirect('manager:dashboard')
        
        results = {}
        total_results = 0
        
        try:
            # Search Bookings
            if request.user.has_perm('bookings.view_booking'):
                try:
                    bookings = Booking.objects.filter(
                        Q(booking_id__icontains=query) |
                        Q(guest_first_name__icontains=query) |
                        Q(guest_last_name__icontains=query) |
                        Q(guest_email__icontains=query) |
                        Q(guest_phone__icontains=query) |
                        Q(hotel__name__icontains=query) |
                        Q(room__room_number__icontains=query)
                    ).select_related('hotel', 'room', 'room__room_type').order_by('-created_at')
                    if bookings.exists():
                        results['bookings'] = {
                            'objects': bookings,
                            'count': bookings.count(),
                            'verbose_name': Booking._meta.verbose_name_plural,
                            'url_name': 'manager:bookings'
                        }
                        total_results += bookings.count()
                except Exception as e:
                    # Log the error but don't crash the search
                    print(f"Error searching bookings: {e}")
            
            # Search Hotels
            if request.user.has_perm('core.view_hotel'):
                try:
                    hotels = Hotel.objects.filter(
                        Q(name__icontains=query) |
                        Q(address_line_1__icontains=query) |
                        Q(address_line_2__icontains=query) |
                        Q(city__icontains=query)
                    )
                    if hotels.exists():
                        results['hotels'] = {
                            'objects': hotels,
                            'count': hotels.count(),
                            'verbose_name': Hotel._meta.verbose_name_plural,
                            'url_name': 'manager:hotels'
                        }
                        total_results += hotels.count()
                except Exception as e:
                    print(f"Error searching hotels: {e}")
            
            # Search Rooms
            if request.user.has_perm('core.view_room'):
                try:
                    rooms = Room.objects.filter(
                        Q(room_number__icontains=query) |
                        Q(room_type__name__icontains=query)
                    )
                    if rooms.exists():
                        results['rooms'] = {
                            'objects': rooms,
                            'count': rooms.count(),
                            'verbose_name': Room._meta.verbose_name_plural,
                            'url_name': 'manager:rooms'
                        }
                        total_results += rooms.count()
                except Exception as e:
                    print(f"Error searching rooms: {e}")
            
            # Search Room Types
            if request.user.has_perm('core.view_roomtype'):
                try:
                    room_types = RoomType.objects.filter(
                        Q(name__icontains=query) |
                        Q(description__icontains=query)
                    )
                    if room_types.exists():
                        results['room_types'] = {
                            'objects': room_types,
                            'count': room_types.count(),
                            'verbose_name': RoomType._meta.verbose_name_plural,
                            'url_name': 'manager:roomtypes'
                        }
                        total_results += room_types.count()
                except Exception as e:
                    print(f"Error searching room types: {e}")
            
            # Search Extras
            if request.user.has_perm('core.view_extra'):
                try:
                    extras = Extra.objects.filter(
                        Q(name__icontains=query) |
                        Q(description__icontains=query)
                    )
                    if extras.exists():
                        results['extras'] = {
                            'objects': extras,
                            'count': extras.count(),
                            'verbose_name': Extra._meta.verbose_name_plural,
                            'url_name': 'manager:extras'
                        }
                        total_results += extras.count()
                except Exception as e:
                    print(f"Error searching extras: {e}")
            
            # Search Offers
            if request.user.has_perm('offers.view_offer'):
                try:
                    offers = Offer.objects.filter(
                        Q(name__icontains=query) |
                        Q(description__icontains=query) |
                        Q(hotel__name__icontains=query)
                    )
                    if offers.exists():
                        results['offers'] = {
                            'objects': offers,
                            'count': offers.count(),
                            'verbose_name': Offer._meta.verbose_name_plural,
                            'url_name': 'manager:offers'
                        }
                        total_results += offers.count()
                except Exception as e:
                    print(f"Error searching offers: {e}")
        
        except Exception as e:
            # General error handling for the entire search process
            messages.error(request, 'An error occurred during search. Please try again.')
            print(f"General search error: {e}")
            return render(request, 'manager/search_results.html', {
                'query': query,
                'results': {},
                'total_results': 0,
                'error': True
            })
        
        context = {
            'query': query,
            'results': results,
            'total_results': total_results
        }
        
        return render(request, 'manager/search_results.html', context)


# Offer Management Views
class OfferListView(BulkActionMixin, BaseListView):
    """List all offers with filtering and search"""
    model = Offer
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'offers.view_offer'
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Additional filters for offers
        hotel_id = self.request.GET.get('hotel')
        if hotel_id:
            qs = qs.filter(hotel_id=hotel_id)
        
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        return qs.select_related('hotel', 'category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hotels'] = Hotel.objects.filter(is_active=True)
        context['categories'] = OfferCategory.objects.filter(is_active=True)
        return context


class OfferCreateView(BaseCreateView):
    """Create a new offer"""
    model = Offer
    form_class = OfferForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:offers')
    permission_required = 'offers.add_offer'


class OfferUpdateView(BaseUpdateView):
    """Update an existing offer"""
    model = Offer
    form_class = OfferForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:offers')
    permission_required = 'offers.change_offer'


class OfferDeleteView(BaseDeleteView):
    """Delete an offer"""
    model = Offer
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:offers')
    permission_required = 'offers.delete_offer'


class OfferDetailView(ModelContextMixin, ManagerRequiredMixin, PermissionRequiredMixin, DetailView):
    """View offer details"""
    model = Offer
    template_name = 'manager/detail.html'
    context_object_name = 'object'
    permission_required = 'offers.view_offer'


# Offer Categories
class OfferCategoryListView(BulkActionMixin, BaseListView):
    """List all offer categories"""
    model = OfferCategory
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'offers.view_offercategory'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Override add_url_name to match urls.py name
        ctx['add_url_name'] = 'manager:offer_category_add'
        # Override model_name to generate correct edit/delete URLs
        ctx['model_name'] = 'offer_category'
        return ctx


class OfferCategoryCreateView(BaseCreateView):
    """Create a new offer category"""
    model = OfferCategory
    form_class = OfferCategoryForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:offer_categories')
    permission_required = 'offers.add_offercategory'


class OfferCategoryUpdateView(BaseUpdateView):
    """Update an existing offer category"""
    model = OfferCategory
    form_class = OfferCategoryForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:offer_categories')
    permission_required = 'offers.change_offercategory'


class OfferCategoryDeleteView(BaseDeleteView):
    """Delete an offer category"""
    model = OfferCategory
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:offer_categories')
    permission_required = 'offers.delete_offercategory'


# Offer Highlights
class OfferHighlightListView(BulkActionMixin, BaseListView):
    """List offer highlights for a specific offer"""
    model = OfferHighlight
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'offers.view_offerhighlight'

    def get_queryset(self):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            return OfferHighlight.objects.filter(offer_id=offer_id).order_by('order')
        return OfferHighlight.objects.all().order_by('offer__name', 'order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            context['offer'] = Offer.objects.get(id=offer_id)
            context['add_url_name'] = 'manager:offer_highlight_add'
        else:
            # Global list view
            context['add_url_name'] = 'manager:offer_highlight_add_global'
        
        # Override model_name to generate correct edit/delete URLs
        context['model_name'] = 'offer_highlight'
        return context


class OfferHighlightCreateView(BaseCreateView):
    """Create a new offer highlight"""
    model = OfferHighlight
    form_class = OfferHighlightForm
    template_name = 'manager/form.html'
    permission_required = 'offers.add_offerhighlight'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['offer_id'] = self.kwargs.get('offer_id')
        return kwargs
    
    def get_success_url(self):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            return reverse_lazy('manager:offer_highlights', kwargs={'offer_id': offer_id})
        return reverse_lazy('manager:offer_highlights_all')
    
    def form_valid(self, form):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            # Set the offer instance for the form
            from offers.models import Offer
            form.instance.offer = Offer.objects.get(id=offer_id)
        return super().form_valid(form)


class OfferHighlightUpdateView(BaseUpdateView):
    """Update an existing offer highlight"""
    model = OfferHighlight
    form_class = OfferHighlightForm
    template_name = 'manager/form.html'
    permission_required = 'offers.change_offerhighlight'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['offer_id'] = self.get_object().offer.id
        return kwargs
    
    def get_success_url(self):
        # Use the object's offer_id directly instead of relying on HTTP_REFERER (security fix)
        highlight = self.get_object()
        return reverse_lazy('manager:offer_highlights', kwargs={'offer_id': highlight.offer.id})


class OfferHighlightDeleteView(BaseDeleteView):
    """Delete an offer highlight"""
    model = OfferHighlight
    template_name = 'manager/confirm_delete.html'
    permission_required = 'offers.delete_offerhighlight'
    
    def get_success_url(self):
        # Use the object's offer_id directly instead of relying on HTTP_REFERER (security fix)
        highlight = self.get_object()
        return reverse_lazy('manager:offer_highlights', kwargs={'offer_id': highlight.offer.id})


# Offer Images
class OfferImageListView(BulkActionMixin, BaseListView):
    """List offer images for a specific offer"""
    model = OfferImage
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'offers.view_offerimage'

    def get_queryset(self):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            return OfferImage.objects.filter(offer_id=offer_id).order_by('order')
        return OfferImage.objects.all().order_by('offer__name', 'order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            context['offer'] = Offer.objects.get(id=offer_id)
            context['add_url_name'] = 'manager:offer_image_add'
        else:
            # Global list view
            context['add_url_name'] = 'manager:offer_image_add_global'
        
        # Override model_name to generate correct edit/delete URLs
        context['model_name'] = 'offer_image'
        return context


class OfferImageCreateView(BaseCreateView):
    """Create a new offer image"""
    model = OfferImage
    form_class = OfferImageForm
    template_name = 'manager/form.html'
    permission_required = 'offers.add_offerimage'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['offer_id'] = self.kwargs.get('offer_id')
        return kwargs
    
    def get_success_url(self):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            return reverse_lazy('manager:offer_images', kwargs={'offer_id': offer_id})
        return reverse_lazy('manager:offer_images_all')
    
    def form_valid(self, form):
        offer_id = self.kwargs.get('offer_id')
        if offer_id:
            form.instance.offer_id = offer_id
        return super().form_valid(form)


class OfferImageUpdateView(BaseUpdateView):
    """Update an existing offer image"""
    model = OfferImage
    form_class = OfferImageForm
    template_name = 'manager/form.html'
    permission_required = 'offers.change_offerimage'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['offer_id'] = self.get_object().offer.id
        return kwargs
    
    def get_success_url(self):
        # Use the object's offer_id directly instead of relying on HTTP_REFERER (security fix)
        image = self.get_object()
        return reverse_lazy('manager:offer_images', kwargs={'offer_id': image.offer.id})


class OfferImageDeleteView(BaseDeleteView):
    """Delete an offer image"""
    model = OfferImage
    template_name = 'manager/confirm_delete.html'
    permission_required = 'offers.delete_offerimage'
    
    def get_success_url(self):
        # Use the object's offer_id directly instead of relying on HTTP_REFERER (security fix)
        image = self.get_object()
        return reverse_lazy('manager:offer_images', kwargs={'offer_id': image.offer.id})


# ============================================================================
# NEW FEATURES: OCCUPANCY CALENDAR, BULK STATUS, HISTORY, REPORTS, EMAILS,
# REFUNDS, MANAGER ROLES
# ============================================================================


# FEATURE 1: OCCUPANCY CALENDAR VIEW
class OccupancyCalendarView(ManagerRequiredMixin, View):
    """
    Display room occupancy calendar for a selected hotel and month.
    Shows which rooms are booked on each day.
    """
    
    def get(self, request):
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
        hotel_id = request.GET.get('hotel')
        
        # Get hotel data
        hotels = Hotel.objects.all()
        selected_hotel = None
        if hotel_id:
            selected_hotel = Hotel.objects.filter(id=hotel_id).first()
        
        # Get occupancy data for the month
        occupancy_calendar = []
        total_rooms = 0
        booked_nights = 0
        
        if selected_hotel:
            rooms = selected_hotel.room_set.all()
            total_rooms = rooms.count()
            
            # Build calendar
            cal = monthcalendar(year, month)
            for week in cal:
                week_data = []
                for day in week:
                    if day == 0:
                        week_data.append(None)
                    else:
                        date = datetime(year, month, day).date()
                        # Count bookings for this date
                        bookings_count = Booking.objects.filter(
                            hotel=selected_hotel,
                            check_in_date__lte=date,
                            check_out_date__gt=date,
                            status__in=['pending', 'confirmed']
                        ).count()
                        
                        occupancy_rate = (bookings_count / total_rooms * 100) if total_rooms > 0 else 0
                        week_data.append({
                            'day': day,
                            'date': date,
                            'booked_rooms': bookings_count,
                            'total_rooms': total_rooms,
                            'occupancy_rate': f"{occupancy_rate:.0f}%"
                        })
                occupancy_calendar.append(week_data)
            
            # Calculate month stats
            month_start = datetime(year, month, 1).date()
            month_end = datetime(year, month, 1) + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            month_end = month_end.date()
            
            month_bookings = Booking.objects.filter(
                hotel=selected_hotel,
                check_in_date__lte=month_end,
                check_out_date__gte=month_start,
                status__in=['pending', 'confirmed']
            )
            
            booked_nights = sum([
                min(b.check_out_date, month_end) - max(b.check_in_date, month_start)
                for b in month_bookings
            ]).days
        
        context = {
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B %Y'),
            'hotels': hotels,
            'selected_hotel': selected_hotel,
            'occupancy_calendar': occupancy_calendar,
            'total_rooms': total_rooms,
            'booked_nights': booked_nights,
        }
        return render(request, 'manager/occupancy_calendar.html', context)


# FEATURE 2: BULK BOOKING STATUS UPDATES
class BulkBookingStatusUpdateView(ManagerRequiredMixin, View):
    """
    Update status of multiple bookings in bulk (e.g., change 10 pending → confirmed at once).
    Includes audit trail for compliance.
    """
    
    def get(self, request):
        form = BulkBookingStatusForm()
        bookings_qs = Booking.objects.all().select_related('hotel', 'room')
        
        # Filter by status if specified
        status = request.GET.get('status')
        if status:
            bookings_qs = bookings_qs.filter(status=status)
        
        context = {
            'form': form,
            'bookings': bookings_qs[:50],  # Show first 50 for selection
            'status_choices': Booking.STATUS_CHOICES,
        }
        return render(request, 'manager/bulk_booking_status.html', context)
    
    def post(self, request):
        form = BulkBookingStatusForm(request.POST)
        if form.is_valid():
            booking_ids = form.cleaned_data['booking_ids']
            new_status = form.cleaned_data['new_status']
            reason = form.cleaned_data['reason']
            
            # Validate booking IDs
            if isinstance(booking_ids, str):
                booking_ids = [int(id.strip()) for id in booking_ids.split(',') if id.strip()]
            
            bookings = Booking.objects.filter(id__in=booking_ids)
            updated_count = 0
            
            for booking in bookings:
                old_status = booking.status
                if old_status != new_status:
                    booking.status = new_status
                    booking.save(update_fields=['status'])
                    
                    # Log the change with audit trail
                    BookingAuditLog.objects.create(
                        booking=booking,
                        changed_by=request.user,
                        change_type='status_change',
                        old_value={'status': old_status},
                        new_value={'status': new_status},
                        reason=reason or 'Bulk status update',
                        ip_address=self.get_client_ip(request)
                    )
                    updated_count += 1
            
            messages.success(request, f'Successfully updated {updated_count} booking(s) to {new_status}')
            return redirect('manager:bookings')
        
        context = {'form': form}
        return render(request, 'manager/bulk_booking_status.html', context)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# FEATURE 3: BOOKING MODIFICATION HISTORY
class BookingHistoryView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Display complete audit trail of all changes made to a booking.
    Shows who changed what, when, and why.
    """
    
    model = Booking
    template_name = 'manager/booking_history.html'
    context_object_name = 'booking'
    permission_required = 'bookings.view_booking'
    
    def get_object(self, queryset=None):
        """Get booking with related data"""
        return super().get_object(
            queryset=self.get_queryset().select_related(
                'hotel', 'room', 'room__room_type', 'user'
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Get all audit logs for this booking
        audit_logs = booking.audit_logs.select_related('changed_by').order_by('-changed_at')
        
        context.update({
            'audit_logs': audit_logs,
            'log_count': audit_logs.count(),
            'guest_full_name': booking.guest_full_name(),
        })
        
        return context


# FEATURE 4: AUTOMATED EMAIL NOTIFICATIONS (Signal-based)
def send_booking_notification(booking, action, reason=''):
    """
    Send email notification to guest about booking status change.
    Called via signals when booking is created/updated.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    action_messages = {
        'created': f'Your booking at {booking.hotel.name} has been confirmed',
        'confirmed': f'Your booking {booking.booking_id} has been confirmed',
        'cancelled': f'Your booking {booking.booking_id} has been cancelled',
        'refunded': f'Refund processed for your booking {booking.booking_id}',
        'status_change': f'Your booking {booking.booking_id} status has been updated',
    }
    
    subject = action_messages.get(action, 'Booking Update')
    
    # Basic email content (can be enhanced with template)
    message = f"""
    Dear {booking.guest_full_name()},
    
    {subject}
    
    Booking Details:
    - Booking ID: {booking.booking_id}
    - Hotel: {booking.hotel.name}
    - Check-in: {booking.check_in_date}
    - Check-out: {booking.check_out_date}
    - Status: {booking.get_status_display()}
    - Total Amount: ${booking.total_amount}
    
    {f'Reason: {reason}' if reason else ''}
    
    If you have any questions, please contact our support team.
    
    Best regards,
    Hotel Booking System
    """
    
    try:
        send_mail(
            subject,
            message,
            'noreply@hotelbooking.com',
            [booking.guest_email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending email notification: {e}")


# FEATURE 5: REFUND MANAGEMENT UI
class BookingRefundListView(ManagerRequiredMixin, ListView):
    """
    List all refund requests with status tracking.
    """
    
    model = BookingRefund
    template_name = 'manager/booking_refund_list.html'
    context_object_name = 'refunds'
    paginate_by = 20
    permission_required = 'bookings.view_booking'
    
    def get_queryset(self):
        qs = BookingRefund.objects.select_related('booking__hotel', 'booking__room').order_by('-refund_requested_at')
        
        # Filter by status if specified
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(refund_status=status)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['refund_statuses'] = BookingRefund.REFUND_STATUS_CHOICES
        context['refund_methods'] = BookingRefund.REFUND_METHOD_CHOICES
        return context


class BookingRefundDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    View and manage refund details for a booking.
    """
    
    model = BookingRefund
    template_name = 'manager/booking_refund_detail.html'
    context_object_name = 'refund'
    permission_required = 'bookings.change_booking'
    
    def post(self, request, *args, **kwargs):
        """Process refund action"""
        refund = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve':
            refund.refund_status = 'processing'
            refund.save()
            messages.success(request, 'Refund marked as processing')
        elif action == 'complete':
            refund.refund_status = 'completed'
            refund.refund_processed_at = timezone.now()
            refund.booking.payment_status = 'refunded'
            refund.booking.save(update_fields=['payment_status'])
            refund.save()
            
            # Send email notification
            send_booking_notification(
                refund.booking,
                'refunded',
                f'Refund of ${refund.refund_amount} has been processed'
            )
            
            # Log audit trail
            BookingAuditLog.objects.create(
                booking=refund.booking,
                changed_by=request.user,
                change_type='refund_issued',
                reason=f'Refund of ${refund.refund_amount} approved',
            )
            
            messages.success(request, 'Refund completed and guest notified')
        elif action == 'reject':
            refund.refund_status = 'failed'
            refund.save()
            messages.info(request, 'Refund request rejected')
        
        return redirect('manager:booking_refund_detail', pk=refund.id)


class RefundPolicyView(ManagerRequiredMixin, UpdateView):
    """
    Configure refund policy for a hotel.
    """
    
    model = RefundPolicy
    form_class = RefundPolicyForm
    template_name = 'manager/refund_policy_form.html'
    permission_required = 'core.change_hotel'
    
    def get_object(self, queryset=None):
        """Get or create refund policy for hotel"""
        hotel_id = self.kwargs.get('hotel_id')
        hotel = Hotel.objects.get(id=hotel_id)
        policy, created = RefundPolicy.objects.get_or_create(hotel=hotel)
        return policy
    
    def get_success_url(self):
        return reverse_lazy('manager:hotels')


# FEATURE 6: REVENUE AND OCCUPANCY REPORTS
class RevenueReportView(ManagerRequiredMixin, View):
    """
    Generate revenue reports with monthly breakdown.
    Shows total revenue, average booking value, and trends.
    """
    
    def get(self, request):
        # Time period filters
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        hotel_id = request.GET.get('hotel')
        
        # Default to last 12 months
        if not date_from:
            date_from = timezone.now() - timedelta(days=365)
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        
        if not date_to:
            date_to = timezone.now().date()
        else:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Query bookings
        bookings = Booking.objects.filter(
            payment_status='paid',
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        if hotel_id:
            bookings = bookings.filter(hotel_id=hotel_id)
        
        # Calculate metrics
        total_revenue = bookings.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_bookings = bookings.count()
        avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
        
        # Monthly breakdown
        monthly_revenue = bookings.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total_amount'),
            booking_count=Count('id')
        ).order_by('month')
        
        # Revenue by hotel
        revenue_by_hotel = bookings.values('hotel__name').annotate(
            revenue=Sum('total_amount'),
            booking_count=Count('id')
        ).order_by('-revenue')
        
        # Revenue by room type
        revenue_by_room_type = bookings.values('room__room_type__name').annotate(
            revenue=Sum('total_amount'),
            booking_count=Count('id')
        ).order_by('-revenue')
        
        context = {
            'total_revenue': f"${total_revenue:,.2f}",
            'total_bookings': total_bookings,
            'avg_booking_value': f"${avg_booking_value:,.2f}",
            'monthly_revenue': list(monthly_revenue),
            'revenue_by_hotel': list(revenue_by_hotel),
            'revenue_by_room_type': list(revenue_by_room_type),
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'hotels': Hotel.objects.all(),
            'selected_hotel_id': hotel_id,
        }
        
        return render(request, 'manager/revenue_report.html', context)


class OccupancyReportView(ManagerRequiredMixin, View):
    """
    Generate occupancy reports showing room utilization rates.
    Shows occupancy %, average length of stay, and booking patterns.
    """
    
    def get(self, request):
        # Time period filters
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        hotel_id = request.GET.get('hotel')
        
        # Default to last 3 months
        if not date_from:
            date_from = timezone.now() - timedelta(days=90)
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        
        if not date_to:
            date_to = timezone.now().date()
        else:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Get period range
        period_days = (date_to - date_from).days or 1
        
        # Query data
        bookings = Booking.objects.filter(
            check_in_date__lte=date_to,
            check_out_date__gte=date_from,
            status__in=['confirmed', 'completed']
        )
        
        if hotel_id:
            bookings = bookings.filter(hotel_id=hotel_id)
        
        # Calculate occupancy metrics
        total_bookings = bookings.count()
        avg_stay_length = bookings.aggregate(
            avg_nights=Coalesce(F('nights'), 0, output_field=IntegerField())
        )['avg_nights'] if total_bookings > 0 else 0
        
        # Get hotel and room data
        if hotel_id:
            hotels_qs = Hotel.objects.filter(id=hotel_id)
        else:
            hotels_qs = Hotel.objects.all()
        
        # Occupancy by hotel
        occupancy_by_hotel = []
        for hotel in hotels_qs:
            total_rooms = hotel.room_set.count()
            hotel_bookings = bookings.filter(hotel=hotel)
            
            booked_nights = sum([
                min(b.check_out_date, date_to) - max(b.check_in_date, date_from)
                for b in hotel_bookings
            ]).days
            
            total_room_nights = total_rooms * period_days
            occupancy_rate = (booked_nights / total_room_nights * 100) if total_room_nights > 0 else 0
            
            occupancy_by_hotel.append({
                'hotel_name': hotel.name,
                'total_rooms': total_rooms,
                'booked_nights': booked_nights,
                'occupancy_rate': f"{occupancy_rate:.1f}%"
            })
        
        # Occupancy by room type
        occupancy_by_room_type = bookings.values('room__room_type__name').annotate(
            booking_count=Count('id'),
            avg_nights=Coalesce(F('nights'), 0, output_field=IntegerField())
        ).order_by('-booking_count')
        
        context = {
            'total_bookings': total_bookings,
            'avg_stay_length': f"{avg_stay_length:.1f} nights" if avg_stay_length > 0 else "No data",
            'occupancy_by_hotel': occupancy_by_hotel,
            'occupancy_by_room_type': list(occupancy_by_room_type),
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'hotels': Hotel.objects.all(),
            'selected_hotel_id': hotel_id,
        }
        
        return render(request, 'manager/occupancy_report.html', context)


# FEATURE 7: MANAGER ROLES AND PROPERTY SCOPING
class ManagerPropertyAssignmentView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Assign hotels/properties to managers.
    Managers can only manage their assigned properties.
    """
    
    model = CustomUser
    template_name = 'manager/manager_properties.html'
    fields = []  # Custom form handling
    permission_required = 'auth.change_user'
    
    def get_object(self, queryset=None):
        """Get the user to assign properties to"""
        return CustomUser.objects.get(id=self.kwargs['user_id'])
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        if user.user_type != 'staff':
            messages.warning(request, 'Only staff users can be assigned properties')
            return redirect('manager:dashboard')
        
        # Get all hotels and user's current assignments
        all_hotels = Hotel.objects.all()
        
        # Note: If you add a ManyToManyField 'managed_hotels' to CustomUser,
        # use: assigned_hotels = user.managed_hotels.all()
        assigned_hotels = []  # Placeholder - implement based on your User model
        
        context = {
            'user': user,
            'all_hotels': all_hotels,
            'assigned_hotels': assigned_hotels,
        }
        return render(request, 'manager/manager_properties.html', context)
    
    def post(self, request, *args, **kwargs):
        """Update property assignments"""
        user = self.get_object()
        hotel_ids = request.POST.getlist('hotels')
        
        # Implementation depends on your User model
        # If you have a ManyToManyField on CustomUser:
        # user.managed_hotels.set(hotel_ids)
        
        messages.success(request, f'Properties assigned to {user.first_name} {user.last_name}')
        return redirect('manager:dashboard')


class ManagerPropertyFilterMixin:
    """
    Mixin to filter querysets by manager's assigned properties.
    Ensures managers only see data for their assigned hotels.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # If user has managed_hotels field, filter by it
        if hasattr(user, 'managed_hotels') and user.user_type == 'staff':
            assigned_hotel_ids = user.managed_hotels.values_list('id', flat=True)
            if assigned_hotel_ids.exists():
                qs = qs.filter(hotel_id__in=assigned_hotel_ids)
        
        return qs


# ============================================================================
# PAYMENTS MANAGEMENT
# ============================================================================

class PaymentListView(BulkActionMixin, BaseListView):
    """List all payments with filtering and search"""
    model = Payment
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'payments.view_payment'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('booking__hotel', 'booking__room').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        # Filter by method
        method = self.request.GET.get('method')
        if method:
            qs = qs.filter(method=method)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)
        
        return qs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['model_name'] = 'payment'
        ctx['add_url_name'] = 'manager:payment_add'
        ctx['detail_url_name'] = None
        ctx['model_verbose_name'] = 'Payment'
        ctx['model_verbose_name_plural'] = 'Payments'
        
        # Add filter options
        ctx['status_choices'] = Payment.PAYMENT_STATUS_CHOICES
        ctx['method_choices'] = Payment.PAYMENT_METHOD_CHOICES
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_method'] = self.request.GET.get('method', '')
        ctx['date_from'] = self.request.GET.get('date_from', '')
        ctx['date_to'] = self.request.GET.get('date_to', '')
        
        return ctx


class PaymentCreateView(BaseCreateView):
    """Create a new payment"""
    model = Payment
    form_class = PaymentForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:payments')
    permission_required = 'payments.add_payment'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['model_name'] = 'payment'
        ctx['model_verbose_name'] = 'Payment'
        ctx['page_title'] = 'Add Payment'
        return ctx


class PaymentUpdateView(BaseUpdateView):
    """Update an existing payment"""
    model = Payment
    form_class = PaymentForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:payments')
    permission_required = 'payments.change_payment'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['model_name'] = 'payment'
        ctx['model_verbose_name'] = 'Payment'
        ctx['page_title'] = 'Edit Payment'
        return ctx


class PaymentDeleteView(BaseDeleteView):
    """Delete a payment"""
    model = Payment
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:payments')
    permission_required = 'payments.delete_payment'


# PROFILE MANAGEMENT VIEWS
class ProfileView(ManagerRequiredMixin, View):
    """Display manager profile information"""
    
    def get(self, request):
        context = {
            'user': request.user,
            'page_title': 'My Profile'
        }
        return render(request, 'manager/profile.html', context)


class ProfileEditView(ManagerRequiredMixin, View):
    """Edit manager profile information (username, email, name)"""
    
    def get(self, request):
        from .forms import ProfileUpdateForm
        form = ProfileUpdateForm(instance=request.user)
        context = {
            'form': form,
            'page_title': 'Edit Profile'
        }
        return render(request, 'manager/profile_edit.html', context)
    
    def post(self, request):
        from .forms import ProfileUpdateForm
        form = ProfileUpdateForm(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('manager:profile')
        
        context = {
            'form': form,
            'page_title': 'Edit Profile'
        }
        return render(request, 'manager/profile_edit.html', context)


class ChangePasswordView(ManagerRequiredMixin, View):
    """Allow manager to change password"""
    
    def get(self, request):
        from .forms import ChangePasswordForm
        form = ChangePasswordForm()
        context = {
            'form': form,
            'page_title': 'Change Password'
        }
        return render(request, 'manager/change_password.html', context)
    
    def post(self, request):
        from .forms import ChangePasswordForm
        from django.contrib.auth import authenticate
        
        form = ChangePasswordForm(request.POST)
        
        if form.is_valid():
            # Verify current password
            current_password = form.cleaned_data.get('current_password')
            if not request.user.check_password(current_password):
                messages.error(request, 'Your current password is incorrect.')
                context = {
                    'form': form,
                    'page_title': 'Change Password'
                }
                return render(request, 'manager/change_password.html', context)
            
            # Set new password
            new_password = form.cleaned_data.get('new_password')
            request.user.set_password(new_password)
            request.user.save()
            
            # Re-authenticate the user to keep them logged in
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('manager:profile')
        
        context = {
            'form': form,
            'page_title': 'Change Password'
        }
        return render(request, 'manager/change_password.html', context)
