import io
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, g, send_file

from .. import db, limiter
from ..models import Contact, User
from ..services.contact_parser import parse_vcf, parse_csv

bp = Blueprint("contacts", __name__, url_prefix="/api/biz/contacts")

CONTACT_TYPES = ["Client", "Vendor", "Partner", "Employee", "Personal", "Other"]


def _require_business():
    if g.user.get("plan") != "business":
        return jsonify({"error": "Business subscription required"}), 403
    return None


def _user_id():
    sub = g.user.get("sub")
    if not sub:
        return None
    user = User.query.filter_by(email=sub).first()
    return user.id if user else None


def _to_dict(c: Contact) -> dict:
    return {
        "id":           c.id,
        "first_name":   c.first_name,
        "last_name":    c.last_name,
        "middle_init":  c.middle_init or "",
        "company":      c.company or "",
        "contact_type": c.contact_type,
        "phones":       json.loads(c.phones) if c.phones else [],
        "emails":       json.loads(c.emails) if c.emails else [],
        "street":       c.street or "",
        "apt":          c.apt or "",
        "city":         c.city or "",
        "state":        c.state or "",
        "zip":          c.zip or "",
        "notes":        c.notes or "",
    }


def _contact_from_body(body: dict, contact: Contact = None) -> Contact:
    if contact is None:
        contact = Contact()
    contact.first_name   = (body.get("first_name") or "").strip()
    contact.last_name    = (body.get("last_name") or "").strip()
    contact.middle_init  = (body.get("middle_init") or "").strip() or None
    contact.company      = (body.get("company") or "").strip() or None
    contact.contact_type = body.get("contact_type", "Client")
    contact.phones       = json.dumps(body.get("phones") or [])
    contact.emails       = json.dumps(body.get("emails") or [])
    contact.street       = (body.get("street") or "").strip() or None
    contact.apt          = (body.get("apt") or "").strip() or None
    contact.city         = (body.get("city") or "").strip() or None
    contact.state        = (body.get("state") or "").strip() or None
    contact.zip          = (body.get("zip") or "").strip() or None
    contact.notes        = (body.get("notes") or "").strip() or None
    return contact


# ── Parse (no DB write) ────────────────────────────────────────────────────────

@bp.post("/parse")
@limiter.limit("20 per hour")
def parse():
    err = _require_business()
    if err:
        return err
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    file = request.files["file"]
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".vcf", ".csv"):
        return jsonify({"error": "Only .vcf and .csv files are supported"}), 415
    try:
        text = file.read().decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 422
    try:
        contacts = parse_vcf(text) if ext == ".vcf" else parse_csv(text)
    except Exception as e:
        return jsonify({"error": f"Parse error: {e}"}), 422
    return jsonify({"contacts": contacts, "count": len(contacts)})


# ── Bulk import ────────────────────────────────────────────────────────────────

@bp.post("/import")
@limiter.limit("10 per hour")
def import_contacts():
    err = _require_business()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    items = body.get("contacts", [])
    if not items:
        return jsonify({"error": "No contacts to import"}), 400
    user_id = _user_id()
    for item in items:
        contact = _contact_from_body(item)
        contact.user_id = user_id
        db.session.add(contact)
    db.session.commit()
    return jsonify({"imported": len(items)})


# ── List / search ──────────────────────────────────────────────────────────────

@bp.get("")
@limiter.limit("120 per hour")
def list_contacts():
    err = _require_business()
    if err:
        return err
    user_id      = _user_id()
    q            = (request.args.get("q") or "").strip().lower()
    contact_type = (request.args.get("type") or "").strip()

    query = Contact.query.filter_by(user_id=user_id)
    if contact_type and contact_type != "All":
        query = query.filter_by(contact_type=contact_type)
    contacts = query.order_by(Contact.last_name, Contact.first_name).all()

    if q:
        contacts = [c for c in contacts if (
            q in c.first_name.lower() or
            q in c.last_name.lower() or
            (c.company and q in c.company.lower()) or
            (c.phones and q in c.phones.lower()) or
            (c.emails and q in c.emails.lower())
        )]
    return jsonify({"contacts": [_to_dict(c) for c in contacts]})


# ── Add single contact ─────────────────────────────────────────────────────────

@bp.post("")
@limiter.limit("60 per hour")
def add_contact():
    err = _require_business()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    if not (body.get("first_name") or body.get("last_name")):
        return jsonify({"error": "first_name or last_name is required"}), 400
    contact = _contact_from_body(body)
    contact.user_id = _user_id()
    db.session.add(contact)
    db.session.commit()
    return jsonify(_to_dict(contact)), 201


# ── Edit contact ───────────────────────────────────────────────────────────────

