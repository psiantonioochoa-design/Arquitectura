"""Línea de comandos del núcleo de Harry.

  validar       comprueba los casos ejecutables contra el generador de 05_pruebas
  listar        lista casos (con filtros)
  diagnostico   revisa una plataforma sin iniciar Ollama ni cargar modelos
  contexto      muestra el contexto EXACTO que recibiría el modelo (sin llamarlo)
  buscar        prueba la recuperación documental y muestra fuente, sección, versión y estado
  correr        crea y ejecuta una corrida (simulación técnica, exploratoria o conformidad)
  reanudar      continúa una corrida interrumpida o con pendientes
  estado        estado breve de una corrida
  resumen       regenera el resumen técnico
  hoja          exporta la hoja de calificación humana
  corridas      lista las corridas, separadas por tipo
  calibrar      compara la estimación de tokens con el conteo real del modelo (no cambia nada)
  prefiltro     señala posibles incumplimientos para revisión humana (no califica)
  comparar      comparación preliminar entre corridas, con respuestas literales y hoja ciega
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import List, Optional

from . import NUCLEO_VERSION, rutas
from .configuracion import ErrorConfiguracion, cargar_plataforma, cargar_proyecto

MARCADOR_EN_VIVO = ("[MARCADOR DE INSPECCIÓN: aquí iría la respuesta que el modelo genere en vivo en el turno {i}. "
                    "En una corrida real este lugar lo ocupa esa respuesta.]")


def _lista(valor: Optional[str]) -> Optional[List[str]]:
    if not valor:
        return None
    return [x.strip() for x in valor.split(",") if x.strip()]


def _ids_generador() -> set:
    ruta = rutas.raiz() / "05_pruebas" / "_generador" / "generar.py"
    spec = importlib.util.spec_from_file_location("generador_05", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {c[0] for c in mod.CASOS}


def _todas_las_carpetas(proyecto) -> List[Path]:
    from .ejecutor import carpetas_de_corridas
    carpetas = list(carpetas_de_corridas(proyecto).values())
    antigua = rutas.evaluaciones() / "corridas"
    if antigua.exists():
        carpetas.append(antigua)
    return carpetas


def _carpeta_corrida(valor: str, proyecto) -> Path:
    p = Path(valor).expanduser()
    if p.is_dir():
        return p.resolve()
    for base in _todas_las_carpetas(proyecto):
        if (base / valor).is_dir():
            return base / valor
    raise SystemExit(f"No encuentro la corrida: {valor}")


def _seleccion(sp):
    sp.add_argument("--casos", help="IDs separados por comas, p. ej. K0-1,S-7,P2")
    sp.add_argument("--bloques", help="Letras de bloque, p. ej. A,B")
    sp.add_argument("--criticidad", help="crítica,alta,media")
    sp.add_argument("--forma", help="un turno,multiturno,par")
    sp.add_argument("--incluir-anexo-a", action="store_true",
                    help="Solo en simulación técnica: registra los 17 casos del Anexo A, que siguen pendientes")


def _imprimir_montaje(montaje, encabezado: List[str], como_json: bool) -> None:
    if como_json:
        print(json.dumps({"encabezado": encabezado, "detalle": montaje.detalle, "mensajes": montaje.mensajes},
                         ensure_ascii=False, indent=2))
        return
    for linea in encabezado:
        print(linea)
    d = montaje.detalle
    print(f"Tokens estimados ({d['metodo_estimacion']}): instrucciones {d['tokens_instrucciones']} · "
          f"recursos {d.get('tokens_recursos', 0)} · referencias {d['tokens_referencias']} · historial {d['tokens_historial']} · "
          f"total {d['total_estimado']} de una ventana de {d['ventana']} con {d['reserva_respuesta']} reservados para la respuesta")
    print(f"Intercambios incluidos: {d['intercambios_incluidos']} · omitidos por espacio: {d['intercambios_omitidos']}"
          + (" · referencias quitadas por espacio" if d["referencias_quitadas_por_espacio"] else ""))
    print(f"Recursos de ayuda enviados (del registro): {', '.join(d.get('recursos_ayuda') or []) or 'ninguno'}")
    print(f"Investigación activada por: {d.get('investigacion_activada_por') or 'nada (solo normas)'}")
    if d["fragmentos"]:
        print("Documentos recuperados:")
        for f in d["fragmentos"]:
            print(f"  - {f['fuente']} · {f['seccion']} · {f['version']} · {f['estado']} · puntaje {f['puntaje']}")
    else:
        print("Documentos recuperados: ninguno")
    print("=" * 78)
    for n, m in enumerate(montaje.mensajes, 1):
        print(f"--- mensaje {n} · rol: {m['role']} · {len(m['content'])} caracteres ---")
        print(m["content"])
    print("=" * 78)


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="harry", description=f"Núcleo y ejecutor de pruebas de Harry {NUCLEO_VERSION}")
    sub = ap.add_subparsers(dest="orden", required=True)

    sub.add_parser("validar", help="Valida los casos ejecutables")

    sp = sub.add_parser("listar", help="Lista casos")
    _seleccion(sp)

    sp = sub.add_parser("diagnostico", help="Revisa una plataforma (estático por defecto)")
    sp.add_argument("--plataforma", required=True)
    sp.add_argument("--consultar-servidor", action="store_true",
                    help="Solo GET a /api/version, /api/tags y /api/ps; no carga modelos")

    sp = sub.add_parser("contexto", help="Muestra el contexto exacto que recibiría el modelo")
    sp.add_argument("--plataforma", help="Para --caso o --mensaje")
    sp.add_argument("--caso", help="ID del caso")
    sp.add_argument("--variante", help="Variante (por defecto, la primera)")
    sp.add_argument("--turno", type=int, help="Índice del turno de la persona (por defecto, el último evaluado)")
    sp.add_argument("--mensaje", help="Un mensaje libre, como inicio de una sesión nueva")
    sp.add_argument("--corrida", help="Muestra lo que de verdad se envió en una corrida")
    sp.add_argument("--unidad", help="Con --corrida: p. ej. 'K2-2|unica|r1'")
    sp.add_argument("--sin-recuperacion", action="store_true")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("buscar", help="Prueba la recuperación documental")
    sp.add_argument("--consulta", required=True)
    sp.add_argument("--categorias", default="norma_propuesta,investigacion",
                    help="Para inspeccionar también: en_revision,historico (nunca se envían al modelo)")
    sp.add_argument("--max", type=int, default=5)

    sp = sub.add_parser("correr", help="Crea y ejecuta una corrida")
    sp.add_argument("--plataforma", required=True)
    _seleccion(sp)
    sp.add_argument("--tipo", choices=("exploratoria", "conformidad"),
                    help="Solo para modelos reales; la simulación siempre es técnica")
    sp.add_argument("--repeticiones", type=int, help="Por defecto, las de proyecto.json (5)")
    sp.add_argument("--etiqueta", help="Sufijo para el nombre de la corrida")
    sp.add_argument("--max-intentos", type=int, help="Intentos por unidad en cada sesión de ejecución")
    sp.add_argument("--autorizo-modelo-real", action="store_true")
    sp.add_argument("--permitir-instrucciones-pendientes", action="store_true")
    sp.add_argument("--permitir-otro-modelo", action="store_true")
    sp.add_argument("--ignorar-memoria", action="store_true")
    sp.add_argument("--solo-crear", action="store_true", help="Crea la corrida sin ejecutarla")

    sp = sub.add_parser("reanudar", help="Continúa una corrida")
    sp.add_argument("corrida")
    sp.add_argument("--forzar", action="store_true", help="Reanuda aunque el código haya cambiado (queda registrado)")
    sp.add_argument("--max-intentos", type=int)
    sp.add_argument("--permitir-otro-modelo", action="store_true")
    sp.add_argument("--ignorar-memoria", action="store_true")

    for nombre, ayuda in (("estado", "Estado breve"), ("resumen", "Regenera resumen.md"), ("hoja", "Exporta calificacion.csv")):
        sp = sub.add_parser(nombre, help=ayuda)
        sp.add_argument("corrida")

    sub.add_parser("corridas", help="Lista las corridas por tipo")

    sp = sub.add_parser("calibrar", help="Compara tokens estimados con prompt_eval_count real (no cambia nada)")
    sp.add_argument("corridas", nargs="+")
    sp.add_argument("--destino", help="Carpeta del informe (por defecto, la de la primera corrida)")

    sp = sub.add_parser("prefiltro", help="Señala posibles incumplimientos para revisión humana (no califica)")
    sp.add_argument("corrida")

    sp = sub.add_parser("comparar", help="Comparación preliminar entre corridas, con respuestas literales")
    sp.add_argument("corridas", nargs="+")
    sp.add_argument("--destino", help="Carpeta nueva para la comparación (por defecto, en exploratorias/)")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = construir_parser().parse_args(argv)
    try:
        proyecto = cargar_proyecto()
    except ErrorConfiguracion as e:
        print(f"ERROR: {e}")
        return 2

    from .casos import cargar, seleccionar, turnos_para_envio, validar
    from .ejecutor import Corrida, ErrorEjecucion
    from .informes import escribir_hoja, escribir_resumen, estado_breve
    from .nucleo import ErrorNucleo, Montaje, Nucleo
    from .recuperacion import ErrorIndice, Recuperador
    from .util import leer_jsonl, sha256_archivo

    try:
        if args.orden == "validar":
            ruta = rutas.ruta(proyecto["casos_ejecutables"])
            datos = cargar(ruta)
            problemas = validar(datos, _ids_generador())
            gen = rutas.raiz() / "05_pruebas" / "_generador" / "generar.py"
            gui = rutas.impl() / "casos" / "guiones.py"
            if datos["meta"].get("hash_generador_05") != sha256_archivo(gen):
                problemas.append("El generador de 05_pruebas cambió: vuelve a correr construir_casos.py")
            if datos["meta"].get("hash_guiones") != sha256_archivo(gui):
                problemas.append("guiones.py cambió: vuelve a correr construir_casos.py")
            if problemas:
                print(f"ERROR: {len(problemas)} problemas")
                for p in problemas:
                    print("  -", p)
                return 1
            casos = datos["casos"]
            formas = {}
            for c in casos:
                formas[c["forma"]] = formas.get(c["forma"], 0) + 1
            print(f"OK: {len(casos)} casos válidos, iguales a los del generador de 05_pruebas.")
            print(f"    formas: {formas}; pendientes del Anexo A: {sum(c['pendiente_anexo_A'] for c in casos)}")
            print("    Ningún mensaje contiene las rúbricas (conducta que cumple, fallas).")
            return 0

        if args.orden == "listar":
            datos = cargar(rutas.ruta(proyecto["casos_ejecutables"]))
            sel, excl = seleccionar(datos["casos"], _lista(args.casos), _lista(args.bloques),
                                    _lista(args.criticidad), _lista(args.forma), args.incluir_anexo_a)
            for c in sel:
                marca = " [Anexo A: pendiente]" if c["pendiente_anexo_A"] else ""
                print(f"{c['id']:<10} {c['criticidad']:<8} {c['forma']:<11} {c['bloque']}{marca}")
            print(f"-- {len(sel)} casos" + (f"; excluidos por Anexo A: {len(excl)} (usa --incluir-anexo-a)" if excl else ""))
            return 0

        if args.orden == "diagnostico":
            from .diagnostico import diagnosticar
            plataforma = cargar_plataforma(args.plataforma)
            hay_error = False
            for nivel, msg in diagnosticar(plataforma, proyecto, args.consultar_servidor):
                print(f"[{nivel:<5}] {msg}")
                hay_error |= nivel == "ERROR"
            return 1 if hay_error else 0

        if args.orden == "contexto":
            if args.corrida:
                carpeta = _carpeta_corrida(args.corrida, proyecto)
                registros = [r for r in leer_jsonl(carpeta / "contextos.jsonl") if "unidad" in r]
                if args.unidad:
                    registros = [r for r in registros if r["unidad"] == args.unidad]
                if args.turno is not None:
                    registros = [r for r in registros if r["turno"] == args.turno]
                if not registros:
                    print("No hay contextos registrados para esa selección (las corridas de la etapa 1 no los guardaban).")
                    return 1
                r = registros[-1]
                _imprimir_montaje(Montaje(r["mensajes"], r["montaje"]),
                                  [f"Contexto REGISTRADO en {carpeta.name}: unidad {r['unidad']}, intento {r['intento']}, turno {r['turno']}"],
                                  args.json)
                return 0
            if not args.plataforma:
                print("ERROR: falta --plataforma")
                return 2
            plataforma = cargar_plataforma(args.plataforma)
            nucleo = Nucleo(plataforma)
            enc = [f"Plataforma: {plataforma['id']} · instrucciones «{nucleo.estado_instrucciones}» v{nucleo.version_instrucciones} "
                   f"(huella {nucleo.hash_instrucciones[:12]})",
                   "Nada de esto se envió a ningún modelo: es una inspección."]
            if args.mensaje:
                montaje = nucleo.montar([{"rol": "usuario", "texto": args.mensaje}], recuperar=not args.sin_recuperacion)
                _imprimir_montaje(montaje, enc + ["Sesión nueva con un mensaje libre."], args.json)
                return 0
            if not args.caso:
                print("ERROR: indica --caso, --mensaje o --corrida")
                return 2
            datos = cargar(rutas.ruta(proyecto["casos_ejecutables"]))
            casos = {c["id"]: c for c in datos["casos"]}
            if args.caso not in casos:
                print(f"ERROR: no existe el caso {args.caso}")
                return 2
            caso = casos[args.caso]
            variante = args.variante or sorted(caso["ejecucion"]["variantes"])[0]
            turnos = turnos_para_envio(caso, variante)
            objetivo = args.turno
            if objetivo is None:
                objetivo = max(i for i, t in enumerate(turnos) if t["rol"] == "usuario" and t["evaluar"])
            if not (0 <= objetivo < len(turnos)) or turnos[objetivo]["rol"] != "usuario":
                print("ERROR: el turno indicado no es un mensaje de la persona")
                return 2
            historial = []
            marcadores = 0
            for i, t in enumerate(turnos[: objetivo + 1]):
                if t["rol"] == "harry_fabricado":
                    historial.append({"rol": "harry", "texto": t["texto"]})
                    continue
                historial.append({"rol": "usuario", "texto": t["texto"]})
                if i < objetivo and not (i + 1 < len(turnos) and turnos[i + 1]["rol"] == "harry_fabricado"):
                    historial.append({"rol": "harry", "texto": MARCADOR_EN_VIVO.format(i=i)})
                    marcadores += 1
            montaje = nucleo.montar(historial, recuperar=not args.sin_recuperacion)
            enc.append(f"Caso {caso['id']} · variante {variante} · turno {objetivo} · criticidad {caso['criticidad']}"
                       + (" · ANEXO A: PENDIENTE" if caso["pendiente_anexo_A"] else ""))
            if marcadores:
                enc.append(f"Hay {marcadores} marcador(es) donde iría una respuesta generada en vivo; "
                           "en la corrida real ese texto y su tamaño serán otros.")
            enc.append("Las rúbricas del caso no forman parte de este contexto.")
            _imprimir_montaje(montaje, enc, args.json)
            return 0

        if args.orden == "buscar":
            cats = _lista(args.categorias) or ["norma_propuesta"]
            rec = Recuperador(rutas.impl() / "recuperacion" / "indice.json", cats, max_fragmentos=args.max,
                              max_tokens=10_000, permitir_no_enviables=True)
            res = rec.buscar(args.consulta)
            if not res:
                print("Sin resultados.")
            for f in res:
                aviso = "  (NO SE ENVÍA AL MODELO)" if f["categoria"] in ("en_revision", "historico") else ""
                print(f"[{f['puntaje']}] {f['fuente']} · {f['seccion']} · {f['version']} · {f['estado']}{aviso}")
                print("    " + f["texto"][:240].replace("\n", " ") + ("…" if len(f["texto"]) > 240 else ""))
            return 0

        if args.orden == "correr":
            plataforma = cargar_plataforma(args.plataforma)
            corrida = Corrida.crear(
                plataforma, proyecto,
                ids=_lista(args.casos), bloques=_lista(args.bloques),
                criticidades=_lista(args.criticidad), formas=_lista(args.forma),
                incluir_anexo_a=args.incluir_anexo_a, repeticiones=args.repeticiones,
                autorizo_modelo_real=args.autorizo_modelo_real,
                permitir_instrucciones_pendientes=args.permitir_instrucciones_pendientes,
                etiqueta=args.etiqueta, tipo=args.tipo,
            )
            print(f"Corrida creada ({corrida.manifiesto['tipo']}): {corrida.carpeta}")
            print(f"AVISO: {corrida.manifiesto['aviso']}")
            if args.solo_crear:
                return 0
            final = corrida.ejecutar(
                permitir_otro_modelo=args.permitir_otro_modelo, ignorar_memoria=args.ignorar_memoria,
                max_intentos=args.max_intentos or int(proyecto.get("max_intentos_por_unidad", 2)),
                avance=print,
            )
            print(f"Estado final: {final}. Resumen: {corrida.carpeta / 'resumen.md'}")
            return 0 if final == "terminada" else 3

        if args.orden == "reanudar":
            corrida = Corrida(_carpeta_corrida(args.corrida, proyecto))
            final = corrida.ejecutar(
                permitir_otro_modelo=args.permitir_otro_modelo, ignorar_memoria=args.ignorar_memoria,
                forzar=args.forzar,
                max_intentos=args.max_intentos or int(proyecto.get("max_intentos_por_unidad", 2)),
                avance=print,
            )
            print(f"Estado final: {final}. Resumen: {corrida.carpeta / 'resumen.md'}")
            return 0 if final == "terminada" else 3

        if args.orden == "estado":
            print(estado_breve(_carpeta_corrida(args.corrida, proyecto)))
            return 0

        if args.orden == "resumen":
            print(escribir_resumen(_carpeta_corrida(args.corrida, proyecto)))
            return 0

        if args.orden == "hoja":
            print(escribir_hoja(_carpeta_corrida(args.corrida, proyecto)))
            return 0

        if args.orden == "corridas":
            hubo = False
            for base in _todas_las_carpetas(proyecto):
                carpetas = sorted(p for p in base.iterdir() if (p / "manifiesto.json").exists()) if base.exists() else []
                print(f"== {base.relative_to(rutas.raiz())}: {len(carpetas)}")
                for p in carpetas:
                    print("   " + estado_breve(p))
                hubo |= bool(carpetas)
            if not hubo:
                print("No hay corridas.")
            return 0

        if args.orden == "calibrar":
            from .calibracion import escribir_calibracion, texto_md
            carpetas = [_carpeta_corrida(c, proyecto) for c in args.corridas]
            destino = Path(args.destino).expanduser() if args.destino else carpetas[0]
            datos = escribir_calibracion(carpetas, destino)
            print(texto_md(datos))
            print(f"Escrito: {destino / 'calibracion.md'} y calibracion.json")
            return 0

        if args.orden == "prefiltro":
            from .prefiltro import escribir_prefiltro, texto_md
            carpeta = _carpeta_corrida(args.corrida, proyecto)
            print(texto_md(escribir_prefiltro(carpeta)))
            print(f"Escrito: {carpeta / 'prefiltro.md'} y prefiltro.csv")
            return 0

        if args.orden == "comparar":
            from datetime import datetime
            from .comparacion import comparar
            from .ejecutor import carpetas_de_corridas
            carpetas = [_carpeta_corrida(c, proyecto) for c in args.corridas]
            destino = Path(args.destino).expanduser() if args.destino else \
                carpetas_de_corridas(proyecto)["exploratoria"] / f"COMPARACION_{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            print(f"Comparación preliminar (no es conformidad): {comparar(carpetas, destino)}")
            return 0
    except (ErrorEjecucion, ErrorConfiguracion, ErrorNucleo, ErrorIndice, ValueError) as e:
        print(f"ERROR: {e}")
        return 2
    except KeyboardInterrupt:
        print("\nInterrumpida. Se puede continuar con: harry reanudar <corrida>")
        return 130
    except Exception as e:
        from .adaptadores.base import ErrorAdaptador
        if isinstance(e, ErrorAdaptador):
            print(f"ERROR del adaptador: {e}")
            return 2
        raise
    return 0
