"""Spanish ATS corpus.

Mirrors every key in en.py. Written for Spanish-language CVs, not translated
word-for-word from the English list, because ATS matching rewards the terms
that actually appear in real CVs:

* Tool and brand names stay in English ("Excel", "Outlook", "Salesforce",
  "POS", "CRM"), because that is how they appear in Spanish CVs. Translating
  "excel" to "sobresalir" would match prose and miss the skill entirely.
* Regional variants are both listed where they diverge ("computadora" and
  "ordenador", "hostelería" and "hotelería", "fontanería" and "plomería").
  Extra entries only add recall -- a CV that says either one matches.
* Skills are noun phrases ("trabajo en equipo", "atención al detalle") rather
  than adjectives, which sidesteps gender agreement -- "organizado" would miss
  "organizada" -- and is the more idiomatic register for a Spanish CV anyway.
* Action verbs are (display, [stems]) pairs. Spanish conjugates heavily, so
  the stem "gestion" catches gestioné / gestionar / gestionado / gestión while
  the user still sees "gestionar" in the report.

Accents are written properly here. Matching folds accents on both sides, so
these entries also match CVs that drop them, which is common.

Category and section KEYS are the English identifiers on purpose -- they are
looked up by name in scoring. CATEGORY_LABELS and SECTION_LABELS carry the
Spanish display text.

Register is neutral Latin American Spanish, since that is the larger audience
for US-market job applications. Peninsular variants are included in the match
lists so a CV from Spain is not penalised.
"""

KEYWORDS = {
    "Technical Skills": [
        "microsoft office", "excel", "word", "powerpoint", "outlook", "google sheets",
        "google docs", "google forms", "entrada de datos", "quickbooks", "zoom", "slack",
        "trello", "asana", "wordpress",
    ],
    "Soft Skills": [
        "comunicación", "trabajo en equipo", "liderazgo", "resolución de problemas",
        "gestión del tiempo", "atención al detalle", "organización", "fiabilidad",
        "multitarea", "servicio al cliente", "adaptabilidad", "automotivación",
        "pensamiento crítico", "colaboración", "resolución de conflictos",
    ],
    "Action Verbs": [
        ("gestionar", ["gestion"]), ("administrar", ["administr"]),
        ("desarrollar", ["desarroll"]), ("crear", ["cre"]), ("liderar", ["lider"]),
        ("dirigir", ["dirig"]), ("mejorar", ["mejor"]), ("aumentar", ["aument"]),
        ("reducir", ["reduc"]), ("diseñar", ["diseñ", "disen"]),
        ("implementar", ["implement"]), ("coordinar", ["coordin"]),
        ("analizar", ["analiz"]), ("entregar", ["entreg"]), ("lograr", ["logr"]),
        ("capacitar", ["capacit"]), ("formar", ["formar", "formó", "formé"]),
        ("mantener", ["manten"]), ("optimizar", ["optimiz"]), ("generar", ["gener"]),
        ("lanzar", ["lanz"]), ("negociar", ["negoci"]), ("supervisar", ["supervis"]),
        ("apoyar", ["apoy"]), ("proporcionar", ["proporcion"]), ("asistir", ["asist"]),
        ("organizar", ["organiz"]), ("planificar", ["planific"]),
        ("ejecutar", ["ejecut"]), ("resolver", ["resolv", "resolu"]),
    ],
    "Resume Essentials": [
        "experiencia", "educación", "habilidades", "resumen", "objetivo",
        "certificaciones", "referencias", "voluntariado", "logros", "proyectos",
    ],
}

CATEGORY_LABELS = {
    "Technical Skills":  "Habilidades técnicas",
    "Soft Skills":       "Habilidades blandas",
    "Action Verbs":      "Verbos de acción",
    "Resume Essentials": "Elementos esenciales del CV",
}

