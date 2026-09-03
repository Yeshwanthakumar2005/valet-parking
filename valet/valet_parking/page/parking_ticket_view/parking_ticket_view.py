import frappe


@frappe.whitelist(allow_guest=True)
def get_ticket(ticket: str):
    tickets = frappe.get_all(
        "Parking Ticket",
        filters={"parking_token": ticket},
        fields=[
            "name",
            "parking_token",
            "vehicle_number",
            "vehicle_type",
            "status",
            "check_in_time",
            "check_out_time",
            "qr_code"
        ],
        limit=1
    )

    if not tickets:
        frappe.throw("Parking ticket not found.")

    return tickets[0]


@frappe.whitelist(allow_guest=True)
def request_vehicle(ticket: str):
    tickets = frappe.get_all(
        "Parking Ticket",
        filters={
            "parking_token": ticket,
            "status": "Parked"
        },
        fields=["name"],
        limit=1
    )

    if not tickets:
        frappe.throw("Vehicle is not currently available for retrieval.")

    doc = frappe.get_doc("Parking Ticket", tickets[0].name)

    doc.status = "Retrieval Requested"
    doc.retrieval_requested_at = frappe.utils.now_datetime()
    doc.save(ignore_permissions=True)

    return {
        "success": True,
        "ticket": doc.parking_token,
        "status": doc.status
    }
