import json
from typing import Any

import frappe
import requests


def _get_whatsapp_setting(key: str, default: str | None = None) -> str | None:
    """Read a WhatsApp setting from site_config.json."""
    return frappe.conf.get(key, default)


def _get_whatsapp_api_url() -> str:
    """Build the Meta Graph API URL."""
    api_version = _get_whatsapp_setting("whatsapp_api_version", "v23.0")
    phone_number_id = _get_whatsapp_setting("whatsapp_phone_number_id")

    if not phone_number_id:
        frappe.throw("WhatsApp Phone Number ID is not configured.")

    return (
        f"https://graph.facebook.com/"
        f"{api_version}/{phone_number_id}/messages"
    )


def send_whatsapp_message(to: str, message: str) -> dict[str, Any]:
    """
    Send a text message through Meta WhatsApp Cloud API.

    Credentials are read from site_config.json:
      whatsapp_access_token
      whatsapp_phone_number_id
      whatsapp_api_version
    """

    access_token = _get_whatsapp_setting("whatsapp_access_token")

    if not access_token:
        return {
            "success": False,
            "error": "WhatsApp access token is not configured."
        }

    url = _get_whatsapp_api_url()

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )

        response_data = response.json()

        if not response.ok:
            frappe.logger().error(
                "WhatsApp API error: %s",
                json.dumps(response_data)
            )

            return {
                "success": False,
                "status_code": response.status_code,
                "error": response_data
            }

        return {
            "success": True,
            "response": response_data
        }

    except requests.RequestException as exc:
        frappe.logger().error(
            "WhatsApp API request failed: %s",
            str(exc)
        )

        return {
            "success": False,
            "error": str(exc)
        }


def _normalise_mobile(mobile: str) -> str:
    """Normalise an Indian mobile number for customer lookup."""
    mobile = str(mobile or "").strip()

    if mobile.startswith("+91"):
        return mobile

    if mobile.startswith("91") and len(mobile) == 12:
        return "+" + mobile

    if mobile.isdigit() and len(mobile) == 10:
        return "+91" + mobile

    return mobile


def _process_vehicle_request(mobile: str) -> dict[str, Any]:
    """Process a customer's request for their parked vehicle."""

    mobile = _normalise_mobile(mobile)

    if not mobile:
        return {
            "success": False,
            "reply": "Mobile number is required."
        }

    customers = frappe.get_all(
        "Valet Customer",
        filters={
            "mobile_number": mobile
        },
        fields=[
            "name",
            "customer_name",
            "vehicle_number"
        ],
        limit=1
    )

    if not customers:
        return {
            "success": False,
            "reply": "No customer found with this mobile number."
        }

    customer = customers[0]

    tickets = frappe.get_all(
        "Parking Ticket",
        filters={
            "customer": customer.name,
            "status": "Parked"
        },
        fields=[
            "name",
            "parking_token",
            "vehicle_number",
            "status"
        ],
        limit=1
    )

    if not tickets:
        return {
            "success": False,
            "reply": "You do not have a parked vehicle right now."
        }

    ticket = frappe.get_doc(
        "Parking Ticket",
        tickets[0].name
    )

    ticket.status = "Retrieval Requested"
    ticket.retrieval_requested_at = frappe.utils.now_datetime()
    ticket.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "ticket": ticket.name,
        "parking_token": ticket.parking_token,
        "vehicle_number": ticket.vehicle_number,
        "status": ticket.status,
        "reply": (
            "Your vehicle retrieval request has been received. "
            "A valet attendant will bring your vehicle shortly."
        )
    }


def _extract_meta_messages(data: dict[str, Any]) -> list[dict[str, str]]:
    """Extract incoming customer messages from Meta's webhook payload."""

    messages = []

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                sender = str(message.get("from", "")).strip()

                if message.get("type") != "text":
                    continue

                text = (
                    message.get("text", {})
                    .get("body", "")
                )

                if sender and text:
                    messages.append({
                        "from": sender,
                        "message": text.strip()
                    })

    return messages


@frappe.whitelist(allow_guest=True)
def webhook() -> Any:
    """
    Handle both Meta webhook verification and incoming messages.

    GET:
      Meta webhook verification.

    POST:
      Real WhatsApp webhook notifications.
    """

    # ---------------------------------------------------------
    # META WEBHOOK VERIFICATION
    # ---------------------------------------------------------
    if frappe.request.method == "GET":

        mode = frappe.form_dict.get("hub.mode")
        verify_token = frappe.form_dict.get("hub.verify_token")
        challenge = frappe.form_dict.get("hub.challenge")

        configured_token = _get_whatsapp_setting(
            "whatsapp_verify_token"
        )

        if (
            mode == "subscribe"
            and verify_token
            and configured_token
            and verify_token == configured_token
        ):
            frappe.local.response["type"] = "text"
            frappe.local.response["message"] = challenge
            return challenge

        frappe.throw(
            "WhatsApp webhook verification failed.",
            frappe.AuthenticationError
        )

    # ---------------------------------------------------------
    # REAL META WHATSAPP WEBHOOK
    # ---------------------------------------------------------
    data = frappe.request.get_json() or {}

    frappe.logger().info(
        "WHATSAPP META WEBHOOK RECEIVED: %s",
        json.dumps(data)
    )

    incoming_messages = _extract_meta_messages(data)

    results = []

    for incoming in incoming_messages:

        mobile = incoming["from"]
        message = incoming["message"].strip().lower()

        request_words = [
            "my vehicle",
            "request vehicle",
            "bring my vehicle",
            "get my vehicle",
            "retrieve vehicle"
        ]

        if any(word in message for word in request_words):

            result = _process_vehicle_request(mobile)

            send_result = send_whatsapp_message(
                mobile,
                result["reply"]
            )

            result["whatsapp"] = send_result
            results.append(result)

        else:

            reply = (
                "Please send 'My Vehicle' to request your parked vehicle."
            )

            send_result = send_whatsapp_message(
                mobile,
                reply
            )

            results.append({
                "success": True,
                "reply": reply,
                "whatsapp": send_result
            })

    return {
        "success": True,
        "processed": len(results),
        "results": results
    }


@frappe.whitelist(allow_guest=True)
def simulate_message(from_number: str, message: str) -> dict[str, Any]:
    """
    Local testing endpoint.

    Example:
      from_number = 9346559536
      message = My Vehicle

    This does NOT call Meta.
    """

    result = _process_vehicle_request(from_number)

    return {
        "success": result["success"],
        "ticket": result.get("ticket"),
        "parking_token": result.get("parking_token"),
        "vehicle_number": result.get("vehicle_number"),
        "status": result.get("status"),
        "reply": result["reply"]
    }