JOB_KEYWORDS = {
    # --- Oficina y administración ---
    "administrative assistant": [
        "soporte administrativo", "gestión de agenda", "programación de citas",
        "correspondencia", "archivo", "microsoft office", "excel", "word", "outlook",
        "entrada de datos", "organización", "multitarea", "comunicación",
        "atención al detalle", "gestión de oficina", "viajes corporativos",
        "informes de gastos", "confidencialidad",
    ],
    "executive assistant": [
        "soporte ejecutivo", "gestión de agenda", "programación de citas",
        "viajes corporativos", "correspondencia", "confidencialidad", "microsoft office",
        "reuniones de directorio", "consejo de administración", "informes de gastos",
        "coordinación de proyectos", "partes interesadas", "discreción", "comunicación",
        "organización", "priorización",
    ],
    "receptionist": [
        "recepción", "atención telefónica", "centralita", "servicio al cliente",
        "programación de citas", "gestión de agenda", "microsoft office", "organización",
        "comunicación", "multitarea", "profesionalismo", "recibimiento de visitantes",
        "gestión de correo electrónico", "entrada de datos",
    ],
    "office manager": [
        "gestión de oficina", "administración", "programación de turnos",
        "gestión de proveedores", "presupuestos", "microsoft office", "organización",
        "liderazgo", "comunicación", "instalaciones", "pedidos de suministros",
        "incorporación de personal", "políticas", "procedimientos",
    ],
    "data entry": [
        "entrada de datos", "captura de datos", "precisión", "hoja de cálculo", "excel",
        "google sheets", "mecanografía", "atención al detalle", "organización",
        "quickbooks", "base de datos", "gestión de registros", "integridad de datos",
        "microsoft office",
    ],
    "virtual assistant": [
        "asistente virtual", "gestión de agenda", "gestión de correo electrónico",
        "entrada de datos", "comunicación", "organización", "microsoft office", "zoom",
        "trello", "asana", "trabajo remoto", "investigación", "redes sociales",
        "atención al cliente", "facturación",
    ],
    # --- Atención al cliente ---
    "customer service": [
        "servicio al cliente", "atención al cliente", "comunicación",
        "resolución de problemas", "crm", "salesforce", "soporte telefónico",
        "soporte por correo", "resolución de conflictos", "empatía", "paciencia",
        "satisfacción del cliente", "retención de clientes", "tickets", "zendesk",
        "mesa de ayuda", "seguimiento",
    ],
    "call center": [
        "centro de llamadas", "call center", "llamadas entrantes", "llamadas salientes",
        "soporte telefónico", "crm", "salesforce", "servicio al cliente", "comunicación",
        "desescalada", "resolución de conflictos", "alto volumen", "multitarea",
        "empatía", "guiones de atención", "métricas", "kpi",
    ],
    "sales associate": [
        "ventas", "servicio al cliente", "conocimiento del producto", "venta adicional",
        "venta cruzada", "punto de venta", "pos", "manejo de efectivo", "inventario",
        "comunicación", "orientación a resultados", "cuota de ventas",
        "trabajo en equipo", "comercio minorista", "merchandising",
    ],
    "retail associate": [
        "comercio minorista", "tienda", "servicio al cliente", "manejo de efectivo",
        "punto de venta", "pos", "inventario", "reposición de mercancía", "merchandising",
        "conocimiento del producto", "venta adicional", "trabajo en equipo",
        "comunicación", "prevención de pérdidas",
    ],
    "cashier": [
        "manejo de efectivo", "caja registradora", "arqueo de caja", "punto de venta",
        "pos", "servicio al cliente", "precisión", "transacciones",
        "comercio minorista", "comunicación", "trabajo en equipo", "ritmo acelerado",
        "responsabilidad", "puntualidad",
    ],
    # --- Alimentos y hostelería ---
    "event server": [
        "alta cocina", "banquetes", "catering", "hostelería", "hotelería",
        "servicio al cliente", "servicio de alimentos", "manipulación de alimentos",
        "manipulador de alimentos", "bebidas alcohólicas", "servicio de bebidas",
        "canapés", "servicio en mesa", "bufé", "montaje de eventos", "desmontaje",
        "atención al huésped", "alto volumen", "emplatado", "presentación", "vinos",
        "puntualidad", "fiabilidad", "bilingüe", "comunicación", "trabajo en equipo",
        "atención al detalle",
    ],
    "hospitality": [
        "alta cocina", "banquetes", "catering", "hostelería", "hotelería",
        "servicio al cliente", "servicio de alimentos", "manipulación de alimentos",
        "manipulador de alimentos", "bebidas alcohólicas", "servicio de bebidas",
        "canapés", "servicio en mesa", "bufé", "montaje de eventos", "desmontaje",
        "atención al huésped", "alto volumen", "emplatado", "presentación", "vinos",
        "puntualidad", "fiabilidad", "bilingüe", "comunicación", "trabajo en equipo",
        "atención al detalle",
    ],
    "server": [
        "servicio de alimentos", "servicio al cliente", "conocimiento del menú",
        "venta adicional", "punto de venta", "manejo de efectivo", "trabajo en equipo",
        "comunicación", "multitarea", "manipulación de alimentos", "bebidas alcohólicas",
        "ritmo acelerado", "satisfacción del huésped", "tareas de apoyo",
    ],
    "barista": [
        "espresso", "café", "arte latte", "punto de venta", "manejo de efectivo",
        "servicio al cliente", "manipulación de alimentos", "ritmo acelerado",
        "trabajo en equipo", "comunicación", "limpieza", "preparación de bebidas",
        "inventario", "apertura", "cierre",
    ],
    "cook": [
        "preparación de alimentos", "manejo de cuchillos", "seguridad alimentaria",
        "servsafe", "manipulador de alimentos", "cocinero de línea",
        "cocinero de preparación", "recetas", "control de porciones", "sanidad",
        "ritmo acelerado", "trabajo en equipo", "inventario", "limpieza",
        "mise en place",
    ],
    "restaurant manager": [
        "gestión de restaurante", "servicio de alimentos", "programación de turnos",
        "inventario", "seguridad alimentaria", "servsafe", "servicio al cliente",
        "liderazgo", "capacitación", "presupuestos", "control de costos",
        "punto de venta", "gestión de personal", "comunicación",
    ],
    # --- Almacén y logística ---
    "warehouse associate": [
        "almacén", "montacargas", "transpaleta", "inventario", "envíos",
        "recepción de mercancía", "preparación de pedidos", "surtido de pedidos",
        "escáner rf", "seguridad", "levantamiento de cargas", "organización",
        "trabajo en equipo", "ritmo acelerado", "precisión",
    ],
    "forklift operator": [
        "montacargas", "certificación de montacargas", "transpaleta", "almacén",
        "inventario", "envíos", "recepción de mercancía", "seguridad", "escáner rf",
        "preparación de pedidos", "levantamiento de cargas", "organización", "precisión",
        "carretilla retráctil",
    ],
    "delivery driver": [
        "conducción", "reparto", "entrega a domicilio", "optimización de rutas",
        "servicio al cliente", "navegación", "gps", "licencia de conducir",
        "historial de conducción limpio", "inspección del vehículo",
        "gestión del tiempo", "comunicación", "puntualidad", "responsabilidad",
        "carga y descarga",
    ],
    "inventory specialist": [
        "gestión de inventario", "conteos cíclicos", "existencias", "envíos",
        "recepción de mercancía", "escáner rf", "precisión", "organización",
        "entrada de datos", "excel", "sistema de gestión de almacenes", "wms", "mermas",
        "conciliación",
    ],
    # --- Salud y cuidados ---
    "caregiver": [
        "cuidado personal", "cuidador", "actividades de la vida diaria",
        "higiene personal", "movilidad", "administración de medicamentos",
        "acompañamiento", "preparación de comidas", "primeros auxilios", "rcp",
        "paciencia", "empatía", "comunicación", "documentación", "adultos mayores",
    ],
    "home health aide": [
        "asistente de salud en el hogar", "cuidado en el hogar", "signos vitales",
        "actividades de la vida diaria", "higiene personal", "movilidad", "traslados",
        "administración de medicamentos", "preparación de comidas", "primeros auxilios",
        "rcp", "documentación", "empatía", "comunicación",
    ],
    "medical assistant": [
        "asistente médico", "signos vitales", "toma de muestras", "flebotomía",
        "historia clínica electrónica", "expediente médico", "programación de citas",
        "codificación médica", "facturación médica", "esterilización", "inyecciones",
        "atención al paciente", "hipaa", "comunicación",
    ],
    "certified nursing assistant": [
        "auxiliar de enfermería", "certificación cna", "signos vitales",
        "actividades de la vida diaria", "higiene del paciente", "movilidad",
        "traslados", "documentación", "atención al paciente", "control de infecciones",
        "empatía", "trabajo en equipo", "comunicación", "adultos mayores",
    ],
    "pharmacy technician": [
        "técnico de farmacia", "dispensación de medicamentos", "recetas",
        "inventario de farmacia", "conteo de medicamentos", "seguros médicos",
        "facturación", "atención al cliente", "hipaa", "precisión", "etiquetado",
        "control de existencias", "comunicación", "farmacología",
    ],
    # --- Limpieza y mantenimiento ---
    "housekeeper": [
        "limpieza", "ama de llaves", "housekeeping", "hotelería",
        "cambio de ropa de cama", "desinfección", "productos de limpieza", "aspirado",
        "atención al detalle", "gestión del tiempo", "discreción", "fiabilidad",
        "inventario de suministros", "áreas comunes",
    ],
    "janitor": [
        "conserje", "limpieza", "mantenimiento", "desinfección", "manejo de residuos",
        "pulido de pisos", "productos químicos de limpieza", "seguridad",
        "atención al detalle", "fiabilidad", "trabajo independiente",
        "inventario de suministros", "áreas comunes", "reparaciones menores",
    ],
    "maintenance technician": [
        "técnico de mantenimiento", "mantenimiento preventivo", "reparaciones",
        "fontanería", "plomería", "electricidad", "hvac", "climatización",
        "solución de problemas", "herramientas manuales", "seguridad",
        "órdenes de trabajo", "carpintería", "pintura", "documentación",
    ],
    # --- Educación y cuidado infantil ---
    "teacher assistant": [
        "asistente de maestro", "apoyo en el aula", "gestión del aula",
        "planificación de clases", "tutoría", "educación especial",
        "desarrollo infantil", "comunicación", "paciencia", "trabajo en equipo",
        "evaluación", "material didáctico", "seguridad de los estudiantes",
        "primeros auxilios",
    ],
    "childcare worker": [
        "cuidado infantil", "guardería", "desarrollo infantil",
        "actividades recreativas", "seguridad de los niños", "primeros auxilios", "rcp",
        "preparación de comidas", "higiene", "paciencia", "comunicación con los padres",
        "rutinas diarias", "supervisión", "educación temprana",
    ],
    "tutor": [
        "tutoría", "enseñanza", "planificación de clases", "matemáticas", "lectura",
        "preparación de exámenes", "evaluación", "paciencia", "comunicación",
        "aprendizaje personalizado", "seguimiento del progreso", "motivación",
        "material didáctico", "clases en línea",
    ],
    "security guard": [
        "guardia de seguridad", "vigilancia", "patrullaje", "control de acceso", "cctv",
        "circuito cerrado", "informes de incidentes", "respuesta ante emergencias",
        "primeros auxilios", "observación", "comunicación", "licencia de seguridad",
        "prevención de pérdidas", "control de multitudes",
    ],
    # --- Tecnología ---
    "web developer": [
        "html", "css", "javascript", "react", "diseño responsivo", "git",
        "control de versiones", "depuración", "api", "bases de datos", "wordpress",
        "seo", "rendimiento web", "accesibilidad", "desarrollo front-end",
    ],
    "it support": [
        "soporte técnico", "mesa de ayuda", "helpdesk", "solución de problemas",
        "windows", "active directory", "redes", "hardware", "software", "tickets",
        "instalación", "configuración", "respaldo de datos", "atención al usuario",
        "ciberseguridad",
    ],
    "social media manager": [
        "redes sociales", "gestión de contenido", "calendario editorial", "instagram",
        "facebook", "linkedin", "tiktok", "analítica", "interacción", "engagement",
        "campañas publicitarias", "redacción publicitaria", "marketing digital", "seo",
        "publicidad pagada",
    ],
    # --- Contabilidad ---
    "bookkeeper": [
        "contabilidad", "teneduría de libros", "quickbooks", "conciliación bancaria",
        "cuentas por pagar", "cuentas por cobrar", "nómina", "excel", "facturación",
        "estados financieros", "libro mayor", "precisión", "impuestos", "auditoría",
    ],
    "accounting clerk": [
        "auxiliar contable", "cuentas por pagar", "cuentas por cobrar",
        "entrada de datos", "conciliación", "facturación", "excel", "quickbooks",
        "libro mayor", "precisión", "archivo", "informes financieros", "nómina",
        "atención al detalle",
    ],
    # --- Oficios y trabajo general ---
    "general laborer": [
        "trabajo general", "obrero", "construcción", "levantamiento de cargas",
        "herramientas manuales", "seguridad", "limpieza del sitio", "carga y descarga",
        "trabajo en equipo", "resistencia física", "puntualidad", "fiabilidad",
        "señalización", "equipo de protección personal",
    ],
    "landscaper": [
        "jardinería", "paisajismo", "corte de césped", "poda", "riego", "plantación",
        "control de malezas", "fertilización", "equipo de jardinería", "sopladora",
        "seguridad", "mantenimiento de jardines", "diseño de jardines",
        "trabajo al aire libre",
    ],
    "catering": [
        "catering", "banquetes", "servicio de alimentos", "montaje de eventos", "bufé",
        "manipulación de alimentos", "seguridad alimentaria", "presentación",
        "servicio al cliente", "trabajo en equipo", "alto volumen",
        "transporte de alimentos", "emplatado", "coordinación de eventos",
    ],
    "freelance caterer": [
        "catering independiente", "banquetes", "planificación de menús", "presupuestos",
        "compra de insumos", "manipulación de alimentos", "seguridad alimentaria",
        "emplatado", "servicio al cliente", "coordinación de eventos", "facturación",
        "gestión de proveedores", "trabajo autónomo", "cotizaciones",
    ],
}

