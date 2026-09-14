"""Fase 4 — quita de la base vectorial TODOS los fragmentos de un conjunto de
doc_id, sin tocar el resto.

Caso de uso: un fix en Fase 1/2 (extracción/limpieza) cambió el texto de
ciertos documentos ya indexados -- no reemplaza vectores 1 a 1 como
`reencode_subset.py` (la cantidad de fragmentos por documento puede cambiar
al re-chunkear con el texto corregido), así que primero hay que QUITAR sus
vectores viejos de la base con este script, y luego agregar los fragmentos
re-chunkeados con `extend_index.py` (que solo acepta doc_id que NO estén ya
en la base).

    uv run python -m codefest_ad_astra.indexing.remove_documents \
        --base entrega/base_vectorial/encoder_bge-m3 \
        --doc-ids /tmp/doc_ids_afectados.json

`--doc-ids` acepta un .json con una lista de strings, o un .txt/.jsonl con un
doc_id por línea (se detecta por extensión).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .faiss_store import (
    cargar_base_vectorial,
    construir_indice,
    guardar_base_vectorial,
    validar_alineacion,
)


def _leer_doc_ids(path: Path) -> set[str]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit(f"{path} debe contener una lista JSON de doc_id.")
        return set(data)
    # .txt / .jsonl / cualquier otra cosa: un doc_id por línea
    doc_ids = set()
    for linea in path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        # tolera que cada línea sea el doc_id pelado o un JSON {"doc_id": ...}
        if linea.startswith("{"):
            doc_ids.add(json.loads(linea)["doc_id"])
        else:
            doc_ids.add(linea.strip('",'))
    return doc_ids


def quitar_documentos(dir_base: Path, path_doc_ids: Path) -> Path:
    dir_base = Path(dir_base)
    doc_ids_a_quitar = _leer_doc_ids(path_doc_ids)
    if not doc_ids_a_quitar:
        raise SystemExit("La lista de doc_id a quitar está vacía.")

    print(f"Cargando base vectorial existente de {dir_base}")
    indice_viejo, metadata_vieja, manifiesto_viejo = cargar_base_vectorial(dir_base)
    print(f"  {indice_viejo.ntotal} vectores ya indexados")

    presentes = {r["doc_id"] for r in metadata_vieja}
    no_encontrados = doc_ids_a_quitar - presentes
    if no_encontrados:
        print(f"  [AVISO] {len(no_encontrados)} doc_id de la lista no estaban en la base (se ignoran)")

    mascara_mantener = np.array([r["doc_id"] not in doc_ids_a_quitar for r in metadata_vieja])
    n_quitados = int((~mascara_mantener).sum())
    if n_quitados == 0:
        raise SystemExit("Ningún fragmento de la base coincide con los doc_id dados -- nada que quitar.")

    print(f"Quitando {n_quitados} fragmentos de {len(doc_ids_a_quitar & presentes)} documentos")

    vectores_completos = indice_viejo.reconstruct_n(0, indice_viejo.ntotal)
    vectores_completos = np.ascontiguousarray(vectores_completos, dtype=np.float32)
    vectores_restantes = vectores_completos[mascara_mantener]
    metadata_restante = [r for r, mantener in zip(metadata_vieja, mascara_mantener) if mantener]

    indice_nuevo = construir_indice(vectores_restantes)
    validar_alineacion(indice_nuevo, metadata_restante)

    manifiesto_nuevo = dict(manifiesto_viejo)
    manifiesto_nuevo.update({
        "actualizado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "num_vectores": int(indice_nuevo.ntotal),
        "num_vectores_quitados_en_esta_actualizacion": n_quitados,
        "num_documentos_quitados_en_esta_actualizacion": len(doc_ids_a_quitar & presentes),
        "doc_ids_quitados_en_esta_actualizacion": str(path_doc_ids),
    })

    guardar_base_vectorial(dir_base, indice_nuevo, metadata_restante, manifiesto_nuevo)
    print(f"\nListo: {n_quitados} vectores quitados, quedan {indice_nuevo.ntotal} -> {dir_base}")
    return dir_base


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Quita de la base vectorial todos los fragmentos de un conjunto de doc_id."
    )
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--doc-ids", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        quitar_documentos(args.base, args.doc_ids)
    except SystemExit as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
