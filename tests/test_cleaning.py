"""Tests de Fase 2 (limpieza) — cleaning.py."""
from codefest_ad_astra.ingest.cleaning import quitar_lineas_repetidas, quitar_sufijo_pegado_repetido


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


def test_quitar_lineas_repetidas_footer_alternado_par_impar():
    """Bug real (corpus DAIO): un informe maquetado a doble página tiene un
    footer distinto en páginas pares vs. impares. Cada uno cubre ~50% de las
    páginas -- por debajo del umbral original de 0.6, nunca se detectaba."""
    paginas = [
        "Contenido página 1.\nRISKY INCREMENTALISM 2",
        "Contenido página 2.\nWWW.DEFENSEAI.EU 3",
        "Contenido página 3.\nRISKY INCREMENTALISM 4",
        "Contenido página 4.\nWWW.DEFENSEAI.EU 5",
        "Contenido página 5.\nRISKY INCREMENTALISM 6",
        "Contenido página 6.\nWWW.DEFENSEAI.EU 7",
    ]
    resultado = quitar_lineas_repetidas(paginas)
    for pagina in resultado:
        assert "RISKY INCREMENTALISM" not in pagina
        assert "WWW.DEFENSEAI.EU" not in pagina


def test_quitar_sufijo_pegado_repetido_footer_sin_salto_de_linea():
    """El footer queda pegado sin '\\n' al final del último párrafo real
    -- quitar_lineas_repetidas no lo puede aislar como línea propia."""
    paginas = [
        "Texto real de la página uno, sin cortar. WWW.DEFENSEAI.EU 5",
        "Otro párrafo real distinto aquí. WWW.DEFENSEAI.EU 6",
        "Un tercer párrafo con más contenido. WWW.DEFENSEAI.EU 7",
    ]
    resultado = quitar_sufijo_pegado_repetido(paginas)
    for pagina in resultado:
        assert "WWW.DEFENSEAI.EU" not in pagina
    assert resultado[0] == "Texto real de la página uno, sin cortar."


def test_quitar_sufijo_pegado_repetido_no_afecta_numeros_reales():
    """Un número real al final de una página (no un footer) no debe
    quitarse si el 'token' que lo precede no se repite en otras páginas."""
    paginas = [
        "El total de acuerdos firmados fue 15",
        "Este párrafo es distinto y no termina en número.",
        "Un tercer párrafo cualquiera, sin relación.",
    ]
    resultado = quitar_sufijo_pegado_repetido(paginas)
    assert resultado == paginas
