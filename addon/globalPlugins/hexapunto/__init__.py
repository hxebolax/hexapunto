# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Hexapunto: convierte el teclado del ordenador en una máquina de escribir braille Perkins.

Módulos del complemento:

- :mod:`.compat`: diferencias entre versiones de NVDA (2026.1 a 2027.x);
- :mod:`.ajustes`: opciones en la configuración de NVDA (con perfiles);
- :mod:`.distribuciones`: distribuciones de teclas por posición física;
- :mod:`.gesto`: el gesto de entrada que se integra con NVDA;
- :mod:`.motor`: el gancho del teclado y la detección de combinaciones;
- :mod:`.maquina`: sonidos de la máquina y posición del carro;
- :mod:`.comandos`: órdenes de espacio con puntos que vienen de fábrica;
- :mod:`.panel`: el panel de opciones de las preferencias de NVDA.
"""

from __future__ import annotations

from typing import Any

import addonHandler
import config
import globalCommands
import globalPluginHandler
import globalVars
import gui
import inputCore
import ui
from logHandler import log
from scriptHandler import script

from . import ajustes, comandos, distribuciones, gesto
from .comandos import CATEGORY, DEFAULT_GESTURES
from .motor import BrailleKeyboard

addonHandler.initTranslation()

ajustes.register()
gesto.register()

#: Base con las órdenes generadas (emulación de teclas y modificadores virtuales).
#: Se crea con la metaclase de los complementos globales para que NVDA recoja sus gestos.
_GeneratedScripts: type = type(globalPluginHandler.GlobalPlugin)(
	"_GeneratedScripts",
	(globalPluginHandler.GlobalPlugin,),
	{"__module__": __name__, **comandos.generatedScripts()},
)


class GlobalPlugin(_GeneratedScripts):
	"""Complemento global de Hexapunto."""

	def __init__(self) -> None:
		super().__init__()
		self.keyboard = BrailleKeyboard()
		self._panelClass: type | None = None
		config.post_configProfileSwitch.register(self._onProfileSwitch)
		if not globalVars.appArgs.secure:
			from .panel import HexapuntoSettingsPanel

			HexapuntoSettingsPanel.keyboard = self.keyboard
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(HexapuntoSettingsPanel)
			self._panelClass = HexapuntoSettingsPanel
		if ajustes.get("enableOnStartup"):
			import wx

			# Al terminar de arrancar NVDA (cuando ya existe la entrada braille).
			wx.CallAfter(self._enableOnStartup)

	def _enableOnStartup(self) -> None:
		try:
			import api

			self.keyboard.onFocus(api.getFocusObject())
			self.keyboard.setEnabled(True)
		except Exception:
			log.error("Hexapunto: no se pudo activar el teclado al iniciar", exc_info=True)

	def terminate(self) -> None:
		try:
			config.post_configProfileSwitch.unregister(self._onProfileSwitch)
			self.keyboard.terminate()
			if self._panelClass is not None:
				classes = gui.settingsDialogs.NVDASettingsDialog.categoryClasses
				if self._panelClass in classes:
					classes.remove(self._panelClass)
				self._panelClass.keyboard = None
			inputCore.gestureSources.pop(gesto.SOURCE, None)
		except Exception:
			log.error("Hexapunto: error al terminar", exc_info=True)
		super().terminate()

	def _onProfileSwitch(self) -> None:
		self.keyboard.reloadSettings()

	# ================================================================ eventos
	def event_gainFocus(self, obj: Any, nextHandler: Any) -> None:
		try:
			self.keyboard.onFocus(obj)
		except Exception:
			log.debugWarning("Hexapunto: error anotando el foco", exc_info=True)
		nextHandler()

	# ================================================================ órdenes propias
	@script(
		# Translators: description of a command of the add-on
		description=_("Activa o desactiva el teclado braille Perkins"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["toggle"],
	)
	def script_toggle(self, gesture: inputCore.InputGesture) -> None:
		self.keyboard.toggle()

	@script(
		# Translators: description of a command of the add-on
		description=_("Dice el estado del teclado braille: puntos, distribución, tabla y columna"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["status"],
	)
	def script_status(self, gesture: inputCore.InputGesture) -> None:
		ui.message(self.keyboard.statusText())

	@script(
		# Translators: description of a command of the add-on
		description=_("Cambia los sonidos: máquina Perkins, clics suaves o sin sonidos"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["cycleSounds"],
	)
	def script_cycleSounds(self, gesture: inputCore.InputGesture) -> None:
		order = [ajustes.SOUNDS_PERKINS, ajustes.SOUNDS_SOFT, ajustes.SOUNDS_NONE]
		labels = {
			# Translators: reported when changing the sound theme
			ajustes.SOUNDS_PERKINS: _("Sonidos de la máquina Perkins"),
			# Translators: reported when changing the sound theme
			ajustes.SOUNDS_SOFT: _("Clics suaves"),
			# Translators: reported when changing the sound theme
			ajustes.SOUNDS_NONE: _("Sin sonidos"),
		}
		current = ajustes.get("sounds")
		new = order[(order.index(current) + 1) % len(order)] if current in order else order[0]
		ajustes.setValue("sounds", new)
		self.keyboard.machine.player.clearCache()
		ui.message(labels[new])

	@script(
		# Translators: description of a command of the add-on
		description=_("Activa o desactiva el modo de práctica (dice cada celda sin escribirla)"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["togglePractice"],
	)
	def script_togglePractice(self, gesture: inputCore.InputGesture) -> None:
		on = not ajustes.get("practiceMode")
		ajustes.setValue("practiceMode", on)
		# Translators: reported when toggling practice mode
		ui.message(_("Modo de práctica activado") if on else _("Modo de práctica desactivado"))

	@script(
		# Translators: description of a command of the add-on
		description=_("Activa o desactiva el modo de una mano"),
		category=CATEGORY,
	)
	def script_toggleOneHand(self, gesture: inputCore.InputGesture) -> None:
		on = not ajustes.get("oneHand")
		ajustes.setValue("oneHand", on)
		self.keyboard.reloadSettings()
		# Translators: reported when toggling one hand mode
		ui.message(_("Modo de una mano activado") if on else _("Modo de una mano desactivado"))

	@script(
		# Translators: description of a command of the add-on
		description=_("Cambia entre braille de 6 y de 8 puntos"),
		category=CATEGORY,
	)
	def script_toggleDots(self, gesture: inputCore.InputGesture) -> None:
		new = 6 if int(ajustes.get("dots") or 6) == 8 else 8
		ajustes.setValue("dots", new)
		self.keyboard.reloadSettings()
		# Translators: reported when changing the number of dots; {n} is 6 or 8
		ui.message(_("{n} puntos").format(n=new))

	@script(
		# Translators: description of a command of the add-on
		description=_("Pasa a la siguiente distribución de teclas"),
		category=CATEGORY,
	)
	def script_cycleLayout(self, gesture: inputCore.InputGesture) -> None:
		layouts = distribuciones.allLayouts(ajustes.customKeys())
		ids = [layout.id for layout in layouts]
		current = ajustes.get("layout")
		index = (ids.index(current) + 1) % len(ids) if current in ids else 0
		ajustes.setValue("layout", ids[index])
		self.keyboard.reloadSettings()
		ui.message(layouts[index].name)

	@script(
		# Translators: description of a command of the add-on
		description=_("Cambia dónde actúa el teclado braille: solo en campos de texto o en todas partes"),
		category=CATEGORY,
	)
	def script_toggleScope(self, gesture: inputCore.InputGesture) -> None:
		if ajustes.get("scope") == ajustes.SCOPE_ALWAYS:
			ajustes.setValue("scope", ajustes.SCOPE_EDITABLE)
			# Translators: reported when changing where the braille keyboard works
			ui.message(_("Teclado braille solo en campos de texto"))
		else:
			ajustes.setValue("scope", ajustes.SCOPE_ALWAYS)
			# Translators: reported when changing where the braille keyboard works
			ui.message(_("Teclado braille en todas partes"))

	@script(
		# Translators: description of a command of the add-on
		description=_("Pone el carro de la máquina al principio de la línea (columna 1)"),
		category=CATEGORY,
	)
	def script_resetColumn(self, gesture: inputCore.InputGesture) -> None:
		self.keyboard.machine.reset()
		# Translators: reported when the carriage is reset
		ui.message(_("Columna 1"))

	@script(
		# Translators: description of a command of the add-on
		description=_("Muestra la lista de combinaciones de espacio con puntos y sus órdenes"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["commandList"],
	)
	def script_commandList(self, gesture: inputCore.InputGesture) -> None:
		from .panel import showCommandList

		showCommandList()

	@script(
		# Translators: description of a command of the add-on
		description=_("Abre las opciones de Hexapunto"),
		category=CATEGORY,
	)
	def script_openSettings(self, gesture: inputCore.InputGesture) -> None:
		if self._panelClass is None:
			return
		import wx

		wx.CallAfter(
			gui.mainFrame.popupSettingsDialog,
			gui.settingsDialogs.NVDASettingsDialog,
			self._panelClass,
		)

	@script(
		# Translators: description of a command of the add-on
		description=_("Muestra el menú NVDA"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["showNvdaMenu"],
	)
	def script_showNvdaMenu(self, gesture: inputCore.InputGesture) -> None:
		globalCommands.commands.script_showGui(gesture)

	@script(
		# Translators: description of a command of the add-on
		description=_("Verbaliza todo desde el cursor"),
		category=CATEGORY,
		gestures=DEFAULT_GESTURES["sayAll"],
	)
	def script_sayAll(self, gesture: inputCore.InputGesture) -> None:
		globalCommands.commands.script_sayAll(gesture)
