import frappe
from valet.valet_parking.api.whatsapp import send_whatsapp_message


@frappe.whitelist()
def get_tickets():
    return frappe.get_all(
        "Parking Ticket",
        fields=[
            "name",
            "parking_token",
            "customer",
            "vehicle_number",
            "vehicle_type",
            "status",
            "check_in_time",
            "check_out_time"
        ],
        filters={
            "status": ["in", [
                "Awaiting Parking",
                "Parked",
                "Retrieval Requested",
                "On The Way"
            ]]
        },
        order_by="creation desc"
    )


@frappe.whitelist()
def update_status(ticket: str, status: str):
    allowed_statuses = [
        "Awaiting Parking",
        "Parked",
        "Retrieval Requested",
        "On The Way",
        "Delivered"
    ]

    if status not in allowed_statuses:
        frappe.throw("Invalid status")

    doc = frappe.get_doc("Parking Ticket", ticket)

    doc.status = status

    # When valet parks the vehicle
    if status == "Parked":
        if not doc.check_in_time:
            doc.check_in_time = frappe.utils.now_datetime()

    # When vehicle is delivered back to customer
    if status == "Delivered":
        doc.check_out_time = frappe.utils.now_datetime()

    doc.save(ignore_permissions=True)

    whatsapp = None

    if status in ["On The Way", "Delivered"]:
        customer = frappe.get_doc("Valet Customer", doc.customer)

        if customer.mobile_number:
            if status == "On The Way":
                message = (
                    f"Your vehicle {doc.vehicle_number} is on the way. "
                    f"Parking token: {doc.parking_token}."
                )
            else:
                message = (
                    f"Your vehicle {doc.vehicle_number} has been delivered. "
                    f"Thank you for using our valet service."
                )

            whatsapp = send_whatsapp_message(
                customer.mobile_number,
                message
            )

    return {
        "success": True,
        "ticket": doc.name,
        "status": doc.status,
        "whatsapp": whatsapp
    }
@frappe.whitelist()
def request_vehicle(ticket: str):
    doc = frappe.get_doc("Parking Ticket", ticket)

    if doc.status != "Parked":
        frappe.throw("Vehicle can only be requested when it is Parked.")

    doc.status = "Retrieval Requested"
    doc.retrieval_requested_at = frappe.utils.now_datetime()

    doc.save(ignore_permissions=True)

    return {
        "success": True,
        "ticket": doc.name,
        "status": doc.status,
        "retrieval_requested_at": doc.retrieval_requested_at
    }
