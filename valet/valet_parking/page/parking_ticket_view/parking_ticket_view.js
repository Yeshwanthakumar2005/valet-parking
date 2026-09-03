frappe.pages["parking-ticket-view"].on_page_load = function (wrapper) {
    new ParkingTicketView(wrapper);
};

class ParkingTicketView {
    constructor(wrapper) {
        this.wrapper = $(wrapper);

        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Parking Ticket",
            single_column: true
        });

        this.load_ticket();
    }

    load_ticket() {
        const ticket = new URLSearchParams(window.location.search).get("ticket");

        if (!ticket) {
            $(this.page.body).html(`
                <div class="alert alert-danger">
                    Parking ticket number is missing.
                </div>
            `);
            return;
        }

        frappe.call({
            method: "valet.valet_parking.page.parking_ticket_view.parking_ticket_view.get_ticket",
            args: {
                ticket: ticket
            },

            callback: (r) => {
                if (r.exc || !r.message) {
                    $(this.page.body).html(`
                        <div class="alert alert-danger">
                            Parking ticket could not be found.
                        </div>
                    `);
                    return;
                }

                this.render_ticket(r.message);
            },

            error: () => {
                $(this.page.body).html(`
                    <div class="alert alert-danger">
                        Could not connect to the server.
                    </div>
                `);
            }
        });
    }

    render_ticket(ticket) {
        $(this.page.body).html(`
            <div class="container py-4">
                <div class="card p-4 mx-auto" style="max-width: 600px;">

                    <h2 class="mb-4 text-center">
                        Parking Ticket
                    </h2>

                    <div class="mb-3">
                        <strong>Parking Token</strong>
                        <div>${ticket.parking_token || ""}</div>
                    </div>

                    <div class="mb-3">
                        <strong>Vehicle Number</strong>
                        <div>${ticket.vehicle_number || ""}</div>
                    </div>

                    <div class="mb-3">
                        <strong>Vehicle Type</strong>
                        <div>${ticket.vehicle_type || ""}</div>
                    </div>

                    <div class="mb-3">
                        <strong>Status</strong>
                        <div>${ticket.status || ""}</div>
                    </div>

                    <div class="mb-3">
                        <strong>Check In</strong>
                        <div>${ticket.check_in_time || ""}</div>
                    </div>

                    ${
                        ticket.check_out_time
                            ? `
                                <div class="mb-3">
                                    <strong>Check Out</strong>
                                    <div>${ticket.check_out_time}</div>
                                </div>
                            `
                            : ""
                    }

                    ${
                        ticket.status === "Parked"
                            ? `
                                <button
                                    class="btn btn-primary w-100"
                                    id="request-vehicle">
                                    Request My Vehicle
                                </button>
                            `
                            : ""
                    }

                </div>
            </div>
        `);

        $("#request-vehicle").on("click", () => {
            this.request_vehicle(ticket.name);
        });
    }

    request_vehicle(ticket_name) {
        frappe.call({
            method: "valet.valet_parking.page.valet_attendant.valet_attendant.request_vehicle",

            args: {
                ticket: ticket_name
            },

            callback: (r) => {
                if (r.exc) {
                    frappe.msgprint("Failed to request vehicle.");
                    return;
                }

                frappe.show_alert({
                    message: "Vehicle retrieval requested",
                    indicator: "green"
                });

                setTimeout(() => {
                    this.load_ticket();
                }, 500);
            }
        });
    }
}
