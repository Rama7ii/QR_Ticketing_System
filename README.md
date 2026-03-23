# QR Ticketing System

Welcome to the QR Ticketing System repository! This project is a minimal yet effective solution for generating and managing electronic tickets using Python, HTML, CSS, and SQLite3. The system allows users to input their information, generates a unique ticket ID, and provides a downloadable PDF containing a QR code for easy verification.

## Features

- **User Information Input:** Collects user's name, date of birth, and phone number for ticket generation.
- **Unique Ticket ID:** Generates a unique ticket ID for each user.
- **QR Code Generation:** Creates a QR code for each booking, facilitating quick and secure access to events and venues.
- **PDF Download:** Allows users to download a PDF containing the QR code for their ticket.
- **Slot Booking (Future Enhancement):** The system supports slot booking for specific time slots, enabling personal usage for events with limited seating or for booking appointments.

## Disclaimer & Contributions
Note: This repository is a fork of the original QR Ticketing System by Sarthak Lamba.
I am not the original creator. This fork includes my own contributions and enhancements, including:
Persistent ticket scan tracking with status and timestamps
Secure staff scanning dashboard with login access
QR code validation and reset functionality
Detailed Excel report generation for scanned tickets
Updated README and documentation
All original features of the QR Ticketing System are maintained, and my changes aim to improve usability for event management and reporting.

## How to Use

1. Clone the repository: `git clone https://github.com/your-username/QR_Ticketing_System.git`
2. Navigate to the project directory: `cd QR_Ticketing_System`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`
5. Access the application in your web browser at `http://localhost:5000`

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/QR_Ticketing_System.git

# Navigate to the project directory
cd QR_Ticketing_System

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Connect with me
Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/sarthaklambaa/). <br>
For any inquiries or suggestions, you can reach out to me via email: samlamba29@gmail.com.

I welcome your feedback and contributions to enhance this QR Ticketing System.<br>
Happy coding!!

## Ticket Validation API

The backend now supports persistent ticket validation with SQLite-backed status tracking.

- New tickets are created with status `unused`.
- `POST /validate` checks a scanned QR payload or raw `ticket_id`.
- Responses are returned as JSON with one of these values in `status`:
  - `VALID`
  - `INVALID`
  - `ALREADY USED`
- Once a ticket is validated, it is marked as `used` and the optional `used_at` timestamp is stored permanently.

Example JSON request:

```json
{"ticket_id": "1234567890"}
```

You can also send the full QR text using the `qr_data` field.
