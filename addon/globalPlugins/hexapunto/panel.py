# Hexapunto: teclado braille Perkins para NVDA.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.
# Consulta el archivo COPYING.txt para más detalles.

"""Interfaz de opciones: panel «Hexapunto» de las preferencias de NVDA.

Incluye el diálogo para personalizar las teclas y el pequeño diálogo que
captura una tecla del teclado físico.
"""

from __future__ import annotations

import os
from typing import Any

import addonHandler
import brailleTables
import gui
import inputCore
import keyboardHandler
import wx
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel
from logHandler import log

from . import ajustes, distribuciones
from .distribuciones import ALL_ROLES, SCAN_ESCAPE

addonHandler.initTranslation()

#: Teclas virtuales que no se pueden usar en el teclado braille (modificadores y bloqueos).
_FORBIDDEN_VKS = frozenset(
	[0x10, 0x11, 0x12, 0x14, 0x5B, 0x5C, 0x5D, 0x90, 0x91, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5],
)
#: Papeles que pueden quedarse sin tecla.
_OPTIONAL_ROLES = ("dot7", "dot8", distribuciones.ROLE_LINE_FEED, distribuciones.ROLE_BACKSPACE)


def _addGroup(sHelper: guiHelper.BoxSizerHelper, parent: wx.Window, label: str) -> guiHelper.BoxSizerHelper:
	"""Añade un grupo con título (wx.StaticBoxSizer) y devuelve su ayudante."""
	sizer = wx.StaticBoxSizer(wx.VERTICAL, parent, label=label)
	group = guiHelper.BoxSizerHelper(parent, sizer=sizer)
	sHelper.addItem(group)
	return group


class KeyCaptureDialog(wx.Dialog):
	"""Espera a que se pulse una tecla y devuelve su código de exploración.

	Escuchar con ``inputCore.decide_handleRawKey`` permite recibir la tecla
	por su posición física, igual que la recibirá el teclado braille.
	Escape cancela y Suprimir deja el papel sin tecla (si puede quedarse sin
	ella). Las teclas modificadoras y las extendidas (flechas, Insert...) no
	se capturan: siguen funcionando con normalidad.
	"""

	NO_KEY = -1
	_VK_DELETE = 0x2E

	def __init__(self, parent: wx.Window, roleName: str, optional: bool, keyboard: Any) -> None:
		# Translators: title of the dialog that waits for a key
		super().__init__(parent, title=_("Asignar tecla"))
		self.scanCode: int | None = None
		self._keyboard = keyboard
		self._optional = optional
		self._registered = False
		self._done = False
		#: Lo actualiza el hilo de la interfaz; el gancho solo lo lee.
		self._active = True
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		if optional:
			message = _(
				# Translators: instructions of the key capture dialog; {role} is e.g. "Punto 1"
				"Pulsa la tecla que quieres usar para «{role}». Escape cancela y Suprimir la deja sin tecla.",
			).format(role=roleName)
		else:
			message = _(
				# Translators: instructions of the key capture dialog; {role} is e.g. "Punto 1"
				"Pulsa la tecla que quieres usar para «{role}». Escape cancela.",
			).format(role=roleName)
		sHelper.addItem(wx.StaticText(self, label=message))
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		if optional:
			# Translators: button to leave a braille keyboard key without any key
			noKeyButton = buttons.addButton(self, label=_("Sin tecla"))
			noKeyButton.Bind(wx.EVT_BUTTON, lambda evt: self._finish(self.NO_KEY))
		# Translators: button to cancel the key capture
		cancel = buttons.addButton(self, id=wx.ID_CANCEL, label=_("Cancelar"))
		cancel.Bind(wx.EVT_BUTTON, lambda evt: self._finish(None))
		sHelper.addDialogDismissButtons(buttons)
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		self.CentreOnParent()
		self.Bind(wx.EVT_CLOSE, lambda evt: self._finish(None))
		self.Bind(wx.EVT_ACTIVATE, self._onActivate)
		self._register()

	def _onActivate(self, evt: wx.ActivateEvent) -> None:
		self._active = evt.GetActive()
		evt.Skip()

	def _register(self) -> None:
		if self._keyboard is not None:
			self._keyboard.suspended = True
		inputCore.decide_handleRawKey.register(self._onRawKey)
		self._registered = True

	def _unregister(self) -> None:
		if self._registered:
			inputCore.decide_handleRawKey.unregister(self._onRawKey)
			self._registered = False
		if self._keyboard is not None:
			self._keyboard.suspended = False

	def _onRawKey(
		self,
		vkCode: int = 0,
		scanCode: int = 0,
		extended: bool = False,
		pressed: bool = True,
		injected: bool = False,
		**kwargs: Any,
	) -> bool:
		"""Hilo del gancho del teclado: no se llama a wx salvo con ``wx.CallAfter``."""
		if injected or not self._registered or self._done or not self._active or not pressed:
			return True
		if vkCode == 0xE7 or keyboardHandler.ignoreInjected:
			# Caracteres Unicode enviados por programas y teclas que emula NVDA.
			return True
		if vkCode == self._VK_DELETE:
			if self._optional:
				wx.CallAfter(self._finish, self.NO_KEY)
				return False
			return True
		if extended or vkCode in _FORBIDDEN_VKS or not scanCode:
			return True
		if scanCode == SCAN_ESCAPE:
			wx.CallAfter(self._finish, None)
			return False
		wx.CallAfter(self._finish, scanCode)
		return False

	def _finish(self, scanCode: int | None) -> None:
		if self._done:
			return
		self._done = True
		self._unregister()
		self.scanCode = scanCode
		if self.IsModal():
			self.EndModal(wx.ID_OK if scanCode is not None else wx.ID_CANCEL)

	def Destroy(self) -> bool:  # noqa: N802 - nombre de wxPython
		self._unregister()
		return super().Destroy()