# Written without accents: check_sections() folds the text before matching, so
# these hit CVs that use accents and CVs that drop them alike.
SECTION_PATTERNS = {
    "Summary / Objective": r"\b(resumen|objetivo|perfil|perfil profesional|acerca de mi|extracto|sobre mi)\b",
    "Work Experience":     r"\b(experiencia|experiencia laboral|experiencia profesional|historial laboral|trayectoria)\b",
    "Education":           r"\b(educacion|formacion|formacion academica|academic|titulo|universidad|licenciatura|bachillerato|instituto|carrera)\w*\b",
    "Skills":              r"\b(habilidades|competencias|aptitudes|conocimientos|destrezas)\b",
    "Certifications":      r"\b(certificad|certificacion|licencia|credencial|acreditacion|diplomad)\w*\b",
    "Achievements":        r"\b(logro|premio|reconocimiento|distincion|merito)\w*\b",
    "Volunteer":           r"\b(voluntariado|voluntario|servicio comunitario|sin animo de lucro|organizacion benefica)\w*\b",
}

SECTION_LABELS = {
    "Summary / Objective": "Resumen / Objetivo",
    "Work Experience":     "Experiencia laboral",
    "Education":           "Educación",
    "Skills":              "Habilidades",
    "Certifications":      "Certificaciones",
    "Achievements":        "Logros",
    "Volunteer":           "Voluntariado",
}

