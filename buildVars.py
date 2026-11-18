# Variables de construcción del complemento Hexapunto.
# Cambia este archivo en lugar de sconstruct o de los manifiestos siempre que sea posible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries

# Algunas cadenas de `addon_info` son traducibles y deben aparecer en los archivos .po.
# Gettext solo reconoce las cadenas que se pasan a la función `_`, así que se importa
# una función `_` falsa que devuelve lo mismo que recibe.
from site_scons.site_tools.NVDATool.utils import _


# Información del complemento
addon_info = AddonInfo(
	# Nombre interno del complemento (identificador para NVDA)
	addon_name="hexapunto",
	# Translators: Summary/title for this add-on
	# to be shown on installation and add-on information found in add-on store
	addon_summary=_("Hexapunto: teclado braille Perkins"),
	# Translators: Long description to be shown for this add-on on add-on information from add-on store
	addon_description=_("""Convierte el teclado del ordenador en una máquina de escribir braille de tipo Perkins.
Se escribe pulsando a la vez las teclas de los puntos (F D S y J K L en la distribución clásica), \
con la barra espaciadora como espaciador, teclas de interlineado y retroceso, braille de 6 u 8 puntos, \
cualquier tabla braille de NVDA (integral o estenográfica), sonidos de una máquina real con la campana \
del final de línea, modo de una mano, modo de práctica para aprender braille, \
órdenes de espacio con puntos para moverse y editar, y un panel de opciones muy completo."""),
	# Versión: año.mes.día de la publicación
	addon_version="2026.11.18",
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_("""Primera versión pública.
- Teclado braille Perkins de 6 y 8 puntos con cuatro distribuciones y una personalizable.
- Integración completa con la entrada braille de NVDA: tablas, braille estenográfico, eco, ayuda de entrada y gestos de entrada.
- Sonidos de una máquina Perkins real, campana de fin de línea y control de volumen.
- Modo de una mano, modo de práctica y signos de apertura españoles automáticos.
- Órdenes de espacio con puntos configurables desde «Gestos de entrada».
- Panel de opciones propio en las preferencias de NVDA."""),
	# Autor
	addon_author="hxebolax",
	# Página de la documentación y soporte
	addon_url="https://github.com/hxebolax/hexapunto",
	# Repositorio con el código fuente
	addon_sourceURL="https://github.com/hxebolax/hexapunto",
	# Nombre del archivo de documentación
	addon_docFileName="readme.html",
	# Versión mínima de NVDA compatible
	addon_minimumNVDAVersion="2026.1",
	# Última versión de NVDA probada
	addon_lastTestedNVDAVersion="2027.1",
	# Canal de actualización (None = versiones estables)
	addon_updateChannel=None,
	# Licencia
	addon_license="GPL v2",
	# Dirección de la licencia
	addon_licenseURL="https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
)

# Archivos Python del complemento.
pythonSources: list[str] = [
	"addon/globalPlugins/hexapunto/*.py",
]

# Archivos con cadenas para traducir.
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Archivos que no se incluyen en el paquete .nvda-addon
# (rutas relativas a la carpeta addon).
excludedFiles: list[str] = [
	"*.pyc",
]

# Idioma base del complemento: está escrito en español.
baseLanguage: str = "es"

# Extensiones de Markdown para la documentación (el manual usa tablas).
markdownExtensions: list[str] = [
	"markdown.extensions.tables",
]

# Tablas braille propias (el complemento no añade ninguna).
brailleTables: BrailleTables = {}

# Diccionarios de símbolos propios (el complemento no añade ninguno).
symbolDictionaries: SymbolDictionaries = {}
