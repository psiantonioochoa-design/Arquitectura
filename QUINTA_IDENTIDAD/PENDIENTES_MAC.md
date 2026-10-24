# Comprobaciones pendientes en la Mac

Lo que la sesión en la nube del 24-oct-2026 no pudo hacer, en orden. Cada paso dice qué orden ejecutar y qué resultado esperar. Ninguno cambia Nimbo ni cierra aplicaciones.

## A. Proyecto y pruebas del software

1. Copia o sincroniza esta versión del proyecto en `/Volumes/NOUS/QUINTA_IDENTIDAD/` **sin borrar** la anterior. Por ejemplo, guarda antes una copia con fecha de la carpeta actual.
2. Corre las pruebas con el Python del sistema:

   ```bash
   cd /Volumes/NOUS/QUINTA_IDENTIDAD/06_implementacion && python3 -I -m unittest discover -s pruebas_software
   ```

   Esperado: **51 de 51** con Python 3.9.6. En la nube solo se probaron 3.11, 3.12 y 3.13.
3. Valida los casos y la matriz:

   ```bash
   python3 -I harry.py validar
   ```

   ```bash
   python3 -I trazabilidad/generar_matriz.py
   ```

   Esperado: 92 casos y 84 requisitos, sin problemas.
4. Revisa las decisiones de `06_implementacion/INFORME_etapa_3.md` §7 antes del piloto; sobre todo, si confirmas la exclusión de los ejemplos resueltos y la frase del Anexo A en I-10.

## B. Piloto conversacional (autorizado: sintético, un modelo a la vez)

5. Revisión del equipo. Solo lee; anota la memoria disponible y si Nimbo tiene un modelo cargado en el 11434:

   ```bash
   bash piloto/revisar_equipo.sh
   ```

6. Corre el piloto completo (detalle en `06_implementacion/piloto/README.md`):

   ```bash
   bash piloto/correr_piloto.sh
   ```

   - **Se detiene** si el puerto 11435 está ocupado, si faltan el ejecutable o los modelos, o si fallan las pruebas.
   - Si la memoria disponible es menor de 40 %, la corrida no empieza. **No cierra nada:** decides tú.
7. Comprueba al terminar:
   - que el puerto 11435 quedó libre;
   - que no queda ningún proceso de Ollama iniciado por el piloto (`ps -ax | grep -i ollama`);
   - que el servidor de Nimbo, si existía, sigue igual.
8. Revisa los resultados:
   - **primero**, si quieres, califica a ciegas `PILOTO_<fecha>/comparacion/comparacion_ciega.csv`;
   - después `comparacion.md`, con las respuestas literales;
   - `calibracion.md`, para decidir si cambia `caracteres_por_token`;
   - el `prefiltro.md` de cada corrida, con señales para revisar, no fallas;
   - `memoria_*.csv` y `recortes_de_entrada.txt`.
9. Comprueba **compatibilidad** en la bitácora y el resumen de cada corrida:
   - que `think: false` funcione con los dos modelos (el prefiltro señala si devolvieron razonamiento);
   - que no haya `done_reason=length`, es decir, respuestas truncadas;
   - versión real de Ollama y digest de cada modelo.

## C. Voz local

10. Revisión del equipo para la voz y consulta de tamaños y licencias (no descarga nada):

    ```bash
    cd /Volumes/NOUS/QUINTA_IDENTIDAD/05_voz_harry && bash instalar/revisar_equipo.sh
    ```

    ```bash
    python3 -I instalar/consultar_modelos.py
    ```

11. **Verifica en la consulta:**
    - que existan `voices/bm_george.pt`, `bm_daniel.pt`, `bm_lewis.pt`, `bm_fable.pt`, `em_alex.pt` y `em_santa.pt`;
    - la licencia de los pesos de Kokoro y de Chatterbox;
    - los archivos del modelo `Chatterbox-Multilingual-es-mx-latam`.
12. **Piper:** crea el entorno, descarga las cuatro voces y genera la primera muestra y las seis pruebas (órdenes en `05_voz_harry/README.md`, paso 2). Lee la MODEL_CARD de cada voz: género, acento y **licencia**.
13. **Kokoro:** igual, paso 3. Mide también con `--dispositivo mps` y compara tiempo y memoria con la CPU.
14. **Escucha y valora** en la interfaz, a ciegas si prefieres:

    ```bash
    python3 -I voz.py interfaz --abrir
    ```

    Valora sobre todo:
    - la edad aparente (45–55);
    - el timbre medio-grave;
    - la calidez y la naturalidad;
    - el acento británico del sur en el texto 06;
    - lo comprensible que resulta el español para un oído mexicano;
    - la ausencia de solemnidad y de teatralidad.
15. **Chatterbox** (autorizado el 24-oct-2026): paso 4 del README. Mira antes tamaños y licencia exactos con `consultar_modelos.py --motor chatterbox`. Primero la V2 con la voz incluida; después, si interesa, la V3 o el modelo es-MX.
16. **Sin conexión:** desconecta la red y genera una muestra con cada motor (`voz.py muestra …`). Debe funcionar. Si falla, el error dirá qué peso falta.
17. **Informe:**

    ```bash
    python3 -I voz.py informe
    ```

    Escribe `evaluacion/comparacion_mac-arm64.md`, con las mediciones del M4 y tus valoraciones por separado.

## D. Lo que sigue sin poder declararse, aunque todo lo anterior salga bien

- La constitución, el Anexo A y la conformidad de Harry siguen **sin aprobar**: el piloto es diagnóstico preliminar.
- Una voz solo queda «elegida» cuando tú la eliges escuchando. Las medidas no bastan.
