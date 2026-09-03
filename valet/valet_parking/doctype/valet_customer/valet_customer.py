# Copyright (c) 2026, Yeshwanth and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class valetcustomer(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		customer_name: DF.Data
		mobile_number: DF.Phone
		status: DF.Literal["Awaiting Parking", "Parked", "Retrieval requested", "On the Way", "Delivered"]
		vehicle_number: DF.Data
		vehicle_type: DF.Literal["car", "bike", "scooter", "other"]
	# end: auto-generated types

	_DOCTYPE_NAME = "valet customer"
ValetCustomer = valetcustomer
