frappe.ui.form.on("Parking Ticket", {
    refresh(frm) {

        // Show retrieval button only when vehicle is currently parked
        if (frm.doc.status === "Parked") {

            frm.add_custom_button(
                "Request My Vehicle",
                function () {

                    frappe.call({
                        method: "valet.valet_parking.page.valet_attendant.valet_attendant.request_vehicle",

                        args: {
                            ticket: frm.doc.name
                        },

                        callback: function (r) {

                            if (r.exc) {
                                frappe.msgprint(
                                    "Failed to request vehicle."
                                );
                                return;
                            }

                            frappe.show_alert({
                                message: "Vehicle retrieval requested",
                                indicator: "green"
                            });

                            frm.reload_doc();
                        }
                    });

                },
                "Vehicle"
            );
        }
    }
});