class CustomKeysDialog(wx.Dialog):
	"""Elige la tecla de cada punto y de cada tecla de la máquina."""

	def __init__(self, parent: wx.Window, keys: dict[str, int], dots: int, keyboard: Any) -> None:
		# Translators: title of the dialog to customize the braille keyboard keys
		super().__init__(parent, title=_("Personalizar las teclas del teclado braille"))
		self.keys = dict(keys)
		self._dots = dots
		self._keyboard = keyboard
		self._buttons: dict[str, wx.Button] = {}
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		intro = _(
			# Translators: explanation at the top of the custom keys dialog
			"Pulsa un botón y después la tecla que quieras para ese punto o esa tecla de la máquina. "
			"Las teclas se reconocen por su posición en el teclado, no por la letra impresa.",
		)
		sHelper.addItem(wx.StaticText(self, label=intro))
		grid = wx.FlexGridSizer(cols=2, vgap=guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS, hgap=20)
		for index, role in enumerate(ALL_ROLES):
			button = wx.Button(self, label=self._buttonLabel(role))
			button.Bind(wx.EVT_BUTTON, lambda evt, r=role: self._capture(r))
			self._buttons[role] = button
			grid.Add(button, flag=wx.EXPAND)
			if index == len(ALL_ROLES) - 1 and len(ALL_ROLES) % 2:
				grid.AddSpacer(0)
		sHelper.addItem(grid)
		bottom = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that copies a built in layout into the custom layout
		resetButton = bottom.addButton(self, label=_("&Copiar de una distribución..."))
		resetButton.Bind(wx.EVT_BUTTON, self._onCopyLayout)
		sHelper.addItem(bottom)
		sHelper.addDialogDismissButtons(wx.OK | wx.CANCEL, separated=True)
		self.Bind(wx.EVT_BUTTON, self._onOk, id=wx.ID_OK)
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		self.CentreOnParent()
		self._buttons["dot1"].SetFocus()

	def _buttonLabel(self, role: str) -> str:
		# Translators: label of a button in the custom keys dialog, e.g. "Punto 1: F"
		label = _("{role}: {key}").format(
			role=distribuciones.roleLabel(role),
			key=distribuciones.keyName(self.keys.get(role, 0)),
		)
		if self._dots == 6 and role in ("dot7", "dot8"):
			# Translators: appended to dots 7 and 8 when the keyboard uses 6 dots
			label += " " + _("(solo con 8 puntos)")
		return label

	def _refresh(self) -> None:
		for role, button in self._buttons.items():
			button.SetLabel(self._buttonLabel(role))
		self.Layout()

	def _capture(self, role: str) -> None:
		dialog = KeyCaptureDialog(
			self, distribuciones.roleLabel(role), role in _OPTIONAL_ROLES, self._keyboard
		)
		try:
			if dialog.ShowModal() == wx.ID_OK and dialog.scanCode is not None:
				if dialog.scanCode == KeyCaptureDialog.NO_KEY:
					self.keys[role] = 0
				else:
					self.keys[role] = dialog.scanCode
				self._refresh()
		finally:
			dialog.Destroy()
		self._buttons[role].SetFocus()

	def _onCopyLayout(self, evt: wx.CommandEvent) -> None:
		layouts = distribuciones.builtinLayouts()
		with wx.SingleChoiceDialog(
			self,
			# Translators: prompt to choose a layout to copy into the custom layout
			_("Elige la distribución que quieres copiar:"),
			# Translators: title of the dialog to copy a layout
			_("Copiar distribución"),
			[layout.name for layout in layouts],
		) as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				self.keys = dict(layouts[dialog.GetSelection()].keys)
				self._refresh()

	def _onOk(self, evt: wx.CommandEvent) -> None:
		missing = [r for r in ALL_ROLES if r not in _OPTIONAL_ROLES and not self.keys.get(r)]
		conflicts = distribuciones.findConflicts(self.keys, self._dots)
		if missing or conflicts:
			lines: list[str] = []
			for role in missing:
				# Translators: error, a mandatory key has no key assigned
				lines.append(_("«{role}» no tiene tecla.").format(role=distribuciones.roleLabel(role)))
			for a, b in conflicts:
				lines.append(
					# Translators: error, two roles share the same key
					_("«{a}» y «{b}» usan la misma tecla.").format(
						a=distribuciones.roleLabel(a),
						b=distribuciones.roleLabel(b),
					),
				)
			gui.messageBox(
				"\n".join(lines),
				# Translators: title of the error message of the custom keys dialog
				_("Teclas no válidas"),
				wx.OK | wx.ICON_ERROR,
				self,
			)
			return
		self.EndModal(wx.ID_OK)