ROLE_SUMMARIES = {
    "hospitality": (
        "Profesional de hostelería con amplia experiencia en servicio de banquetes, "
        "alta cocina y catering. Reconocido por ofrecer experiencias excepcionales a "
        "los huéspedes en entornos de alto volumen, con un firme compromiso con la "
        "atención al detalle, la puntualidad y el trabajo en equipo. Bilingüe y con "
        "una presentación profesional impecable."
    ),
    "event server": (
        "Camarero de eventos y banquetes con sólida trayectoria en servicio en mesa, "
        "operación de bufés y atención al huésped. Puntual y confiable, con capacidad "
        "demostrada para desempeñarse en entornos de catering de ritmo acelerado y "
        "alto volumen."
    ),
    "customer service": (
        "Profesional orientado al cliente con experiencia comprobada en la resolución "
        "de consultas, la construcción de relaciones y la entrega constante de un "
        "servicio de excelencia. Comunicador sólido con dominio de sistemas CRM, "
        "resolución de conflictos y soporte multicanal."
    ),
    "data entry": (
        "Especialista en entrada de datos con precisión demostrada en la gestión de "
        "hojas de cálculo, el procesamiento de información y el apoyo administrativo. "
        "Dominio de Microsoft Office y firme compromiso con un flujo de trabajo "
        "organizado y eficiente."
    ),
    "virtual assistant": (
        "Asistente virtual organizado y automotivado, con experiencia en gestión de "
        "agenda, coordinación de correo electrónico y apoyo a equipos remotos. Dominio "
        "de Microsoft Office, Google Workspace y herramientas de gestión de proyectos "
        "como Trello y Asana."
    ),
    "web developer": (
        "Desarrollador web orientado a resultados con experiencia práctica en HTML, "
        "CSS, JavaScript y diseño responsivo. Habilidad en depuración, control de "
        "versiones con Git y entrega puntual de interfaces limpias y adaptadas a "
        "dispositivos móviles."
    ),
}

