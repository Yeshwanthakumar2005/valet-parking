# Valet Parking Management System

A Frappe-based valet parking management system that manages customers, parking tickets, QR-based vehicle retrieval requests, and valet attendant workflows.

## Project Overview

The system digitizes the valet parking process from vehicle check-in to vehicle delivery.

## Main Workflow

Customer
→ Parking Ticket
→ Parking Token + QR Code
→ Customer scans QR
→ Request My Vehicle
→ Retrieval Requested
→ Valet Attendant
→ On The Way
→ Delivered

## Features

- Customer management
- Vehicle details management
- Parking ticket creation
- Automatic parking token generation
- Check-in and check-out time tracking
- QR code generation
- Mobile QR scanning
- Public customer ticket page
- Request My Vehicle functionality
- Retrieval request tracking
- Valet attendant dashboard
- Vehicle status management

### Ticket Status Flow

```text
Awaiting Parking
       ↓
Parked
       ↓
Retrieval Requested
       ↓
On The Way
       ↓
Delivered
