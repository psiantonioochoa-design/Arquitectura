"""Voz local de Harry: texto a audio, separado del razonamiento y de la identidad.

Este paquete no genera texto, no lee la constitución ni importa el núcleo de
Harry (06_implementacion). Solo convierte en audio el texto que recibe.
No usa micrófono, no escucha y no expone nada fuera de 127.0.0.1.

El orquestador (cli, servidor, cliente, generar) usa solo la biblioteca
estándar de Python 3.9 o superior. Cada motor corre en su propio entorno
aislado (entornos/<motor>/), a través de trabajador.py.
"""

VERSION = "0.1.0"
