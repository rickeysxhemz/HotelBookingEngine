import csv
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from bookings.models import Booking, BookingExtra, BookingGuest, BookingHistory
from core.models import (Extra, Hotel, Room, RoomAmenity, RoomImage, RoomType,
                       RoomTypeAmenity, SeasonalPricing)

from .forms import (BookingExtraForm, BookingForm, BookingGuestForm,
                    BookingHistoryForm, ExtraForm, HotelForm, RoomAmenityForm,
                    RoomForm, RoomImageForm, RoomTypeAmenityForm,
                    RoomTypeForm, SeasonalPricingForm)


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


class ManagerLoginView(View):
    """
    Custom login view for managers only.
    Only allows users with user_type 'staff' and is_staff=True to login.
    Blocks admin users (user_type 'admin' or is_superuser=True).
    """
    
    def get(self, request):
        # Render a simple form with email and password fields
        return render(request, 'manager/login.html', {'form': None})

    def post(self, request):
        from django.contrib.auth import authenticate
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.is_active:
                user_type = getattr(user, 'user_type', None)
                if user.is_staff and user_type == 'staff' and not user.is_superuser and user_type != 'admin':
                    login(request, user)
                    messages.success(request, 'Login successful. Welcome, Manager!')
                    return redirect('manager:dashboard')
                else:
                    messages.error(request, 'Access denied: Only staff managers can log in here.')
            else:
                messages.error(request, 'This account is inactive.')
        else:
            messages.error(request, 'Invalid email or password.')
        return render(request, 'manager/login.html', {'form': None})


