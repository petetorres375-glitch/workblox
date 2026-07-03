import csv
import io
import re

REASON_MISSING_NAME    = "Missing name"
REASON_MALFORMED_VCARD = "Malformed vCard block"
REASON_UNREADABLE_ROW  = "Unreadable row"


def parse_vcf(text: str) -> tuple[list[dict], list[dict]]:
    contacts, skipped = [], []
    blocks = re.split(r'BEGIN:VCARD', text, flags=re.IGNORECASE)
    row_num = 0
    for block in blocks:
        if not block.strip():
            continue
        row_num += 1
        end = block.upper().find('END:VCARD')
        if end != -1:
            block = block[:end]
        raw = " ".join(block.split())[:150]
        try:
            c = _parse_vcard_block(block)
        except Exception:
            skipped.append({"row": row_num, "raw": raw, "reason": REASON_MALFORMED_VCARD})
            continue
        if c["first_name"] or c["last_name"]:
            c["valid"], c["reason"] = True, None
        else:
            c["valid"], c["reason"] = False, REASON_MISSING_NAME
        c["row"] = row_num
        contacts.append(c)
    return contacts, skipped


def _unfold(text: str) -> str:
    return re.sub(r'\r?\n[ \t]', '', text)


def _parse_vcard_block(block: str) -> dict:
    block = _unfold(block)
    first_name = last_name = middle_init = company = ""
    phones, emails = [], []
    street = apt = city = state = zip_code = ""

    for line in block.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        field_part, _, value = line.partition(':')
        field_name = field_part.split(';')[0].upper().strip()
        value = value.strip()

        if field_name == 'N':
            parts = value.split(';')
            last_name  = parts[0].strip() if len(parts) > 0 else ""
            first_name = parts[1].strip() if len(parts) > 1 else ""
            middle     = parts[2].strip() if len(parts) > 2 else ""
            middle_init = middle[0] if middle else ""
        elif field_name == 'FN' and not first_name and not last_name:
            parts = value.rsplit(' ', 1)
            first_name = parts[0].strip() if len(parts) == 2 else value
            last_name  = parts[1].strip() if len(parts) == 2 else ""
        elif field_name == 'ORG':
            company = value.split(';')[0].strip()
        elif field_name == 'TEL':
            phone = _clean_phone(value)
            if phone and phone not in phones:
                phones.append(phone)
        elif field_name == 'EMAIL':
            email = value.lower().strip()
            if email and email not in emails:
                emails.append(email)
        elif field_name == 'ADR':
            parts = value.split(';')
            if len(parts) >= 7:
                street   = parts[2].strip()
                apt      = parts[1].strip()
                city     = parts[3].strip()
                state    = parts[4].strip()
                zip_code = parts[5].strip()
            elif len(parts) >= 5:
                street = parts[2].strip() if len(parts) > 2 else ""
                city   = parts[3].strip() if len(parts) > 3 else ""
                state  = parts[4].strip() if len(parts) > 4 else ""

    return {
        "first_name": first_name, "last_name": last_name, "middle_init": middle_init,
        "company": company, "contact_type": "Other",
        "phones": phones, "emails": emails,
        "street": street, "apt": apt, "city": city, "state": state, "zip": zip_code,
        "notes": "",
    }


def _clean_phone(phone: str) -> str:
    digits = re.sub(r'[^\d+]', '', phone)
    if digits.startswith('+1') and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone.strip()


_HEADER_MAP = {
    'given name': 'first_name',   'first name': 'first_name',
    'firstname':  'first_name',   'first': 'first_name',
    'family name': 'last_name',   'last name': 'last_name',
    'lastname':    'last_name',   'last': 'last_name',   'surname': 'last_name',
    'additional name': 'middle_init', 'middle name': 'middle_init',
    'middle initial':  'middle_init', 'middle': 'middle_init',
    'organization': 'company', 'company': 'company',
    'employer': 'company',     'business name': 'company',
    'phone': 'phone',          'mobile phone': 'phone',
    'home phone': 'phone',     'work phone': 'phone',
    'cell phone': 'phone',     'business phone': 'phone',
    'cell': 'phone',           'mobile': 'phone',       'telephone': 'phone',
    'e-mail address': 'email', 'email address': 'email',
    'email': 'email',          'e-mail': 'email',
    'street': 'street',        'address': 'street',
    'home street': 'street',   'business street': 'street',
    'city': 'city',            'home city': 'city',     'business city': 'city',
    'state': 'state',          'home state': 'state',   'business state': 'state',
    'region': 'state',         'province': 'state',
    'zip': 'zip',              'postal code': 'zip',    'zip code': 'zip',
    'home postal code': 'zip', 'business postal code': 'zip',
    'notes': 'notes',          'note': 'notes',         'description': 'notes',
}


def _build_csv_contact(row: dict, header_map: dict) -> dict:
    c = {
        "first_name": "", "last_name": "", "middle_init": "",
        "company": "", "contact_type": "Other",
        "phones": [], "emails": [],
        "street": "", "apt": "", "city": "", "state": "", "zip": "", "notes": "",
    }
    for field, value in row.items():
        if not value or field not in header_map:
            continue
        target = header_map[field]
        value = value.strip()
        if target == 'phone':
            phone = _clean_phone(value)
            if phone and phone not in c['phones']:
                c['phones'].append(phone)
        elif target == 'email':
            email = value.lower()
            if email and email not in c['emails']:
                c['emails'].append(email)
        elif target == 'middle_init':
            c['middle_init'] = value[0] if value else ""
        elif target in c:
            c[target] = value
    return c


def parse_csv(text: str) -> tuple[list[dict], list[dict]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], []

    header_map = {}
    for field in reader.fieldnames:
        norm = field.strip().lower()
        if norm in _HEADER_MAP:
            header_map[field] = _HEADER_MAP[norm]
        elif re.match(r'phone \d+', norm):
            header_map[field] = 'phone'
        elif re.match(r'e-?mail \d+', norm):
            header_map[field] = 'email'
        elif re.match(r'organization \d+ - name', norm):
            header_map[field] = 'company'

    contacts, skipped = [], []
    row_iter = iter(reader)
    row_num = 0
    while True:
        row_num += 1
        try:
            row = next(row_iter)
        except StopIteration:
            break
        except Exception:
            skipped.append({"row": row_num, "raw": "", "reason": REASON_UNREADABLE_ROW})
            continue

        try:
            c = _build_csv_contact(row, header_map)
        except Exception:
            raw = ", ".join(str(v) for v in list(row.values())[:4] if v)
            skipped.append({"row": row_num, "raw": raw[:150], "reason": REASON_UNREADABLE_ROW})
            continue

        if c["first_name"] or c["last_name"]:
            c["valid"], c["reason"] = True, None
        else:
            c["valid"], c["reason"] = False, REASON_MISSING_NAME
        c["row"] = row_num
        contacts.append(c)

    return contacts, skipped
