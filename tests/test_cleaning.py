"""Tests de Fase 2 (limpieza) — cleaning.py."""
from codefest_ad_astra.ingest.cleaning import quitar_lineas_repetidas


def test_quitar_lineas_repetidas_identicas():
    """Caso original: una línea idéntica en todas las páginas es boilerplate."""
    paginas = [
        "Header Fijo\nContenido A\nMás contenido A",
        "Header Fijo\nContenido B",
        "Header Fijo\nContenido C",
    ]
    resultado = quitar_lineas_repetidas(paginas)
    assert all("Header Fijo" not in p for p in resultado)
    assert "Contenido A" in resultado[0]
    assert "Contenido B" in resultado[1]
    assert "Contenido C" in resultado[2]


def test_quitar_lineas_repetidas_footer_con_numero_de_pagina():
    """Bug real (corpus CSET): un footer del tipo 'Título | N' con N distinto
    en cada página nunca calzaba por igualdad exacta y se colaba en el texto,
    rompiendo el requisito de que cada fragmento termine en oración completa."""
    paginas = [
        "Contenido real de la página uno.\nCenter for Security and Emerging Technology | 1",
        "Contenido real de la página dos.\nCenter for Security and Emerging Technology | 2",
        "Contenido real de la página tres.\nCenter for Security and Emerging Technology | 3",
        "Contenido real de la página cuatro.\nCenter for Security and Emerging Technology | 4",
    ]
    resultado = quitar_lineas_repetidas(paginas)
    for pagina in resultado:
        assert "Center for Security and Emerging Technology" not in pagina
    assert "Contenido real de la página uno." in resultado[0]
    assert "Contenido real de la página cuatro." in resultado[3]


def test_quitar_lineas_repetidas_numero_de_pagina_solo():
    """Variante: la línea es SOLO el número de página, sin texto de footer."""
    paginas = [
        "Contenido A.\n1",
        "Contenido B.\n2",
        "Contenido C.\n3",
    ]
    resultado = quitar_lineas_repetidas(paginas)
    assert "1" not in resultado[0].splitlines()
    assert "2" not in resultado[1].splitlines()
    assert "3" not in resultado[2].splitlines()


def test_quitar_lineas_repetidas_no_afecta_contenido_no_repetido():
    """Una línea que contiene un número pero NO se repite en la mayoría de
    páginas no debe eliminarse (evita falsos positivos por sobre-normalizar)."""
    paginas = [
        "En 2020 se firmaron 15 acuerdos.",
        "Otro contenido totalmente distinto.",
        "Un tercer párrafo sin relación.",
    ]
    resultado = quitar_lineas_repetidas(paginas)
    assert "En 2020 se firmaron 15 acuerdos." in resultado[0]


def test_quitar_lineas_repetidas_menos_de_tres_paginas_no_hace_nada():
    paginas = ["Repetido\nA", "Repetido\nB"]
    assert quitar_lineas_repetidas(paginas) == paginas