class DashboardView(ManagerRequiredMixin, View):
    """Enhanced dashboard with quick stats for the manager UI."""
    
    def get(self, request):
        today = timezone.now().date()
        user = request.user
        # Booking stats
        total_bookings = Booking.objects.count()
        new_bookings = Booking.objects.filter(booking_date__date=today).count()
        checked_in = Booking.objects.filter(status='checked_in').count()
        upcoming = Booking.objects.filter(check_in__gte=today).count()
        recent_bookings = Booking.objects.order_by('-booking_date')[:8]

        # Core entities
        hotels_count = Hotel.objects.count()
        rooms_count = Room.objects.count()
        extras_count = Extra.objects.count()
        roomtypes_count = RoomType.objects.count()
        roomamenities_count = RoomAmenity.objects.count()
        roomimages_count = RoomImage.objects.count()
        roomtypeamenities_count = RoomTypeAmenity.objects.count()
        seasonalpricing_count = SeasonalPricing.objects.count()

        # Bookings related
        bookingextras_count = BookingExtra.objects.count()
        bookingguests_count = BookingGuest.objects.count()
        bookinghistories_count = BookingHistory.objects.count()

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
            'bookingextra': {
                'add': user.has_perm('bookings.add_bookingextra'),
                'view': user.has_perm('bookings.view_bookingextra'),
                'change': user.has_perm('bookings.change_bookingextra'),
            },
            'bookingguest': {
                'add': user.has_perm('bookings.add_bookingguest'),
                'view': user.has_perm('bookings.view_bookingguest'),
                'change': user.has_perm('bookings.change_bookingguest'),
            },
            'bookinghistory': {
                'add': user.has_perm('bookings.add_bookinghistory'),
                'view': user.has_perm('bookings.view_bookinghistory'),
                'change': user.has_perm('bookings.change_bookinghistory'),
            },
            'booking': {
                'add': user.has_perm('bookings.add_booking'),
                'view': user.has_perm('bookings.view_booking'),
                'change': user.has_perm('bookings.change_booking'),
            },
        }

        context = {
            'total_bookings': total_bookings,
            'new_bookings': new_bookings,
            'checked_in': checked_in,
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
            'bookingextras_count': bookingextras_count,
            'bookingguests_count': bookingguests_count,
            'bookinghistories_count': bookinghistories_count,
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
            if 'booking_reference' in field_names:
                filters |= Q(booking_reference__icontains=q)
            if 'primary_guest_name' in field_names:
                filters |= Q(primary_guest_name__icontains=q)
            if filters:
                qs = qs.filter(filters)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model_name = self.model._meta.model_name
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
        messages.success(self.request, 'Created successfully.')
        return super().form_valid(form)


class BaseUpdateView(ModelContextMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, 'Updated successfully.')
        return super().form_valid(form)

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


# Booking extras, guests, history
class BookingExtraListView(BulkActionMixin, BaseListView):
    model = BookingExtra
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'bookings.view_bookingextra'


class BookingExtraCreateView(BaseCreateView):
    model = BookingExtra
    form_class = BookingExtraForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:bookingextras')
    permission_required = 'bookings.add_bookingextra'


class BookingExtraUpdateView(BaseUpdateView):
    model = BookingExtra
    form_class = BookingExtraForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:bookingextras')
    permission_required = 'bookings.change_bookingextra'


class BookingExtraDeleteView(BaseDeleteView):
    model = BookingExtra
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:bookingextras')
    permission_required = 'bookings.delete_bookingextra'


class BookingExtraExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'bookings.view_bookingextra'
    def get(self, request, *args, **kwargs):
        qs = BookingExtra.objects.all()
        fields = ['id', 'booking_id', 'extra_id', 'quantity', 'unit_price', 'total_price']
        return export_as_csv(qs, fields)


class BookingGuestListView(BulkActionMixin, BaseListView):
    model = BookingGuest
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'bookings.view_bookingguest'


class BookingGuestCreateView(BaseCreateView):
    model = BookingGuest
    form_class = BookingGuestForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:bookingguests')
    permission_required = 'bookings.add_bookingguest'


class BookingGuestUpdateView(BaseUpdateView):
    model = BookingGuest
    form_class = BookingGuestForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:bookingguests')
    permission_required = 'bookings.change_bookingguest'


class BookingGuestDeleteView(BaseDeleteView):
    model = BookingGuest
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:bookingguests')
    permission_required = 'bookings.delete_bookingguest'


class BookingHistoryListView(BulkActionMixin, BaseListView):
    model = BookingHistory
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'bookings.view_bookinghistory'


class BookingHistoryCreateView(BaseCreateView):
    model = BookingHistory
    form_class = BookingHistoryForm
    template_name = 'manager/form.html'
    success_url = reverse_lazy('manager:bookinghistories')
    permission_required = 'bookings.add_bookinghistory'


class BookingHistoryDeleteView(BaseDeleteView):
    model = BookingHistory
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:bookinghistories')
    permission_required = 'bookings.delete_bookinghistory'


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


# Bookings (basic list + detail)
class BookingListView(BulkActionMixin, BaseListView):
    model = Booking
    template_name = 'manager/list.html'
    context_object_name = 'objects'
    permission_required = 'bookings.view_booking'


class BookingDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Booking
    template_name = 'manager/detail.html'
    context_object_name = 'object'
    permission_required = 'bookings.view_booking'


class BookingCreateView(BaseCreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'manager/form.html'
    permission_required = 'bookings.add_booking'


class BookingUpdateView(BaseUpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'manager/form.html'
    permission_required = 'bookings.change_booking'


class BookingDeleteView(BaseDeleteView):
    model = Booking
    template_name = 'manager/confirm_delete.html'
    success_url = reverse_lazy('manager:bookings')
    permission_required = 'bookings.delete_booking'


class GlobalSearchView(ManagerRequiredMixin, View):
    """Global search view that searches across multiple models"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if not query:
            return render(request, 'manager/search_results.html', {
                'query': query,
                'results': {},
                'total_results': 0
            })
        
        results = {}
        total_results = 0
        
        # Search Bookings
        if request.user.has_perm('bookings.view_booking'):
            bookings = Booking.objects.filter(
                Q(booking_reference__icontains=query) |
                Q(primary_guest_name__icontains=query) |
                Q(primary_guest_email__icontains=query) |
                Q(primary_guest_phone__icontains=query)
            )[:10]
            if bookings.exists():
                results['bookings'] = {
                    'objects': bookings,
                    'count': bookings.count(),
                    'verbose_name': Booking._meta.verbose_name_plural,
                    'url_name': 'manager:bookings'
                }
                total_results += bookings.count()
        
        # Search Hotels
        if request.user.has_perm('core.view_hotel'):
            hotels = Hotel.objects.filter(
                Q(name__icontains=query) |
                Q(address_line_1__icontains=query) |
                Q(address_line_2__icontains=query) |
                Q(city__icontains=query)
            )[:10]
            if hotels.exists():
                results['hotels'] = {
                    'objects': hotels,
                    'count': hotels.count(),
                    'verbose_name': Hotel._meta.verbose_name_plural,
                    'url_name': 'manager:hotels'
                }
                total_results += hotels.count()
        
        # Search Rooms
        if request.user.has_perm('core.view_room'):
            rooms = Room.objects.filter(
                Q(room_number__icontains=query) |
                Q(room_type__name__icontains=query)
            )[:10]
            if rooms.exists():
                results['rooms'] = {
                    'objects': rooms,
                    'count': rooms.count(),
                    'verbose_name': Room._meta.verbose_name_plural,
                    'url_name': 'manager:rooms'
                }
                total_results += rooms.count()
        
        # Search Room Types
        if request.user.has_perm('core.view_roomtype'):
            room_types = RoomType.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:10]
            if room_types.exists():
                results['room_types'] = {
                    'objects': room_types,
                    'count': room_types.count(),
                    'verbose_name': RoomType._meta.verbose_name_plural,
                    'url_name': 'manager:roomtypes'
                }
                total_results += room_types.count()
        
        # Search Extras
        if request.user.has_perm('core.view_extra'):
            extras = Extra.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:10]
            if extras.exists():
                results['extras'] = {
                    'objects': extras,
                    'count': extras.count(),
                    'verbose_name': Extra._meta.verbose_name_plural,
                    'url_name': 'manager:extras'
                }
                total_results += extras.count()
        
        context = {
            'query': query,
            'results': results,
            'total_results': total_results
        }
        
        return render(request, 'manager/search_results.html', context)