@bp.put("/<int:cid>")
@limiter.limit("60 per hour")
def edit_contact(cid):
    err = _require_business()
    if err:
        return err
    contact = Contact.query.filter_by(id=cid, user_id=_user_id()).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    body = request.get_json(silent=True) or {}
    _contact_from_body(body, contact)
    db.session.commit()
    return jsonify(_to_dict(contact))


# ── Delete contact ─────────────────────────────────────────────────────────────

@bp.delete("/<int:cid>")
@limiter.limit("60 per hour")
def delete_contact(cid):
    err = _require_business()
    if err:
        return err
    contact = Contact.query.filter_by(id=cid, user_id=_user_id()).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"deleted": True})


# ── PDF export ─────────────────────────────────────────────────────────────────

@bp.post("/export/pdf")
@limiter.limit("20 per hour")
def export_pdf():
    err = _require_business()
    if err:
        return err

    from fpdf import FPDF

    body    = request.get_json(silent=True) or {}
    ids     = body.get("ids")  # list of IDs; None = export all
    user_id = _user_id()

    if ids:
        contacts = (Contact.query
            .filter(Contact.user_id == user_id, Contact.id.in_(ids))
            .order_by(Contact.last_name, Contact.first_name).all())
    else:
        contacts = (Contact.query
            .filter_by(user_id=user_id)
            .order_by(Contact.last_name, Contact.first_name).all())

    if not contacts:
        return jsonify({"error": "No contacts to export"}), 400

    FONT_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")
    FONT_REG  = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

    C_INK  = (15,  23,  42)
    C_BLUE = (37,  99, 235)
    C_SOFT = (100, 116, 139)
    C_RULE = (226, 232, 240)
    W = 180

    class _PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.add_font("DJ", "",  FONT_REG)
            self.add_font("DJ", "B", FONT_BOLD)

        def footer(self):
            self.set_y(-14)
            self.set_font("DJ", "", 7.5)
            self.set_text_color(*C_SOFT)
            now = datetime.now().strftime("%B %d, %Y")
            self.cell(W, 5, f"Contacts — Workblox Business  |  {now}", align="C")

    pdf = _PDF()
    pdf.set_auto_page_break(True, 20)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # Header banner
    pdf.set_fill_color(*C_INK)
    pdf.rect(0, 0, 210, 26, "F")
    pdf.set_xy(15, 7)
    pdf.set_font("DJ", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W, 7, "Contact Directory")
    pdf.ln(8)
    pdf.set_x(15)
    pdf.set_font("DJ", "", 8.5)
    pdf.set_text_color(180, 190, 210)
    count_label = f"{len(contacts)} contact{'s' if len(contacts) != 1 else ''}"
    now = datetime.now().strftime("%B %d, %Y  %H:%M")
    pdf.cell(W, 5, f"{count_label}   |   {now}   |   Workblox Business")
    pdf.ln(16)

    for c in contacts:
        phones = json.loads(c.phones) if c.phones else []
        emails = json.loads(c.emails) if c.emails else []

        name_parts = [p for p in [c.first_name, (c.middle_init + ".") if c.middle_init else "", c.last_name] if p]
        name = " ".join(name_parts).strip()

        pdf.set_font("DJ", "B", 11)
        pdf.set_text_color(*C_BLUE)
        pdf.cell(W, 6, name)
        pdf.ln(6)

        if c.company:
            pdf.set_font("DJ", "", 9.5)
            pdf.set_text_color(*C_SOFT)
            pdf.cell(W, 5, c.company)
            pdf.ln(5)

        pdf.set_font("DJ", "", 8.5)
        pdf.set_text_color(*C_SOFT)
        pdf.cell(W, 4, c.contact_type)
        pdf.ln(5)

        pdf.set_font("DJ", "", 9.5)
        pdf.set_text_color(*C_INK)

        for phone in phones:
            pdf.cell(W, 5, phone)
            pdf.ln(5)
        for email in emails:
            pdf.cell(W, 5, email)
            pdf.ln(5)

        address_lines = []
        if c.street:
            address_lines.append(c.street + (f", {c.apt}" if c.apt else ""))
        loc = ", ".join(p for p in [c.city, c.state] if p)
        if c.zip:
            loc = (loc + " " + c.zip).strip()
        if loc:
            address_lines.append(loc)
        for line in address_lines:
            pdf.cell(W, 5, line)
            pdf.ln(5)

        if c.notes:
            pdf.set_font("DJ", "", 8.5)
            pdf.set_text_color(*C_SOFT)
            pdf.multi_cell(W, 5, f"Note: {c.notes}")

        pdf.ln(3)
        pdf.set_draw_color(*C_RULE)
        pdf.set_line_width(0.3)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    if len(contacts) == 1:
        stem = (contacts[0].last_name or contacts[0].first_name or "contact").lower()
    else:
        stem = "contacts_directory"

    return send_file(buf, as_attachment=True,
        download_name=f"{stem}.pdf",
        mimetype="application/pdf")
