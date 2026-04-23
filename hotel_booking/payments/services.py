"""Tap Payments service - Production-grade payment processing"""
import logging
import json
import hmac
import hashlib
import uuid
from decimal import Decimal
from typing import Tuple, Optional, Dict, Any
from django.conf import settings
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .models import Payment, TapPaymentTransaction

logger = logging.getLogger(__name__)

class TapPaymentException(Exception):
    """Tap payment service exceptions"""
    pass

class TapPaymentService:
    """
    Tap Payments integration service with retry logic, idempotency, 
    webhook verification, and comprehensive error handling
    """
    
    BASE_URL = 'https://api.tap.company/v2'
    MAX_RETRIES = 3
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        """Initialize with Tap API credentials from settings"""
        self.api_key = api_key or getattr(settings, 'TAP_API_KEY', None)
        self.secret_key = secret_key or getattr(settings, 'TAP_SECRET_KEY', None)
        if not self.secret_key:
            raise TapPaymentException("TAP_SECRET_KEY not configured in settings")
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with automatic retry strategy"""
        session = requests.Session()
        retry = Retry(total=self.MAX_RETRIES, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update({'Authorization': f'Bearer {self.secret_key}', 'Content-Type': 'application/json'})
        return session
    
    def create_payment(self, booking, amount: Decimal, currency='SAR', source_id: Optional[str]=None, save_card=False) -> Tuple[bool, Optional[Payment], Optional[str]]:
        """Create payment charge via Tap API"""
        try:
            idempotency_key = str(uuid.uuid4())
            payload = {
                'amount': float(amount),
                'currency': currency,
                'customer': {
                    'first_name': booking.guest_first_name,
                    'last_name': booking.guest_last_name,
                    'email': booking.guest_email,
                    'phone': {'country_code': '+966', 'number': booking.guest_phone}
                },
                'description': f"Booking {booking.booking_id} - {booking.hotel.name}",
                'metadata': {'booking_id': booking.booking_id, 'hotel_id': str(booking.hotel.id)},
                'receipt': {'email': True},
                'redirect': {'url': getattr(settings, 'SITE_URL', 'http://localhost:5173') + f'/booking/{booking.id}?from=tap'},
            }
            if source_id:
                payload['source'] = {'id': source_id}
            if save_card:
                payload['save_card'] = True
            merchant_id = getattr(settings, 'TAP_MERCHANT_ID', '')
            if merchant_id:
                payload['merchant'] = {'id': merchant_id}
            
            response = self.session.post(f'{self.BASE_URL}/charges', json=payload, timeout=30, headers={'Idempotency-Key': idempotency_key})
            response.raise_for_status()
            data = response.json()
            
            tap_id = data.get('id')
            tap_status = data.get('status')
            tap_success = tap_status in ['CHARGED', 'COMPLETED']
            tap_pending = tap_status in ['INITIATED', 'IN_PROGRESS', 'PENDING']

            if tap_success:
                payment_status = 'completed'
            elif tap_pending:
                payment_status = 'processing'
            else:
                payment_status = 'failed'

            payment, _ = Payment.objects.update_or_create(booking=booking, defaults={
                'amount': amount, 'currency': currency, 'method': 'tap', 'transaction_id': tap_id,
                'idempotency_key': idempotency_key, 'status': payment_status,
            })

            TapPaymentTransaction.objects.update_or_create(payment=payment, defaults={
                'tap_id': tap_id, 'tap_source_id': data.get('source', {}).get('id'),
                'tap_card_last_4': data.get('source', {}).get('card', {}).get('last_four'),
                'tap_card_brand': data.get('source', {}).get('card', {}).get('brand'),
                'tap_success': tap_success, 'tap_response_code': data.get('response', {}).get('code'),
                'tap_error_message': data.get('response', {}).get('message'), 'tap_raw_response': data,
            })

            redirect_url = (data.get('transaction') or {}).get('url')
            if redirect_url:
                payment.redirect_url = redirect_url

            logger.info(f"Payment created: {tap_id} status={tap_status}")

            if tap_success or tap_pending:
                return True, payment, None
            return False, payment, data.get('response', {}).get('message') or f'Status {tap_status}'
        except Exception as e:
            logger.error(f"Payment error: {str(e)}", exc_info=True)
            return False, None, str(e)
    
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal]=None, reason: Optional[str]=None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Process refund for a payment"""
        try:
            payload = {'charge_id': transaction_id}
            if amount:
                payload['amount'] = float(amount)
            if reason:
                payload['reason'] = reason
            
            response = self.session.post(f'{self.BASE_URL}/refunds', json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            success = data.get('status') in ['REFUNDED', 'COMPLETED']
            error = None if success else data.get('response', {}).get('message', 'Refund failed')
            logger.info(f"Refund {'succeeded' if success else 'failed'}: {transaction_id}")
            return success, data, error
        except Exception as e:
            logger.error(f"Refund error: {str(e)}", exc_info=True)
            return False, None, str(e)
    
    def verify_payment(self, charge_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Verify payment status from Tap API"""
        try:
            response = self.session.get(f'{self.BASE_URL}/charges/{charge_id}', timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Payment verified: {charge_id}")
            return True, data, None
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            return False, None, str(e)
    
    def get_payment_status(self, transaction_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Get payment status from database and verify with API"""
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            success, data, error = self.verify_payment(transaction_id)
            if success and data:
                tap_status = data.get('status')
                if tap_status in ['CHARGED', 'COMPLETED'] and payment.status != 'completed':
                    payment.status = 'completed'
                    payment.save()
            return True, payment.status, None
        except Payment.DoesNotExist:
            return False, None, f"Payment not found: {transaction_id}"
        except Exception as e:
            logger.error(f"Status error: {str(e)}", exc_info=True)
            return False, None, str(e)
    
    def verify_webhook_signature(self, payload: str, signature: str, secret: Optional[str]=None) -> bool:
        """Verify Tap webhook signature for security"""
        try:
            webhook_secret = secret or getattr(settings, 'TAP_WEBHOOK_SECRET', None)
            if not webhook_secret:
                return False
            computed = hmac.new(webhook_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(computed, signature)
        except Exception as e:
            logger.error(f"Signature error: {str(e)}")
            return False
