# Hexapunto: teclado braille Perkins para NVDA

Hexapunto convierte el teclado del ordenador en una **máquina de escribir braille de tipo Perkins**. Se escribe como en la máquina: se pulsan a la vez las teclas de los puntos de cada celda y, al soltarlas, la celda se escribe en el documento, el correo, el campo de búsqueda o la consola donde esté el cursor.

* Versión: 2026.11.18
* Compatible con: NVDA 2026.1 a 2027.1 (y siguientes versiones de la serie 2027)
* Autor: Héctor J. Benítez Corredera
* Código fuente: [github.com/hxebolax/hexapunto](https://github.com/hxebolax/hexapunto)
* Licencia: GNU GPL, versión 2 o posterior


## Qué es y para qué sirve

La máquina Perkins tiene seis teclas, una por cada punto de la celda braille, un espaciador en el centro, una tecla de interlineado a la izquierda y una de retroceso a la derecha. Hexapunto pone esas mismas teclas en el teclado del ordenador, en la fila central, donde descansan los dedos:

| Tecla de la máquina | Tecla del ordenador (distribución clásica) |
| --- | --- |
| Interlineado | A |
| Punto 3, punto 2, punto 1 | S, D, F |
| Espaciador | Barra espaciadora |
| Punto 4, punto 5, punto 6 | J, K, L |
| Retroceso | Ñ |

Sirve para:

* escribir en braille con un ordenador normal, sin línea braille ni teclado braille;
* aprender y practicar braille (hay un modo de práctica que dice cada celda sin escribirla);
* que quien aprendió a escribir con una Perkins, o con pauta y punzón, siga escribiendo como sabe;
* dar clase de braille con un ordenador: el alumnado oye la máquina, la campana del final de la línea y lo que escribe.

## Características

* Braille de **6 puntos** (literario, como la Perkins) y de **8 puntos** (informático).
* **Cuatro distribuciones** de teclas (clásica, pizarra en espejo, fila superior y centrada) y una **personalizada** en la que cada punto va en la tecla que se quiera.
* Las teclas se reconocen por su **posición física**: funciona igual con teclados español, inglés, francés, alemán o cualquier otro.
* **Integración completa con la entrada braille de NVDA**: las celdas pasan por el mismo sistema que un teclado braille de una línea braille, con su tabla, el braille estenográfico, el eco de caracteres, la línea braille, la ayuda de entrada y los gestos de entrada.
* Cualquier **tabla braille** de NVDA, con una tabla automática integral del idioma para 6 puntos.
* **Sonidos de una máquina Perkins real**, con la **campana** que avisa del final de la línea, control de volumen, clics suaves como alternativa y sonidos propios.
* **Órdenes de espacio con puntos** para moverse y editar (flechas, Inicio, Fin, Tabulador, Escape, Suprimir...), las mismas que usan las líneas braille HIMS, Freedom Scientific y Seika.
* **Modo de una mano**, **modo de práctica**, **signos de apertura españoles** automáticos (¿ y ¡) y opción de **bloquear** las demás letras para no escribir por error.
* Solo actúa donde se escribe: en el resto de sitios, y siempre que se pulsa Control, Alt, Windows, Mayúsculas o la tecla NVDA, el teclado funciona como siempre.
* Todas las opciones en **Preferencias de NVDA > Hexapunto (teclado braille)**, con **perfiles de configuración**.
* Totalmente en español.

## Instalación

1. Descarga el archivo `hexapunto-2026.11.18.nvda-addon` desde la página de [versiones del repositorio](https://github.com/hxebolax/hexapunto/releases).
2. Ábrelo (Intro sobre el archivo) con NVDA en marcha y acepta la instalación.
3. Reinicia NVDA cuando lo pida.

Requisitos: NVDA 2026.1 o posterior. No hace falta ninguna línea braille.

## Primeros pasos

1. Abre un editor de texto, por ejemplo el Bloc de notas.
2. Pulsa **NVDA+Alt+B**. Oirás meter el papel en la máquina y NVDA dirá «Teclado braille activado».
3. Escribe la letra «h»: pulsa a la vez **F**, **D** y **K** (puntos 1, 2 y 5) y suéltalas. NVDA dirá «h».
4. Escribe «o» (puntos 1, 3 y 5: **F**, **S** y **K**), «l» (puntos 1, 2 y 3: **F**, **D** y **S**) y «a» (punto 1: **F**).
5. Pulsa la **barra espaciadora** para escribir un espacio y la **A** (interlineado) para pasar a la línea siguiente.
6. Para borrar la última celda, pulsa la **Ñ** (retroceso).
7. Pulsa **NVDA+Alt+B** otra vez para desactivar el teclado braille. Oirás sacar el papel.

La celda se escribe al **soltar todas las teclas**, no al pulsarlas: no hace falta soltarlas exactamente a la vez. Mientras se mantiene una tecla pulsada se pueden añadir más puntos a la misma celda.

## Cómo se escribe

### Las teclas

Con la distribución clásica, los dedos índice, corazón y anular de la mano izquierda escriben los puntos 1, 2 y 3 (F, D y S), y los de la mano derecha los puntos 4, 5 y 6 (J, K y L). Los pulgares van en la barra espaciadora. El meñique izquierdo pulsa el interlineado (A) y el derecho, el retroceso (Ñ). Es la misma postura que en la máquina Perkins.

Además, si no se cambia en las opciones, **Intro** también hace de interlineado y **Retroceso** de retroceso braille. Así lo que esté a medias en la entrada braille (por ejemplo, una palabra en estenografía) se traduce antes de pasar de línea.

### Distribuciones

| Distribución | Puntos 1 2 3 | Puntos 4 5 6 | Interlineado / punto 7 | Retroceso / punto 8 |
| --- | --- | --- | --- | --- |
| Perkins clásica | F D S | J K L | A | Ñ |
| Pizarra, escritura en espejo | J K L | F D S | A (punto 8) | Ñ (punto 7) |
| Fila superior | R E W | U I O | Q | P |
| Centrada | G F D | H J K | S | L |
| Personalizada | a elegir | a elegir | a elegir | a elegir |

* **Pizarra**: para quien aprendió con pauta y punzón, donde se escribe de derecha a izquierda y en espejo. Los puntos 1, 2 y 3 están a la derecha.
* **Fila superior** y **centrada**: útiles si el teclado no deja pulsar a la vez ciertas teclas de la fila central (consulta el apartado «Solución de problemas»).
* **Personalizada**: en las opciones, botón «Personalizar teclas...». Se pulsa el botón de cada punto y luego la tecla que se quiere. Escape cancela y Suprimir deja una tecla opcional sin asignar. Se puede partir de una copia de cualquier otra distribución.

Las letras de la tabla son las de un teclado español. En otros teclados son las teclas que están en el mismo sitio: la Ñ española es la tecla de punto y coma de un teclado inglés.

### 6 y 8 puntos

* Con **6 puntos** (lo normal en una Perkins) la A y la Ñ son el interlineado y el retroceso.
* Con **8 puntos**, la A es el punto 7 y la Ñ el punto 8. Como en todos los teclados braille de NVDA, el **punto 7 solo** borra la última celda, el **punto 8 solo** es Intro y los **puntos 7 y 8 juntos** traducen lo que haya a medias. Intro y Retroceso siguen funcionando como interlineado y retroceso.

### La tabla braille

La tabla decide qué letra sale de cada celda. En las opciones se puede elegir:

* **Automática** (la que viene de fábrica): con 6 puntos, la tabla integral de 6 puntos del idioma de NVDA (en español, «Español grado 1», que es braille literario como el de una Perkins); con 8 puntos, la tabla de entrada de NVDA.
* **La tabla de entrada de NVDA**: la que esté en Preferencias > Braille.
* **Cualquier tabla** de entrada de NVDA, también las estenográficas (grado 2). Con una tabla estenográfica, las celdas se acumulan y la palabra se escribe al pulsar el espaciador, como en cualquier teclado braille con NVDA.

Hexapunto **no cambia la configuración de NVDA**: mientras el teclado braille está activado usa su tabla y, al desactivarlo, vuelve la que tenga NVDA.

### Signos de apertura españoles

En braille español la interrogación y la exclamación usan la misma celda para abrir y para cerrar (puntos 2 6 y puntos 2 3 5); se distinguen por su posición. Con la opción «Signos de apertura españoles automáticos», Hexapunto escribe **¿** y **¡** al principio de la palabra y **?** y **!** en el resto, como se lee en papel. Solo actúa con las tablas de braille literario español (grado 1 y grado 2).

## Dónde actúa el teclado braille

Por defecto, el teclado braille **solo actúa al escribir**: en campos de texto, documentos, terminales y en el modo foco de las páginas web. En los demás sitios (el escritorio, los menús, las listas, el modo exploración de una página) las teclas funcionan como siempre, aunque el teclado braille esté activado. Al volver a un campo de texto, vuelve a actuar sin hacer nada.

Con la opción «Dónde actúa: en todas partes», el teclado braille actúa siempre. Fuera de los campos de texto, cada celda se convierte en la pulsación de la tecla correspondiente: en el modo exploración, por ejemplo, la celda de la «h» salta al siguiente encabezado, como con un teclado braille de una línea.

Además, en cualquier caso:

* Toda tecla pulsada con **Control, Alt, Windows, Mayúsculas o la tecla NVDA** llega sin cambios: Control+C, Alt+Tabulador o NVDA+T funcionan como siempre.
* Las teclas que no son del teclado braille (flechas, Tabulador, Escape, teclas de función, números...) funcionan como siempre, salvo que se active la opción de bloquearlas.
* **NVDA+F2** (dejar pasar la siguiente tecla) también deja pasar las teclas del teclado braille.
* En el **modo dormir** de una aplicación y en la **pantalla de bloqueo** de Windows no actúa.

## Integración con NVDA

Hexapunto no escribe el texto por su cuenta: cada combinación se convierte en un **gesto de teclado braille de NVDA**, igual que los de las líneas braille con teclado braille. Gracias a ello:

* Funcionan la **tabla braille**, el **braille estenográfico**, los **números y mayúsculas** de la tabla y la corrección con el retroceso, exactamente como con un teclado braille de verdad.
* NVDA dice cada carácter según la opción **«Verbalizar caracteres al escribir»**, y en los campos de contraseña no dice lo que se escribe.
* Si hay una **línea braille** conectada, muestra las celdas a medias en la posición del cursor.
* La **ayuda de entrada** (NVDA+1) dice qué hace cada combinación sin ejecutarla.
* En **Preferencias > Gestos de entrada** las combinaciones aparecen con el nombre «Teclado braille Hexapunto» y se pueden **asignar a cualquier orden de NVDA**. Por ejemplo, se puede hacer que espacio con puntos 1 4 5 6 lea la línea actual.
* Los **modificadores virtuales** de la entrada braille (Control, Alt, Mayúsculas, Windows y NVDA) funcionan: activa Control con su orden y escribe la celda de la «s» para pulsar Control+S.
* Las combinaciones de Hexapunto tienen su propio origen de gestos (`hexapunto:`), así que **no cambian nada** de los teclados braille de las líneas braille.

## Órdenes

### Órdenes de teclado

| Orden | Gesto |
| --- | --- |
| Activar o desactivar el teclado braille | NVDA+Alt+B |

Las demás órdenes de Hexapunto no tienen gesto de teclado, pero se les puede asignar uno en Preferencias > Gestos de entrada, categoría «Hexapunto (teclado braille)».

### Combinaciones de espacio con puntos

Se pulsa la barra espaciadora a la vez que los puntos. Funcionan cuando el teclado braille está actuando.

| Combinación | Orden |
| --- | --- |
| Espacio con punto 1 | Flecha arriba |
| Espacio con punto 4 | Flecha abajo |
| Espacio con punto 3 | Flecha izquierda |
| Espacio con punto 6 | Flecha derecha |
| Espacio con punto 2 | Palabra anterior (Control+flecha izquierda) |
| Espacio con punto 5 | Palabra siguiente (Control+flecha derecha) |
| Espacio con puntos 1 2 | Inicio |
| Espacio con puntos 4 5 | Fin |
| Espacio con puntos 1 2 3 | Principio del texto (Control+Inicio) |
| Espacio con puntos 4 5 6 | Final del texto (Control+Fin) |
| Espacio con puntos 1 2 6 | Retroceder página |
| Espacio con puntos 3 4 5 | Avanzar página |
| Espacio con puntos 1 3 | Mayúsculas+Tabulador |
| Espacio con puntos 4 6 | Tabulador |
| Espacio con puntos 1 5 («e») | Escape |
| Espacio con puntos 2 5 | Suprimir |
| Espacio con puntos 1 3 4 («m») | Alt (barra de menús) |
| Espacio con puntos 3 4 | Tecla Windows |
| Espacio con puntos 2 3 4 5 («t») | Alt+Tabulador |
| Espacio con puntos 1 4 5 («d») | Mostrar el escritorio (Windows+D) |
| Espacio con puntos 1 2 3 4 6 | Tecla de aplicaciones (menú contextual) |
| Espacio con puntos 1 3 5 6 («z») | Deshacer (Control+Z) |
| Espacio con puntos 1 3 4 5 («n») | Menú NVDA |
| Espacio con puntos 1 2 3 4 5 6 | Verbalizar todo |
| Espacio con puntos 2 4 («i») | Estado del teclado braille |
| Espacio con puntos 2 3 4 («s») | Cambiar los sonidos |
| Espacio con puntos 1 2 3 4 («p») | Modo de práctica |
| Espacio con puntos 1 2 5 («h») | Lista de combinaciones |

La **lista de combinaciones** (espacio con puntos 1 2 5) muestra en una ventana navegable todas las combinaciones de Hexapunto y lo que hacen en ese momento, incluidas las que se hayan cambiado o añadido en Gestos de entrada.

Una combinación de espacio con puntos sin orden asignada da un pitido grave (se puede cambiar por un aviso hablado o ninguno).

### Órdenes disponibles sin combinación

Estas órdenes están en Gestos de entrada, en la categoría «Hexapunto (teclado braille)», listas para asignarles una combinación o un gesto de teclado:

* Activar o desactivar el modo de una mano.
* Cambiar entre 6 y 8 puntos.
* Pasar a la siguiente distribución de teclas.
* Cambiar dónde actúa (solo en campos de texto o en todas partes).
* Poner el carro al principio de la línea.
* Abrir las opciones de Hexapunto.
* Activar o desactivar los modificadores virtuales Control, Alt, Mayúsculas, Windows y NVDA para la siguiente celda o tecla.
* Pulsar Control+S, Control+A, Control+C, Control+X, Control+V, Intro y Retroceso.

## Modos especiales

### Modo de una mano

Para quien escribe con una sola mano. Los puntos que se pulsan por separado **se suman en la misma celda** y la celda se escribe al pulsar el **espaciador**. Por ejemplo, para la «h» (puntos 1 2 5): pulsa F y D, suelta, pulsa K, suelta y pulsa el espaciador. NVDA dice los puntos que lleva la celda. Con la celda vacía, el espaciador escribe un espacio. El retroceso descarta la celda a medias.

### Modo de práctica

Para aprender braille. Las celdas **no se escriben**: NVDA dice qué carácter sale con la tabla elegida y sus puntos («b, puntos 1 2»). Suenan la máquina y la campana igual que al escribir. Las combinaciones de espacio con puntos siguen funcionando. Se activa y desactiva con espacio con puntos 1 2 3 4 o en las opciones.

### Decir los puntos

Con la opción «Decir los puntos de cada celda escrita», además del carácter, NVDA dice los puntos de cada celda. Muy útil al aprender.

### Bloquear las demás teclas

Una máquina Perkins solo tiene sus teclas. Con la opción «Bloquear las demás letras, números y signos», mientras el teclado braille está actuando, las letras, números y signos que no son del teclado braille no escriben nada y dan un pitido grave. Así no se escriben letras por error. Las flechas, Tabulador, Escape, las teclas de función y los atajos con Control, Alt o Windows siguen funcionando.

## Sonidos y la máquina

Hexapunto suena como una máquina Perkins de verdad: el golpe de las teclas (con varias grabaciones para que no suene siempre igual), el espaciador, el retroceso, el interlineado y la **campana** que avisa del final de la línea.

* **La campana**: Hexapunto cuenta las celdas escritas en la línea, como el carro de la máquina. Cuando faltan las celdas indicadas en las opciones (6 por defecto, sobre una línea de 40 celdas), suena la campana. El interlineado, Intro y el cambio de campo devuelven el carro al principio. Las celdas por línea van de 10 a 100.
* **Tope del margen**: con esta opción, cada celda escrita después del final de la línea da un pitido grave, como el tope de la máquina.
* **Papel**: al activar el teclado braille suena meter el papel y al desactivarlo, sacarlo (se puede quitar).
* **Juegos de sonidos**: máquina Perkins (grabación real), clics suaves o sin sonidos. Se cambian con espacio con puntos 2 3 4.
* **Volumen**: de 0 a 100, independiente del volumen de la voz. El botón «Probar los sonidos» toca una muestra.

### Sonidos propios

Se pueden usar otros sonidos. En las opciones, el botón «Abrir la carpeta de sonidos propios» abre (y crea si hace falta) la carpeta `hexapunto\sonidos` dentro de la carpeta de configuración de NVDA. Pon ahí archivos WAV con estos nombres; los que estén ahí tienen preferencia sobre los del complemento y no se pierden al actualizarlo:

| Archivo | Cuándo suena |
| --- | --- |
| `tecla.wav` (o `tecla1.wav`, `tecla2.wav`...) | Al pulsar las teclas de los puntos (con varios, uno al azar) |
| `espacio.wav` (o `espacio1.wav`...) | Al pulsar el espaciador |
| `retroceso.wav` | Retroceso |
| `linea.wav` | Interlineado y meter el papel |
| `campana.wav` | Campana del final de la línea |
| `papel.wav` | Sacar el papel |

El volumen se aplica a los WAV PCM de 16 bits; los de otros formatos suenan con su volumen original.

## Opciones

Están en el menú NVDA > Preferencias > Opciones > **Hexapunto (teclado braille)**. Todas se guardan en la configuración de NVDA y funcionan con los **perfiles de configuración**: se puede tener, por ejemplo, un perfil para el procesador de textos con otra tabla o sin sonidos.

### General

* **Activar el teclado braille al iniciar NVDA**: queda activado desde el principio.
* **Dónde actúa**: solo al escribir en campos de texto y documentos, o en todas partes (consulta el apartado «Dónde actúa el teclado braille»).
* **Pitido al entrar en un campo donde se escribe en braille**: un pitido corto agudo avisa de que el teclado braille vuelve a actuar.

### Teclado

* **Puntos**: 6 u 8.
* **Distribución de las teclas** y botón **Personalizar teclas...**
* **Intro y Retroceso del teclado hacen de interlineado y retroceso braille**.
* **Modo de una mano**.
* **Bloquear las demás letras, números y signos mientras se escribe en braille**.

### Escritura

* **Tabla braille**: automática, la de NVDA o cualquier tabla de entrada.
* **Signos de apertura españoles automáticos**.
* **Decir los puntos de cada celda escrita**.
* **Modo de práctica**.
* **Aviso de una combinación de espacio con puntos sin orden**: pitido, voz o ninguno.

### Sonidos y máquina

* **Sonidos**: máquina Perkins, clics suaves o sin sonidos.
* **Volumen de los sonidos** y botón **Probar los sonidos**.
* **Sonido de meter y sacar el papel**.
* **Campana cerca del final de la línea**, **celdas por línea** y **celdas que faltan cuando suena la campana**.
* **Pitido grave al pasar del final de la línea**.
* Botón **Abrir la carpeta de sonidos propios**.

### Órdenes

* Botón **Ver la lista de combinaciones**.

El botón **Restablecer los valores de fábrica** pone todas las opciones del panel como vienen al instalar (se guardan al pulsar Aceptar o Aplicar).

## Solución de problemas

### Algunas combinaciones no se escriben

Muchos teclados, sobre todo los de portátil, no pueden detectar ciertas combinaciones de tres o más teclas pulsadas a la vez (es una limitación del propio teclado, llamada «ghosting»). Si una letra no sale nunca:

1. Prueba la distribución **Fila superior** o **Centrada**, que usan otras teclas.
2. Crea una distribución **personalizada** con las teclas que tu teclado detecte bien.
3. Usa el **modo de una mano**, que no necesita pulsar más de una o dos teclas a la vez.
4. Los teclados mecánicos y los de juego suelen detectar cualquier combinación («N-key rollover»).

### Las letras normales no escriben

Si el teclado braille está activado y actúa en el sitio donde estás, F, D, S, J, K, L, A, Ñ y la barra espaciadora son teclas braille. Desactívalo con NVDA+Alt+B, o deja pasar una tecla con NVDA+F2.

### En una página web no escribe

En el modo exploración las letras sirven para moverse por la página, y el teclado braille no actúa. Entra en el campo de edición (Intro o NVDA+Espacio para pasar al modo foco) y escribe.

### Sale texto raro o letras que no son

Comprueba la tabla braille en las opciones (o con espacio con puntos 2 4, que dice la tabla en uso). Para escribir braille literario de 6 puntos en español, usa «Español grado 1»; la tabla «Español 8 puntos» es braille informático.

### Control remoto

Mientras NVDA controla otro ordenador con el acceso remoto, las teclas van al otro ordenador y el teclado braille local no actúa.

## Información para desarrolladores

### Compilar el complemento

Hace falta Python 3.11 o posterior, [SCons](https://scons.org/) y [Markdown](https://python-markdown.github.io/). Para generar las plantillas de traducción, también GNU gettext.

```
pip install scons markdown
scons
```

Se genera `hexapunto-2026.11.18.nvda-addon` en la carpeta raíz. Este archivo `readme.md` se convierte en la documentación del complemento (`doc/es/readme.html`), la que abre NVDA desde la Tienda de complementos. Con `scons pot` se genera la plantilla de traducción `hexapunto.pot`.

### Pruebas automáticas

Las pruebas usan versiones simuladas de los módulos de NVDA, así que no hace falta NVDA:

```
pip install pytest wxPython
python -m pytest tests
```

La prueba del panel de opciones usa además el `gui/guiHelper.py` del código fuente de NVDA. Indica su carpeta con la variable de entorno `NVDA_SOURCE` (por ejemplo `..\nvda\source`); si no lo encuentra, esa prueba se omite.

### Estructura

| Archivo | Contenido |
| --- | --- |
| `addon/globalPlugins/hexapunto/__init__.py` | Complemento global: órdenes, eventos, perfiles y panel de opciones |
| `addon/globalPlugins/hexapunto/motor.py` | Gancho del teclado, detección de combinaciones y envío a NVDA |
| `addon/globalPlugins/hexapunto/gesto.py` | Gesto de entrada braille propio (origen `hexapunto:`) |
| `addon/globalPlugins/hexapunto/distribuciones.py` | Distribuciones de teclas por código de exploración |
| `addon/globalPlugins/hexapunto/maquina.py` | Sonidos, volumen, campana y posición del carro |
| `addon/globalPlugins/hexapunto/comandos.py` | Órdenes de espacio con puntos y emulación de teclas |
| `addon/globalPlugins/hexapunto/ajustes.py` | Especificación de la configuración y tablas automáticas |
| `addon/globalPlugins/hexapunto/panel.py` | Panel de opciones y diálogos de teclas |
| `addon/globalPlugins/hexapunto/compat.py` | Diferencias entre NVDA 2026.1 y 2027.x |
| `addon/sounds` | Sonidos de la máquina Perkins |
| `tests` | Pruebas automáticas |

### Cómo funciona por dentro

1. El motor se registra en `inputCore.decide_handleRawKey`, que NVDA consulta con cada pulsación antes de procesarla. Se trabaja con **códigos de exploración**, así que la distribución no depende del idioma del teclado.
2. Las teclas de puntos se capturan y se acumulan mientras se mantienen pulsadas. Al soltarlas todas, la combinación pasa al hilo principal de NVDA.
3. Allí se crea un `HexapuntoGesture`, subclase de `BrailleInputGesture`, con un identificador propio (`hexapunto:dot1+dot2`) seguido de los genéricos (`bk:dots`), y se ejecuta con `inputCore.manager.executeGesture`. NVDA hace el resto: retrotraducción con liblouis, braille estenográfico, eco, línea braille, ayuda de entrada y gestos de entrada.
4. Las teclas que emula NVDA no se capturan: NVDA 2026.3 y posteriores pasan `injected=True` y, en 2026.1 y 2026.2, se comprueba `keyboardHandler.ignoreInjected` y la tecla virtual `VK_PACKET` de los caracteres Unicode.
5. La entrada braille está en `braille.input` desde NVDA 2026.3 y en `brailleInput` antes; `compat.py` elige la que exista sin provocar avisos de obsolescencia.

## Créditos

* Grabaciones de la máquina Perkins: «brailler.wav» de DennyD74 en [Freesound](https://freesound.org/people/DennyD74/sounds/611444/), con licencia [Creative Commons 0](https://creativecommons.org/publicdomain/zero/1.0/) (dominio público). La campana es un sonido sintetizado.
* Las combinaciones de espacio con puntos siguen las de las líneas braille HIMS, Freedom Scientific y Seika documentadas en la guía de NVDA.
* Basado en el modo Perkins del lector de pantalla Tiresias, del mismo autor.
* Plantilla de complementos de la comunidad de NVDA.
* «Perkins» es una marca de Perkins School for the Blind; Hexapunto no tiene relación con ella y solo usa el nombre para describir el tipo de máquina que emula.

## Licencia

Copyright (C) 2026 Héctor J. Benítez Corredera.

Este programa es software libre: puedes redistribuirlo y modificarlo según los términos de la Licencia Pública General de GNU publicada por la Free Software Foundation, versión 2 de la licencia o (a tu elección) cualquier versión posterior. Consulta el archivo `COPYING.txt`.

## Registro de cambios

### 2026.11.18

Primera versión pública.

* Teclado braille Perkins de 6 y 8 puntos sobre el teclado del ordenador.
* Distribuciones Perkins clásica, pizarra en espejo, fila superior, centrada y personalizada, por posición física de las teclas.
* Integración completa con la entrada braille de NVDA: tablas, braille estenográfico, eco, línea braille, ayuda de entrada, gestos de entrada y modificadores virtuales.
* Tabla automática integral del idioma para 6 puntos.
* Sonidos de una máquina Perkins real, campana de fin de línea, tope del margen, volumen y sonidos propios.
* Órdenes de espacio con puntos configurables desde Gestos de entrada y lista de combinaciones.
* Modo de una mano, modo de práctica, decir los puntos, bloqueo de las demás teclas y signos de apertura españoles automáticos.
* Panel de opciones en las preferencias de NVDA, con perfiles de configuración.
* Compatible con NVDA 2026.1 a 2027.1.