GENERIC_SUMMARY = (
    "Profesional orientado a resultados con una base sólida en comunicación, trabajo "
    "en equipo y atención al detalle. Comprometido con entregar trabajo de calidad de "
    "forma eficiente y con adaptarse a nuevos retos con una actitud positiva y "
    "enfocada en soluciones."
)

# Spanish quantified-achievement patterns. Spanish states results as
# "aumenté las ventas en un 30%", so the connector is "en un" rather than "by".
METRIC_PATTERNS = [
    r"\d+\s*%",
    r"(?:\$|US\$|EUR|€)\s*[\d.,]+",
    r"\b\d+\s*(?:personas|empleados|colaboradores|clientes|huéspedes|huespedes|cuentas|miembros|equipo)\b",
    r"\b(?:aument|increment|reduj|reduc|mejor|gener|ahorr|gestion|super)\w*\s+(?:\w+\s+){0,3}(?:en\s+un\s+)?\d+",
    r"\b\d{1,3}(?:[.,]\d{3})+\b",
]

# "Ciudad, País" / "Ciudad, Estado" -- accepts accented city names, which the
# US-style [A-Z][a-zA-Z\s]+ pattern would reject.
LOCATION_PATTERN = r"\b[A-ZÁÉÍÓÚÑ][\wáéíóúñ\s]+,\s*[A-ZÁÉÍÓÚÑ][\wáéíóúñ]{1,}\b"

