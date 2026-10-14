"""Phrase banks used to build synthetic reviews in Spanish, English and Portuguese.

Reviews are synthetic on purpose (the brief forbids scraping real platforms).
Each topic has a positive and a negative phrase so the reputation area can later
find recurring themes (cleanliness, staff, noise, etc.).
"""

TOPICS: dict[str, dict[str, tuple[str, str]]] = {
    # topic: {language: (positive, negative)}
    "cleanliness": {
        "es": ("La habitación estaba impecable.", "La habitación no estaba limpia al llegar."),
        "en": ("The room was spotless.", "The room was not clean when we arrived."),
        "pt": ("O quarto estava impecável.", "O quarto não estava limpo quando chegamos."),
    },
    "staff": {
        "es": ("El personal fue muy amable y atento.", "El personal de recepción fue poco amable."),
        "en": ("The staff were friendly and helpful.", "The front desk staff were rude."),
        "pt": ("A equipe foi muito simpática e atenciosa.", "A recepção foi pouco simpática."),
    },
    "location": {
        "es": ("La ubicación es excelente, cerca de todo.", "La ubicación es lejos de todo."),
        "en": ("Great location, close to everything.", "The location is far from everything."),
        "pt": ("A localização é excelente, perto de tudo.", "A localização é longe de tudo."),
    },
    "breakfast": {
        "es": ("El desayuno fue variado y delicioso.", "El desayuno era pobre y repetitivo."),
        "en": ("Breakfast was varied and delicious.", "Breakfast was poor and repetitive."),
        "pt": (
            "O café da manhã foi variado e delicioso.",
            "O café da manhã era fraco e repetitivo.",
        ),
    },
    "noise": {
        "es": ("La habitación era muy silenciosa.", "Había mucho ruido en la noche."),
        "en": ("The room was very quiet.", "It was very noisy at night."),
        "pt": ("O quarto era muito silencioso.", "Havia muito barulho à noite."),
    },
    "wifi": {
        "es": ("El wifi funcionó perfecto.", "El wifi era lento y se caía constantemente."),
        "en": ("The wifi worked perfectly.", "The wifi was slow and kept dropping."),
        "pt": ("O wifi funcionou perfeitamente.", "O wifi era lento e caía o tempo todo."),
    },
    "check_in": {
        "es": ("El check-in fue rápido.", "Esperamos más de una hora para el check-in."),
        "en": ("Check-in was quick.", "We waited over an hour to check in."),
        "pt": ("O check-in foi rápido.", "Esperamos mais de uma hora pelo check-in."),
    },
    "value": {
        "es": ("Muy buena relación calidad-precio.", "Demasiado caro para lo que ofrece."),
        "en": ("Very good value for money.", "Too expensive for what it offers."),
        "pt": ("Ótimo custo-benefício.", "Caro demais pelo que oferece."),
    },
    "pool": {
        "es": ("La piscina estaba muy bien cuidada.", "La piscina estaba sucia y llena."),
        "en": ("The pool was well kept.", "The pool was dirty and crowded."),
        "pt": ("A piscina estava muito bem cuidada.", "A piscina estava suja e lotada."),
    },
    "relocation": {
        "es": (
            "Nos atendieron sin problemas a pesar de la alta ocupación.",
            "Nos reubicaron en otro hotel porque no había habitación.",
        ),
        "en": (
            "They handled us smoothly despite the hotel being full.",
            "We were moved to another hotel because there was no room.",
        ),
        "pt": (
            "Fomos bem atendidos apesar da ocupação alta.",
            "Fomos realocados para outro hotel porque não havia quarto.",
        ),
    },
}

OPENERS: dict[str, dict[str, tuple[str, ...]]] = {
    "positive": {
        "es": ("Excelente estadía.", "Volveríamos sin dudarlo.", "Muy recomendado."),
        "en": ("Excellent stay.", "We would come back for sure.", "Highly recommended."),
        "pt": ("Estadia excelente.", "Voltaríamos com certeza.", "Muito recomendado."),
    },
    "mixed": {
        "es": ("Estadía correcta.", "Tiene cosas buenas y malas.", "Cumple, sin más."),
        "en": ("Decent stay.", "Some good and some bad.", "It does the job."),
        "pt": ("Estadia razoável.", "Tem pontos bons e ruins.", "Cumpre o básico."),
    },
    "negative": {
        "es": ("Muy mala experiencia.", "No lo recomiendo.", "Esperaba mucho más."),
        "en": ("Very bad experience.", "I do not recommend it.", "I expected much more."),
        "pt": ("Experiência muito ruim.", "Não recomendo.", "Esperava muito mais."),
    },
}

TITLES: dict[str, dict[str, tuple[str, ...]]] = {
    "positive": {
        "es": ("¡Excelente!", "Muy buena estadía", "Superó expectativas"),
        "en": ("Excellent!", "Great stay", "Exceeded expectations"),
        "pt": ("Excelente!", "Ótima estadia", "Superou as expectativas"),
    },
    "mixed": {
        "es": ("Aceptable", "Regular", "Podría mejorar"),
        "en": ("Okay", "Average", "Could be better"),
        "pt": ("Aceitável", "Regular", "Poderia melhorar"),
    },
    "negative": {
        "es": ("Decepcionante", "No volvería", "Mala experiencia"),
        "en": ("Disappointing", "Would not return", "Bad experience"),
        "pt": ("Decepcionante", "Não voltaria", "Experiência ruim"),
    },
}

FIRST_NAMES: dict[str, tuple[str, ...]] = {
    "es": (
        "María",
        "José",
        "Andrés",
        "Lucía",
        "Camila",
        "Sofía",
        "Juan",
        "Valentina",
        "Sebastián",
        "Daniela",
        "Carlos",
        "Mariana",
        "Alejandro",
        "Paula",
        "Mateo",
    ),
    "en": (
        "James",
        "Emily",
        "Michael",
        "Sarah",
        "David",
        "Jessica",
        "Daniel",
        "Laura",
        "Thomas",
        "Hannah",
        "Chris",
        "Olivia",
        "Ryan",
        "Megan",
        "Jack",
    ),
    "pt": (
        "João",
        "Ana",
        "Pedro",
        "Beatriz",
        "Lucas",
        "Mariana",
        "Gabriel",
        "Júlia",
        "Rafael",
        "Larissa",
        "Tiago",
        "Inês",
        "Bruno",
        "Carolina",
        "Rodrigo",
    ),
}

LAST_NAMES: dict[str, tuple[str, ...]] = {
    "es": (
        "García",
        "Rodríguez",
        "Martínez",
        "López",
        "Hernández",
        "Gómez",
        "Díaz",
        "Pérez",
        "Sánchez",
        "Ramírez",
        "Torres",
        "Fontalvo",
        "Castro",
        "Vargas",
    ),
    "en": (
        "Smith",
        "Johnson",
        "Brown",
        "Taylor",
        "Wilson",
        "Davies",
        "Miller",
        "Clark",
        "Walker",
        "Wright",
        "Hall",
        "Young",
        "King",
        "Scott",
    ),
    "pt": (
        "Silva",
        "Santos",
        "Oliveira",
        "Souza",
        "Pereira",
        "Costa",
        "Ferreira",
        "Almeida",
        "Carvalho",
        "Gomes",
        "Ribeiro",
        "Martins",
        "Rocha",
        "Lima",
    ),
}

REVIEWER_COUNTRIES: dict[str, tuple[str, ...]] = {
    "es": ("CO", "MX", "ES", "AR", "CL", "PE"),
    "en": ("US", "GB", "CA", "AU", "IE", "NL"),
    "pt": ("BR", "PT"),
}