class HexapuntoSettingsPanel(SettingsPanel):
	# Translators: title of the add-on settings panel
	title = _("Hexapunto (teclado braille)")
	#: Teclado braille del complemento (lo pone el GlobalPlugin).
	keyboard: Any = None

	def makeSettings(self, settingsSizer: wx.BoxSizer) -> None:
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self._customKeys = ajustes.customKeys()
		self._makeGeneral(sHelper)
		self._makeKeyboard(sHelper)
		self._makeWriting(sHelper)
		self._makeSounds(sHelper)
		self._makeCommands(sHelper)
		# Translators: button that sets every option of the panel back to its default value
		defaults = sHelper.addItem(wx.Button(self, label=_("&Restablecer los valores de fábrica")))
		defaults.Bind(wx.EVT_BUTTON, self._onDefaults)
		self._loadValues()

	# ------------------------------------------------------------------ grupos
	def _makeGeneral(self, sHelper: guiHelper.BoxSizerHelper) -> None:
		# Translators: group of options in the settings panel
		group = _addGroup(sHelper, self, _("General"))
		box = group.sizer.GetStaticBox()
		self.enableOnStartup = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("&Activar el teclado braille al iniciar NVDA")),
		)
		self._scopeValues = [ajustes.SCOPE_EDITABLE, ajustes.SCOPE_ALWAYS]
		scopeLabels = [
			# Translators: choice of where the braille keyboard works
			_("Solo al escribir en campos de texto y documentos (el resto del teclado normal)"),
			# Translators: choice of where the braille keyboard works
			_("En todas partes (también emula teclas en menús, listas y modo exploración)"),
		]
		self.scope = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("&Dónde actúa:"),
			wx.Choice,
			choices=scopeLabels,
		)
		self.announceActivationInField = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("Pitido al entrar en un campo donde se escribe en &braille")),
		)

	def _makeKeyboard(self, sHelper: guiHelper.BoxSizerHelper) -> None:
		# Translators: group of options in the settings panel
		group = _addGroup(sHelper, self, _("Teclado"))
		box = group.sizer.GetStaticBox()
		self._dotsValues = [6, 8]
		self.dots = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("&Puntos:"),
			wx.Choice,
			# Translators: choices of the number of dots
			choices=[
				_("6 puntos (braille literario, como la máquina Perkins)"),
				_("8 puntos (braille informático)"),
			],
		)
		self._layouts = distribuciones.allLayouts(self._customKeys)
		self.layout = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("&Distribución de las teclas:"),
			wx.Choice,
			choices=[layout.name for layout in self._layouts],
		)
		self.layout.Bind(wx.EVT_CHOICE, lambda evt: self._updateLayoutDescription())
		self.layoutDescription = group.addItem(wx.StaticText(box, label=""))
		# Translators: button that opens the custom keys dialog
		customizeButton = group.addItem(wx.Button(box, label=_("&Personalizar teclas...")))
		customizeButton.Bind(wx.EVT_BUTTON, self._onCustomize)
		self.enterAndBackspace = group.addItem(
			wx.CheckBox(
				box,
				# Translators: option in the settings panel
				label=_("Intro y Retroceso del teclado hacen de i&nterlineado y retroceso braille"),
			),
		)
		self.oneHand = group.addItem(
			wx.CheckBox(
				box,
				# Translators: option in the settings panel
				label=_("Modo de &una mano (los puntos se suman y el espaciador escribe la celda)"),
			),
		)
		self.blockOtherKeys = group.addItem(
			wx.CheckBox(
				box,
				# Translators: option in the settings panel
				label=_("&Bloquear las demás letras, números y signos mientras se escribe en braille"),
			),
		)

	def _makeWriting(self, sHelper: guiHelper.BoxSizerHelper) -> None:
		# Translators: group of options in the settings panel
		group = _addGroup(sHelper, self, _("Escritura"))
		box = group.sizer.GetStaticBox()
		self._tableValues, tableLabels = self._tableChoices()
		self.table = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("&Tabla braille:"),
			wx.Choice,
			choices=tableLabels,
		)
		self.spanishMarks = group.addItem(
			wx.CheckBox(
				box,
				# Translators: option in the settings panel
				label=_("Signos de apertura españoles automáticos (¿ y ¡ al principio de la palabra)"),
			),
		)
		self.speakDots = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("Decir los &puntos de cada celda escrita")),
		)
		self.practiceMode = group.addItem(
			wx.CheckBox(
				box,
				# Translators: option in the settings panel
				label=_("Modo de prá&ctica: decir cada celda sin escribirla (para aprender braille)"),
			),
		)
		self._unassignedValues = [ajustes.UNASSIGNED_BEEP, ajustes.UNASSIGNED_SPEECH, ajustes.UNASSIGNED_NONE]
		self.unassignedFeedback = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("Aviso de una combinación de espacio con puntos sin orden:"),
			wx.Choice,
			# Translators: choices of the feedback for unassigned chords
			choices=[_("Pitido"), _("Decirlo con la voz"), _("Ninguno")],
		)

	def _makeSounds(self, sHelper: guiHelper.BoxSizerHelper) -> None:
		# Translators: group of options in the settings panel
		group = _addGroup(sHelper, self, _("Sonidos y máquina"))
		box = group.sizer.GetStaticBox()
		self._soundsValues = [ajustes.SOUNDS_PERKINS, ajustes.SOUNDS_SOFT, ajustes.SOUNDS_NONE]
		self.sounds = group.addLabeledControl(
			# Translators: label of a combo box in the settings panel
			_("&Sonidos:"),
			wx.Choice,
			choices=[
				# Translators: choice of sound theme
				_("Máquina Perkins (grabación real)"),
				# Translators: choice of sound theme
				_("Clics suaves"),
				# Translators: choice of sound theme
				_("Sin sonidos"),
			],
		)
		self.volume = group.addLabeledControl(
			# Translators: label of a spin control in the settings panel
			_("&Volumen de los sonidos (0 a 100):"),
			nvdaControls.SelectOnFocusSpinCtrl,
			min=0,
			max=100,
			initial=80,
		)
		# Translators: button that plays a sample of the sounds
		testButton = group.addItem(wx.Button(box, label=_("Pro&bar los sonidos")))
		testButton.Bind(wx.EVT_BUTTON, self._onTestSounds)
		self.paperSounds = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("Sonido de meter y sacar el papel al activar y desactivar")),
		)
		self.bell = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("Ca&mpana cerca del final de la línea")),
		)
		self.lineLength = group.addLabeledControl(
			# Translators: label of a spin control in the settings panel
			_("Celdas por &línea:"),
			nvdaControls.SelectOnFocusSpinCtrl,
			min=10,
			max=100,
			initial=40,
		)
		self.bellCells = group.addLabeledControl(
			# Translators: label of a spin control in the settings panel
			_("La campana suena cuando faltan estas celdas:"),
			nvdaControls.SelectOnFocusSpinCtrl,
			min=1,
			max=20,
			initial=6,
		)
		self.marginStop = group.addItem(
			# Translators: option in the settings panel
			wx.CheckBox(box, label=_("Pitido grave al pasar del final de la línea (tope del margen)")),
		)
		# Translators: button that opens the folder for the user's own sounds
		folderButton = group.addItem(wx.Button(box, label=_("Abrir la carpeta de s&onidos propios")))
		folderButton.Bind(wx.EVT_BUTTON, self._onOpenSoundsFolder)

	def _makeCommands(self, sHelper: guiHelper.BoxSizerHelper) -> None:
		# Translators: group of options in the settings panel
		group = _addGroup(sHelper, self, _("Órdenes"))
		box = group.sizer.GetStaticBox()
		text = _(
			# Translators: explanation in the commands group of the settings panel
			"Las combinaciones de espacio con puntos son órdenes de NVDA: se cambian en "
			"Preferencias > Gestos de entrada, categoría «Hexapunto (teclado braille)», "
			"y a cualquier combinación se le puede asignar cualquier orden de NVDA.",
		)
		group.addItem(wx.StaticText(box, label=text))
		# Translators: button that shows the list of chord commands
		listButton = group.addItem(wx.Button(box, label=_("&Ver la lista de combinaciones")))
		listButton.Bind(wx.EVT_BUTTON, lambda evt: showCommandList())

	# ------------------------------------------------------------------ valores
	def _tableChoices(self) -> tuple[list[str], list[str]]:
		auto = ajustes.autoTableFileName()
		if auto:
			try:
				autoName = brailleTables.getTable(auto).displayName
			except LookupError:
				autoName = auto
			# Translators: choice of the automatic braille table; {table} is its name
			autoLabel = _("Automática: {table} con 6 puntos; con 8, la tabla de entrada de NVDA").format(
				table=autoName,
			)
		else:
			# Translators: choice of the automatic braille table when the language has none
			autoLabel = _("Automática: la tabla de entrada de NVDA")
		values = [ajustes.TABLE_AUTO, ajustes.TABLE_NVDA]
		labels = [
			autoLabel,
			# Translators: choice of braille table
			_("La tabla de entrada de NVDA (Preferencias > Braille)"),
		]
		for table in brailleTables.listTables():
			if not table.input:
				continue
			values.append(table.fileName)
			if table.contracted:
				# Translators: a contracted braille table; {table} is its name
				labels.append(_("{table} (estenográfico)").format(table=table.displayName))
			else:
				labels.append(table.displayName)
		return values, labels

	@staticmethod
	def _select(control: wx.Choice, values: list[Any], value: Any) -> None:
		try:
			control.SetSelection(values.index(value))
		except ValueError:
			control.SetSelection(0)

	def _loadValues(self, defaults: bool = False) -> None:
		def value(key: str) -> Any:
			if defaults:
				return config_default(key)
			return ajustes.get(key)

		self.enableOnStartup.SetValue(bool(value("enableOnStartup")))
		self._select(self.scope, self._scopeValues, value("scope"))
		self.announceActivationInField.SetValue(bool(value("announceActivationInField")))
		self._select(self.dots, self._dotsValues, int(value("dots") or 6))
		self._select(self.layout, [layout.id for layout in self._layouts], value("layout"))
		self.enterAndBackspace.SetValue(bool(value("enterAndBackspaceAsPerkins")))
		self.oneHand.SetValue(bool(value("oneHand")))
		self.blockOtherKeys.SetValue(bool(value("blockOtherKeys")))
		self._select(self.table, self._tableValues, value("table"))
		self.spanishMarks.SetValue(bool(value("spanishMarks")))
		self.speakDots.SetValue(bool(value("speakDots")))
		self.practiceMode.SetValue(bool(value("practiceMode")))
		self._select(self.unassignedFeedback, self._unassignedValues, value("unassignedFeedback"))
		self._select(self.sounds, self._soundsValues, value("sounds"))
		self.volume.SetValue(int(value("volume")))
		self.paperSounds.SetValue(bool(value("paperSounds")))
		self.bell.SetValue(bool(value("bell")))
		self.lineLength.SetValue(int(value("lineLength")))
		self.bellCells.SetValue(int(value("bellCells")))
		self.marginStop.SetValue(bool(value("marginStop")))
		self._updateLayoutDescription()

	def _updateLayoutDescription(self) -> None:
		index = self.layout.GetSelection()
		if 0 <= index < len(self._layouts):
			self.layoutDescription.SetLabel(self._layouts[index].description)
			self.layoutDescription.Wrap(self.scaleSize(500))
			self.Layout()

	# ------------------------------------------------------------------ acciones
	def _onCustomize(self, evt: wx.CommandEvent) -> None:
		index = self.layout.GetSelection()
		current = self._layouts[index] if 0 <= index < len(self._layouts) else self._layouts[0]
		start = dict(self._customKeys) if current.id == distribuciones.CUSTOM_ID else dict(current.keys)
		dots = self._dotsValues[max(0, self.dots.GetSelection())]
		with CustomKeysDialog(self, start, dots, self.keyboard) as dialog:
			if dialog.ShowModal() != wx.ID_OK:
				return
			self._customKeys = dialog.keys
		self._layouts = distribuciones.allLayouts(self._customKeys)
		self.layout.SetSelection(len(self._layouts) - 1)
		self._updateLayoutDescription()

	def _onTestSounds(self, evt: wx.CommandEvent) -> None:
		"""Toca una muestra con las opciones elegidas (sin guardarlas)."""
		from . import maquina

		saved = {key: ajustes.get(key) for key in ("sounds", "volume")}
		try:
			ajustes.setValue("sounds", self._soundsValues[max(0, self.sounds.GetSelection())])
			ajustes.setValue("volume", self.volume.GetValue())
			player = maquina.SoundPlayer()
			for name in (maquina.KEY, maquina.KEY, maquina.SPACE, maquina.KEY, maquina.BELL):
				player._playNow(name)
				wx.MilliSleep(160)
		except Exception:
			log.error("Hexapunto: error probando los sonidos", exc_info=True)
		finally:
			for key, val in saved.items():
				ajustes.setValue(key, val)

	def _onOpenSoundsFolder(self, evt: wx.CommandEvent) -> None:
		from . import maquina

		folder = maquina.userSoundsDir()
		try:
			os.makedirs(folder, exist_ok=True)
			os.startfile(folder)
		except OSError:
			log.error("Hexapunto: no se pudo abrir %s", folder, exc_info=True)

	def _onDefaults(self, evt: wx.CommandEvent) -> None:
		import ui

		self._loadValues(defaults=True)
		# Translators: reported after restoring the default values in the settings panel
		ui.message(_("Valores de fábrica puestos. Pulsa Aceptar o Aplicar para guardarlos."))

	def onSave(self) -> None:
		ajustes.setValue("enableOnStartup", self.enableOnStartup.GetValue())
		ajustes.setValue("scope", self._scopeValues[max(0, self.scope.GetSelection())])
		ajustes.setValue("announceActivationInField", self.announceActivationInField.GetValue())
		ajustes.setValue("dots", self._dotsValues[max(0, self.dots.GetSelection())])
		ajustes.setValue("layout", self._layouts[max(0, self.layout.GetSelection())].id)
		ajustes.setCustomKeys(self._customKeys)
		ajustes.setValue("enterAndBackspaceAsPerkins", self.enterAndBackspace.GetValue())
		ajustes.setValue("oneHand", self.oneHand.GetValue())
		ajustes.setValue("blockOtherKeys", self.blockOtherKeys.GetValue())
		ajustes.setValue("table", self._tableValues[max(0, self.table.GetSelection())])
		ajustes.setValue("spanishMarks", self.spanishMarks.GetValue())
		ajustes.setValue("speakDots", self.speakDots.GetValue())
		ajustes.setValue("practiceMode", self.practiceMode.GetValue())
		ajustes.setValue(
			"unassignedFeedback", self._unassignedValues[max(0, self.unassignedFeedback.GetSelection())]
		)
		ajustes.setValue("sounds", self._soundsValues[max(0, self.sounds.GetSelection())])
		ajustes.setValue("volume", self.volume.GetValue())
		ajustes.setValue("paperSounds", self.paperSounds.GetValue())
		ajustes.setValue("bell", self.bell.GetValue())
		ajustes.setValue("lineLength", self.lineLength.GetValue())
		ajustes.setValue("bellCells", self.bellCells.GetValue())
		ajustes.setValue("marginStop", self.marginStop.GetValue())
		if self.keyboard is not None:
			self.keyboard.reloadSettings()

	def isValid(self) -> bool:
		if self.bellCells.GetValue() >= self.lineLength.GetValue():
			self._validationErrorMessageBox(
				# Translators: validation error in the settings panel
				_("La campana tiene que sonar antes del final de la línea."),
				# Translators: name of the option with the error
				_("La campana suena cuando faltan estas celdas"),
			)
			return False
		return super().isValid()