MESSAGES = {
    "warn_short":        "El CV parece muy corto (menos de 200 caracteres)",
    "warn_no_email":     "No se detectó ninguna dirección de correo electrónico",
    "warn_few_words":    "Se detectaron muy pocas palabras ({count}); el CV puede estar incompleto",
    "tip_phone":         "Considera agregar un número de teléfono",
    "tip_too_long":      "El CV puede ser demasiado largo: apunta a 1 página (2 como máximo)",

    "rec_role_title":    "Agrega palabras clave específicas para {role}",
    "rec_role_detail":   "Fundamentales para este puesto; añádelas en Habilidades o Experiencia: {keywords}",
    "rec_role_overflow": " (+{count} más)",
    "rec_metrics_title": "Agrega logros medibles",
    "rec_metrics_detail": 'Las cifras hacen destacar tus logros; por ejemplo "Gestioné un equipo de 15 personas" o "Reduje los costos en un 20%"',
    "rec_verbs_strong_title":  "Refuerza tus logros con verbos de acción",
    "rec_verbs_strong_detail": "Comienza cada punto con: {keywords}",
    "rec_verbs_more_title":    "Agrega más verbos de acción",
    "rec_verbs_more_detail":   "Considera usar: {keywords}",
    "rec_tech_title":    "Amplía tu sección de habilidades técnicas",
    "rec_tech_detail":   "Agrega las que domines: {keywords}",
    "rec_summary_title": "Agrega un resumen profesional",
    "rec_summary_detail": "3 o 4 líneas al inicio, adaptadas al puesto que buscas",
    "rec_skills_title":  'Agrega una sección de "Habilidades"',
    "rec_skills_detail": "Una sección de habilidades claramente identificada ayuda al ATS a extraer tus cualificaciones de inmediato",
    "rec_contact_title": "Completa tus datos de contacto",
    "rec_contact_detail": "Considera agregar: {items}",
    "rec_soft_title":    "Incorpora más habilidades blandas",
    "rec_soft_detail":   "Úsalas con naturalidad en tu resumen o en tus logros: {keywords}",

    "contact_linkedin":  "URL de LinkedIn",
    "contact_location":  "Ciudad, País",

    "grade_a": "A — Excelente",
    "grade_b": "B — Bueno",
    "grade_c": "C — Necesita mejoras",
    "grade_d": "D — Débil",
    "grade_f": "F — Requiere una revisión importante",

    "report_title":   "ANALIZADOR ATS DE CV — INFORME",
    "report_file":    "Archivo",
    "report_date":    "Fecha",
    "report_found":   "Encontrado",
    "report_missing": "Falta",
    "report_yes":     "SÍ",
    "report_no":      "FALTA",
    "label_email":    "Correo electrónico",
    "label_phone":    "Teléfono",
    "label_linkedin": "LinkedIn",
    "label_location": "Ubicación",

    "hdr_overall":   "PUNTUACIÓN GENERAL",
    "hdr_grade":     "CALIFICACIÓN",
    "hdr_found":     "PALABRAS CLAVE",
    "hdr_contact":   "DATOS DE CONTACTO",
    "hdr_recs":      "RECOMENDACIONES",
    "hdr_warnings":  "ADVERTENCIAS",
    "hdr_tips":      "CONSEJOS",
    "hdr_breakdown": "DESGLOSE DE PALABRAS CLAVE",
    "hdr_end":       "FIN DEL INFORME — Generado por Workblox",

    "priority_high":   "ALTA",
    "priority_medium": "MEDIA",
    "priority_low":    "BAJA",

    "job_role_generic":  "el puesto",
}


