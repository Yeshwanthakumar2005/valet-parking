frappe.pages["valet-attendant"].on_page_load = function (wrapper) {
    new ValetAttendantPage(wrapper);
};

class ValetAttendantPage {
    constructor(wrapper) {
        this.wrapper = $(wrapper);

        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Valet Attendant",
            single_column: true
        });

        this.make();
        this.load_tickets();
    }

    make() {
        this.$content = $(`
            <div class="valet-dashboard">

                <div class="row mb-4">

                    <div class="col-md-3">
                        <div class="card p-3">
                            <h5>Awaiting Parking</h5>
                            <h2 id="awaiting-count">0</h2>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="card p-3">
                            <h5>Parked</h5>
                            <h2 id="parked-count">0</h2>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="card p-3">
                            <h5>Retrieval Requests</h5>
                            <h2 id="retrieval-count">0</h2>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="card p-3">
                            <h5>On The Way</h5>
                            <h2 id="way-count">0</h2>
                        </div>
                    </div>

                </div>

                <div id="tickets"></div>

            </div>
        `);

        $(this.page.body).append(this.$content);
    }

    load_tickets() {
        console.log("Loading tickets...");

        frappe.call({
            method: "valet.valet_parking.page.valet_attendant.valet_attendant.get_tickets",

            callback: (r) => {
                console.log("GET TICKETS RESPONSE:", r);

                if (r.exc) {
                    console.error("GET TICKETS ERROR:", r.exc);
                    frappe.msgprint("Failed to load parking tickets.");
                    return;
                }

                this.render_tickets(r.message || []);
            },

            error: (err) => {
                console.error("GET TICKETS REQUEST ERROR:", err);
                frappe.msgprint("Could not connect to server.");
            }
        });
    }

    render_tickets(tickets) {

        const counts = {
            "Awaiting Parking": 0,
            "Parked": 0,
            "Retrieval Requested": 0,
            "On The Way": 0,
            "Delivered": 0
        };

        tickets.forEach(ticket => {
            if (counts[ticket.status] !== undefined) {
                counts[ticket.status]++;
            }
        });

        $("#awaiting-count").text(counts["Awaiting Parking"]);
        $("#parked-count").text(counts["Parked"]);
        $("#retrieval-count").text(counts["Retrieval Requested"]);
        $("#way-count").text(counts["On The Way"]);

        let html = "";

        tickets.forEach(ticket => {

            html += `
                <div class="card mb-3 p-3">

                    <div class="row align-items-center">

                        <div class="col-md-2">
                            <strong>${ticket.parking_token || ""}</strong>
                        </div>

                        <div class="col-md-2">
                            Vehicle: ${ticket.vehicle_number || ""}
                        </div>

                        <div class="col-md-2">
                            Type: ${ticket.vehicle_type || ""}
                        </div>

                        <div class="col-md-2">
                            Status:
                            <strong>${ticket.status || ""}</strong>
                        </div>

                        <div class="col-md-4">
                            ${this.get_buttons(ticket)}
                        </div>

                    </div>

                </div>
            `;
        });

        if (!html) {
            html = `
                <div class="alert alert-info">
                    No parking tickets found.
                </div>
            `;
        }

        $("#tickets").html(html);

        this.bind_buttons();
    }

    get_buttons(ticket) {

        if (ticket.status === "Awaiting Parking") {
            return `
                <button
                    class="btn btn-primary update-status"
                    data-ticket="${ticket.name}"
                    data-status="Parked">
                    Mark Parked
                </button>
            `;
        }

        if (ticket.status === "Retrieval Requested") {
            return `
                <button
                    class="btn btn-primary update-status"
                    data-ticket="${ticket.name}"
                    data-status="On The Way">
                    Mark On The Way
                </button>
            `;
        }

        if (ticket.status === "On The Way") {
            return `
                <button
                    class="btn btn-success update-status"
                    data-ticket="${ticket.name}"
                    data-status="Delivered">
                    Mark Delivered
                </button>
            `;
        }

        return "";
    }

    bind_buttons() {

        $(".update-status").off("click").on("click", (e) => {

            const button = $(e.currentTarget);

            const ticket = button.attr("data-ticket");
            const status = button.attr("data-status");

            console.log("=================================");
            console.log("BUTTON CLICKED");
            console.log("Ticket:", ticket);
            console.log("New Status:", status);
            console.log("=================================");

            button.prop("disabled", true);
            button.text("Updating...");

            frappe.call({
                method: "valet.valet_parking.page.valet_attendant.valet_attendant.update_status",

                args: {
                    ticket: ticket,
                    status: status
                },

                callback: (r) => {

                    console.log("UPDATE RESPONSE:", r);

                    if (r.exc) {
                        console.error("UPDATE STATUS ERROR:", r.exc);

                        frappe.msgprint(
                            "Failed to update ticket. Check the browser console."
                        );

                        button.prop("disabled", false);
                        button.text("Try Again");

                        return;
                    }

                    if (!r.message) {
                        console.error("No response from server:", r);

                        frappe.msgprint("Server returned no response.");

                        button.prop("disabled", false);

                        return;
                    }

                    console.log("STATUS UPDATED:", r.message);

                    frappe.show_alert({
                        message: "Ticket updated to " + r.message.status,
                        indicator: "green"
                    });

                    this.load_tickets();
                },

                error: (err) => {

                    console.error("UPDATE REQUEST ERROR:", err);

                    frappe.msgprint(
                        "Server request failed. Check Terminal 1."
                    );

                    button.prop("disabled", false);
                    button.text("Try Again");
                }
            });
        });
    }
}
