import io
import frappe
import qrcode
from frappe.model.document import Document


class ParkingTicket(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        check_in_time: DF.Datetime | None
        check_out_time: DF.Datetime | None
        customer: DF.Link
        parking_token: DF.Data | None
        retrieval_requested_at: DF.Datetime | None
        status: DF.Literal["Awaiting Parking", "Parked", "Retrieval Requested", "On The Way", "Delivered", "Cancelled"]
        vehicle_number: DF.Data
        vehicle_type: DF.Literal["car", "bike", "scooter", "van", "other"]
    # end: auto-generated types

    def before_insert(self):
        # Generate unique parking token automatically
        if not self.parking_token:
            self.parking_token = frappe.model.naming.make_autoname("PT-.####")

        # Record vehicle check-in time automatically
        if not self.check_in_time:
            self.check_in_time = frappe.utils.now_datetime()

        # New ticket starts as Awaiting Parking
        if not self.status:
            self.status = "Awaiting Parking"

    def on_update(self):
        # When valet attendant marks the vehicle as Parked,
        # record the parking/check-in time if it has not already been set.
        if self.status == "Parked" and not self.check_in_time:
            self.check_in_time = frappe.utils.now_datetime()

        # When vehicle is delivered, record checkout time
        if self.status == "Delivered" and not self.check_out_time:
            self.check_out_time = frappe.utils.now_datetime()

    def after_insert(self):
        # Generate and attach a QR code containing the parking token.
        if self.parking_token and not self.qr_code:
            ticket_url = f"{frappe.utils.get_url()}/parking-ticket-view?ticket={self.parking_token}"
            qr = qrcode.make(ticket_url)

            buffer = io.BytesIO()
            qr.save(buffer, format="PNG")

            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": f"{self.parking_token}.png",
                "attached_to_doctype": self.doctype,
                "attached_to_name": self.name,
                "attached_to_field": "qr_code",
                "content": buffer.getvalue(),
                "is_private": 0
            })

            file_doc.insert(ignore_permissions=True)

            frappe.db.set_value(
                self.doctype,
                self.name,
                "qr_code",
                file_doc.file_url,
                update_modified=False
            )
