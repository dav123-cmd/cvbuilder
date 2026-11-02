"""
M-Pesa Daraja STK Push integration for the resume builder paywall.

Flow:
1. User hits "Upgrade" -> initiate_stk_push() sends a request to Safaricom,
   which triggers a payment prompt on their phone.
2. Safaricom calls our callback URL asynchronously with the result.
3. We mark the Payment as success/failed and flip the Resume to "paid" tier.

"""

import os
import base64
import requests
from datetime import datetime
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Resume, Payment


MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE")  # Paybill/Till number
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL")  # must be publicly reachable HTTPS

# Use sandbox until you're verified for production
MPESA_BASE_URL = os.environ.get("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")

UPGRADE_PRICE_KES = 1 # one-time unlock; adjust as you decide on pricing


def get_access_token():
    """OAuth token required by Safaricom before any Daraja API call."""
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=15)
    response.raise_for_status()
    return response.json()["access_token"]


def build_password(timestamp: str) -> str:
    raw = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def initiate_stk_push(resume: Resume, phone_number: str) -> Payment:
    """
    Kicks off the STK push prompt on the user's phone.
    phone_number must be in 2547XXXXXXXX format (the ResumeForm already
    normalizes .
    """
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = build_password(timestamp)
    access_token = get_access_token()

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": UPGRADE_PRICE_KES,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": f"RESUME-{str(resume.id)[:8]}",
        "TransactionDesc": "Resume Builder Premium Unlock",
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(
        f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers,
        timeout=15,
    )
    data = response.json()

    # Create the Payment record regardless of outcome so we have an audit trail
    payment = Payment.objects.create(
        resume=resume,
        phone_number=phone_number,
        amount=UPGRADE_PRICE_KES,
        checkout_request_id=data.get("CheckoutRequestID", ""),
        merchant_request_id=data.get("MerchantRequestID", ""),
        status="pending",
    )

    if data.get("ResponseCode") != "0":
        # Safaricom rejected the request outright (bad shortcode, invalid phone, etc.)
        payment.status = "failed"
        payment.raw_callback = data
        payment.save(update_fields=["status", "raw_callback"])

    return payment


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


@login_required
@require_POST
def upgrade_initiate(request, resume_id):
    """Called from the upgrade page when the user submits their phone number."""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    phone_number = request.POST.get("phone_number", "").strip()

    if not phone_number:
        return JsonResponse({"error": "Phone number is required."}, status=400)

    try:
        payment = initiate_stk_push(resume, phone_number)
    except requests.RequestException:
        return JsonResponse(
            {"error": "Could not reach M-Pesa right now. Please try again shortly."}, status=503
        )

    if payment.status == "failed":
        return JsonResponse({"error": "M-Pesa rejected the request. Check the phone number and try again."}, status=400)

    return JsonResponse({
        "message": "Check your phone and enter your M-Pesa PIN to complete payment.",
        "checkout_request_id": payment.checkout_request_id,
    })


@csrf_exempt
def mpesa_callback(request):
    
    try:
        payload = request.body
        import json
        data = json.loads(payload)
    except (ValueError, TypeError):
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid payload"})

    stk_callback = data.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
    if not payment:
        # Nothing to reconcile against — log and acknowledge so Safaricom stops retrying
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    payment.raw_callback = data

    if result_code == 0:
        # Success — extract the receipt number from the metadata items
        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        receipt = next((i["Value"] for i in metadata if i.get("Name") == "MpesaReceiptNumber"), "")
        payment.status = "success"
        payment.mpesa_receipt_number = receipt
        payment.save()

        # Unlock the resume
        resume = payment.resume
        resume.tier = "paid"
        resume.save(update_fields=["tier"])
    else:
        payment.status = "failed"
        payment.save()

    # Always acknowledge receipt, or Safaricom will keep retrying the callback
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


@login_required
def upgrade_status(request, resume_id):
    """
    Polled by the frontend (every few seconds) while waiting for the user to
    complete the STK push on their phone, since the callback is async.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    latest_payment = resume.payments.order_by("-created_at").first()

    if not latest_payment:
        return JsonResponse({"status": "none"})

    return JsonResponse({
        "status": latest_payment.status,
        "is_paid": resume.is_paid,
    })