# Role identifiers stay English (they are IDs); this is the display text.
ROLE_LABELS = {
    "administrative assistant"     : "Asistente administrativo",
    "executive assistant"          : "Asistente ejecutivo",
    "receptionist"                 : "Recepcionista",
    "office manager"               : "Gerente de oficina",
    "data entry"                   : "Captura de datos",
    "virtual assistant"            : "Asistente virtual",
    "customer service"             : "Servicio al cliente",
    "call center"                  : "Centro de llamadas",
    "sales associate"              : "Asesor de ventas",
    "retail associate"             : "Dependiente de tienda",
    "cashier"                      : "Cajero",
    "event server"                 : "Camarero de eventos",
    "hospitality"                  : "Hostelería",
    "server"                       : "Camarero",
    "barista"                      : "Barista",
    "cook"                         : "Cocinero",
    "restaurant manager"           : "Gerente de restaurante",
    "warehouse associate"          : "Operario de almacén",
    "forklift operator"            : "Operador de montacargas",
    "delivery driver"              : "Repartidor",
    "inventory specialist"         : "Especialista en inventario",
    "caregiver"                    : "Cuidador",
    "home health aide"             : "Asistente de salud a domicilio",
    "medical assistant"            : "Asistente médico",
    "certified nursing assistant"  : "Auxiliar de enfermería certificado",
    "pharmacy technician"          : "Técnico de farmacia",
    "housekeeper"                  : "Ama de llaves",
    "janitor"                      : "Conserje",
    "maintenance technician"       : "Técnico de mantenimiento",
    "teacher assistant"            : "Asistente de maestro",
    "childcare worker"             : "Auxiliar de cuidado infantil",
    "tutor"                        : "Tutor",
    "security guard"               : "Guardia de seguridad",
    "web developer"                : "Desarrollador web",
    "it support"                   : "Soporte técnico",
    "social media manager"         : "Community manager",
    "bookkeeper"                   : "Tenedor de libros",
    "accounting clerk"             : "Auxiliar contable",
    "general laborer"              : "Peón general",
    "landscaper"                   : "Jardinero",
    "catering"                     : "Catering",
    "freelance caterer"            : "Catering independiente",
}