def config_default(key: str) -> Any:
	"""Valor de fábrica de una opción, sacado de la especificación."""
	import config

	try:
		return config.conf.getConfigValidation((ajustes.SECTION, key)).default
	except Exception:
		log.debugWarning("Hexapunto: sin valor por defecto para %s", key, exc_info=True)
		return None


def showCommandList() -> None:
	"""Muestra en una ventana navegable las combinaciones de Hexapunto y sus órdenes."""
	import html

	import ui

	from .gesto import SOURCE

	rows: list[tuple[str, str, str]] = []
	try:
		mappings = inputCore.manager.getAllGestureMappings()
		for category, scripts in mappings.items():
			for scriptName, info in scripts.items():
				for gestureId in info.gestures:
					if not gestureId.lower().startswith(SOURCE + ":"):
						continue
					_source, text = inputCore.getDisplayTextForGestureIdentifier(gestureId)
					rows.append((text, scriptName, category))
	except Exception:
		log.error("Hexapunto: no se pudo obtener la lista de órdenes", exc_info=True)
	rows.sort(key=lambda r: (len(r[0]), r[0]))
	# Translators: title of the window with the list of chord commands
	title = _("Combinaciones de Hexapunto")
	if not rows:
		# Translators: shown when there are no chord commands
		body = "<p>" + html.escape(_("No hay ninguna combinación asignada.")) + "</p>"
	else:
		header = "<tr><th>{}</th><th>{}</th><th>{}</th></tr>".format(
			# Translators: column header in the list of chord commands
			html.escape(_("Combinación")),
			# Translators: column header in the list of chord commands
			html.escape(_("Orden")),
			# Translators: column header in the list of chord commands
			html.escape(_("Categoría")),
		)
		body = (
			"<table>"
			+ header
			+ "".join(
				f"<tr><td>{html.escape(c)}</td><td>{html.escape(s)}</td><td>{html.escape(cat)}</td></tr>"
				for c, s, cat in rows
			)
			+ "</table>"
		)
	intro = _(
		# Translators: text above the list of chord commands
		"Pulsa el espaciador a la vez que los puntos. Puedes cambiar estas combinaciones "
		"en Preferencias > Gestos de entrada.",
	)
	ui.browseableMessage(
		f"<h1>{html.escape(title)}</h1><p>{html.escape(intro)}</p>{body}", title, isHtml=True
	)
