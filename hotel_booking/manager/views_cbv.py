from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

from core.models import Hotel, Room, RoomType, Extra, SeasonalPricing
from bookings.models import Booking
from .forms import HotelForm, RoomForm, RoomTypeForm, ExtraForm, SeasonalPricingForm, BookingForm
from .forms import BookingExtraForm, BookingGuestForm, BookingHistoryForm, RoomAmenityForm, RoomImageForm, RoomTypeAmenityForm
from bookings.models import BookingExtra, BookingGuest, BookingHistory
from core.models import RoomAmenity, RoomImage, RoomTypeAmenity
from django.http import HttpResponse
import csv


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name='Manager').exists() or self.request.user.is_superuser


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


class BaseListView(ModelContextMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
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
        ctx['detail_url_name'] = f'manager:{model_name}_detail'
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
