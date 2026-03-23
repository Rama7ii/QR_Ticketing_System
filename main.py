from flask import Flask, jsonify, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode, os, random, string
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.pagesizes import letter
from sqlalchemy import inspect, text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_ticketing.db'
db = SQLAlchemy(app)

STATUS_UNUSED = "unused"
STATUS_USED = "used"
RESPONSE_VALID = "VALID"
RESPONSE_INVALID = "INVALID"
RESPONSE_ALREADY_USED = "ALREADY USED"


class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(10), unique=True, nullable=False)
    f_name = db.Column(db.String(50), nullable=False)
    l_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False, default=STATUS_UNUSED)
    used_at = db.Column(db.DateTime, nullable=True)


def initialize_database():
    db.create_all()

    inspector = inspect(db.engine)
    if not inspector.has_table(FormData.__tablename__):
        return

    columns = {column['name'] for column in inspector.get_columns(FormData.__tablename__)}
    with db.engine.begin() as connection:
        if 'status' not in columns:
            connection.execute(
                text(
                    f"ALTER TABLE {FormData.__tablename__} "
                    f"ADD COLUMN status VARCHAR(10) NOT NULL DEFAULT '{STATUS_UNUSED}'"
                )
            )
        if 'used_at' not in columns:
            connection.execute(
                text(
                    f"ALTER TABLE {FormData.__tablename__} "
                    "ADD COLUMN used_at DATETIME"
                )
            )


def extract_ticket_id(qr_data):
    if not qr_data:
        return ""

    for line in str(qr_data).splitlines():
        if line.startswith('Ticket ID:'):
            return line.split(':', 1)[1].strip()

    return str(qr_data).strip()


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f_name = request.form['f_name']
        l_name = request.form['l_name']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        phone_number = request.form['phone_number']

        if len(phone_number) > 10:
            return render_template("index.html", error="Phone number cannot be longer than 10 digits")

        ticket_id = generate_ticket_id()
        form_data = FormData(
            ticket_id=ticket_id,
            f_name=f_name,
            l_name=l_name,
            dob=dob,
            phone_number=phone_number,
            status=STATUS_UNUSED,
        )

        db.session.add(form_data)
        db.session.commit()

        generate_qr_code(ticket_id, f_name, l_name, dob)
        return render_template("success.html", ticket_id=ticket_id)

    return render_template("index.html")


def generate_ticket_id():
    while True:
        random_id = ''.join(random.choices(string.digits, k=10))
        if not FormData.query.filter_by(ticket_id=random_id).first():
            return random_id


def generate_qr_code(ticket_id, f_name, l_name, dob):
    data = f'Ticket ID: {ticket_id}\nName: {f_name} {l_name}\nDOB: {dob.strftime("%Y-%m-%d")}'
    img = qrcode.make(data)
    img.save(f"static/qrcodes/{ticket_id}.png")


@app.route("/get", methods=['GET'])
def get_data():
    data = FormData.query.all()
    return render_template("get_data.html", data=data)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/validate", methods=['POST'])
def validate_ticket_route():
    payload = request.get_json(silent=True) or request.form
    qr_data = payload.get('qr_data') or payload.get('ticket_id')

    result = validate_ticket(qr_data)
    return jsonify(result)


@app.route("/pdf/<ticket_id>")
def download_pdf(ticket_id):
    pdf_filename = f"ticket_{ticket_id}.pdf"
    pdf_path = generate_pdf(ticket_id, pdf_filename)
    return send_file(pdf_path, as_attachment=True)


def validate_ticket(qr_data):
    ticket_id = extract_ticket_id(qr_data)
    ticket = FormData.query.filter_by(ticket_id=ticket_id).first()

    if not ticket:
        return {"status": RESPONSE_INVALID, "ticket_id": ticket_id}

    if ticket.status == STATUS_USED:
        return {
            "status": RESPONSE_ALREADY_USED,
            "ticket_id": ticket.ticket_id,
            "used_at": ticket.used_at.isoformat() if ticket.used_at else None,
        }

    ticket.status = STATUS_USED
    ticket.used_at = datetime.utcnow()
    db.session.commit()

    return {
        "status": RESPONSE_VALID,
        "ticket_id": ticket.ticket_id,
        "used_at": ticket.used_at.isoformat(),
    }


def generate_pdf(ticket_id, filename):
    pdf_dir = os.path.join(app.root_path, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)

    pdf_path = os.path.join(pdf_dir, filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(letter[0] / 2, letter[1] - 50, "QR TICKETING SYSTEM")

    c.setFont("Helvetica", 12)
    form_data = FormData.query.filter_by(ticket_id=ticket_id).first()

    if form_data:
        c.drawString(100, 700, f"Ticket ID: {form_data.ticket_id}")
        c.drawString(100, 680, f"Name: {form_data.f_name} {form_data.l_name}")
        c.drawString(100, 660, f"DOB: {form_data.dob.strftime('%Y-%m-%d')}")
        c.drawString(100, 640, f"Phone Number: {form_data.phone_number}")
        c.drawString(100, 620, f"Status: {form_data.status.upper()}")

        if form_data.used_at:
            c.drawString(100, 600, f"Used At: {form_data.used_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            qr_y_position = 530
        else:
            qr_y_position = 550

        img_path = f"static/qrcodes/{form_data.ticket_id}.png"
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            img_width = 100
            img_height = img_width / aspect_ratio
            c.drawInlineImage(img_path, 100, qr_y_position - img_height, width=img_width, height=img_height)

    c.setFont("Helvetica", 10)
    c.drawCentredString(letter[0] / 2, 30, "Made by Sarthak Lamba")
    c.drawCentredString(letter[0] / 2, 15, "Contact: samlamba29@gmail.com | LinkedIn: linkedin.com/in/sarthaklambaa")

    c.showPage()
    c.save()

    return pdf_path


with app.app_context():
    initialize_database()


if __name__ == '__main__':
    app.run(debug=False)
