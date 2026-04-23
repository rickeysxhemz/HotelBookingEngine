"""Payment views for Tap Payments integration"""
import json
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from bookings.models import Booking
from .models import Payment, TapPaymentTransaction
from .serializers import PaymentSerializer, PaymentListSerializer
from .services import TapPaymentService, TapPaymentException

logger = logging.getLogger(__name__)


class InitiatePaymentView(generics.CreateAPIView):
    """Initiate payment - POST /payments/initiate/"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            booking_id = request.data.get('booking_id')
            amount = request.data.get('amount')
            tap_source_id = request.data.get('tap_source_id')
            
            if not all([booking_id, amount, tap_source_id]):
                return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            
            booking = Booking.objects.get(id=booking_id)
            if booking.user and booking.user != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
            tap_service = TapPaymentService()
            success, payment, error = tap_service.create_payment(booking=booking, amount=amount, source_id=tap_source_id)

            if not success:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            if payment.status == 'completed':
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
            else:
                booking.payment_status = 'pending'
            booking.save()

            data = PaymentSerializer(payment).data
            redirect_url = getattr(payment, 'redirect_url', None)
            if redirect_url:
                data['redirect_url'] = redirect_url
            logger.info(f"Payment initiated: {payment.id}")
            return Response(data, status=status.HTTP_201_CREATED)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
        except TapPaymentException:
            return Response({'error': 'Payment service unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Payment error: {str(e)}", exc_info=True)
            return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TapPaymentCallbackView(APIView):
    """Webhook handler for Tap - POST /payments/callback/"""
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        try:
            signature = request.headers.get('x-tap-signature', '')
            raw_body = request.body.decode('utf-8')
            
            tap_service = TapPaymentService()
            if not tap_service.verify_webhook_signature(raw_body, signature):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
            
            payload = json.loads(raw_body)
            event_type = payload.get('type')
            data = payload.get('data', {})
            charge_id = data.get('id')
            charge_status = data.get('status')
            
            logger.info(f"Webhook: {event_type} - {charge_id}")
            
            if event_type == 'charge.captured' or charge_status in ['CHARGED', 'COMPLETED']:
                try:
                    payment = Payment.objects.get(transaction_id=charge_id)
                    payment.status = 'completed'
                    payment.save()
                    booking = payment.booking
                    booking.payment_status = 'paid'
                    booking.status = 'confirmed'
                    booking.save()
                    logger.info(f"Payment completed: {payment.id}")
                except Payment.DoesNotExist:
                    logger.warning(f"Payment not found: {charge_id}")
            
            elif event_type == 'charge.failed' or charge_status == 'FAILED':
                try:
                    payment = Payment.objects.get(transaction_id=charge_id)
                    payment.status = 'failed'
                    payment.save()
                    logger.warning(f"Payment failed: {payment.id}")
                except Payment.DoesNotExist:
                    logger.warning(f"Payment not found: {charge_id}")
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return Response({'error': 'Processing error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(generics.RetrieveAPIView):
    """Get payment - GET /payments/{id}/"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(booking__user=user) | Payment.objects.filter(booking__guest_email=user.email)


class PaymentListView(generics.ListAPIView):
    """List payments - GET /payments/"""
    serializer_class = PaymentListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(booking__user=self.request.user).select_related('booking', 'tap_transaction').order_by('-created_at')


class PaymentRefundView(generics.CreateAPIView):
    """Process refund - POST /payments/{id}/refund/"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk, *args, **kwargs):
        try:
            payment = Payment.objects.get(id=pk)
            if payment.booking.user != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
            if payment.status != 'completed':
                return Response({'error': 'Payment not refundable'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not payment.booking.can_be_cancelled():
                return Response({'error': 'Booking cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
            
            tap_service = TapPaymentService()
            success, _, error = tap_service.refund_payment(transaction_id=payment.transaction_id, reason=request.data.get('reason'))
            
            if not success:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
            payment.status = 'refunded'
            payment.save()
            payment.booking.payment_status = 'refunded'
            payment.booking.status = 'cancelled'
            payment.booking.save()
            
            logger.info(f"Refund processed: {payment.id}")
            return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Refund error: {str(e)}", exc_info=True)
            return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
