# Hexapunto: pruebas automáticas.
# Copyright (C) 2026 hxebolax
# Este archivo está cubierto por la Licencia Pública General de GNU, versión 2 o posterior.

"""Prueba del panel de opciones con wxPython y el ``guiHelper`` real de NVDA.

Se omite si no está wxPython o no se encuentra el código fuente de NVDA.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from typing import Any

import pytest

from conftest import NVDA_SOURCE

wx = pytest.importorskip("wx")
if NVDA_SOURCE is None:
	pytest.skip("no se encuentra el código fuente de NVDA", allow_module_level=True)


def _load(name: str, path: str) -> types.ModuleType:
	spec = importlib.util.spec_from_file_location(name, path)
	assert spec and spec.loader
	module = importlib.util.module_from_spec(spec)
	sys.modules[name] = module
	spec.loader.exec_module(module)
	return module


@pytest.fixture(scope="module")
def guiModules() -> Any:
	app = wx.App(False)
	gui = sys.modules["gui"]
	gui.__path__ = []  # type: ignore[attr-defined]
	# windowUtils necesita las bibliotecas de NVDA: factor de escala 1 en las pruebas.
	sys.modules["windowUtils"] = types.SimpleNamespace(getWindowScalingFactor=lambda handle: 1)
	dpi = _load("gui.dpiScalingHelper", str(NVDA_SOURCE / "gui" / "dpiScalingHelper.py"))
	guiHelper = _load("gui.guiHelper", str(NVDA_SOURCE / "gui" / "guiHelper.py"))
	gui.guiHelper = guiHelper  # type: ignore[attr-defined]

	class SelectOnFocusSpinCtrl(wx.SpinCtrl):
		def __init__(self, parent: Any, min: int = 0, max: int = 100, initial: int = 0, **kw: Any) -> None:
			super().__init__(parent, min=min, max=max, initial=initial)

	nvdaControls = types.ModuleType("gui.nvdaControls")
	nvdaControls.SelectOnFocusSpinCtrl = SelectOnFocusSpinCtrl  # type: ignore[attr-defined]
	sys.modules["gui.nvdaControls"] = nvdaControls
	gui.nvdaControls = nvdaControls  # type: ignore[attr-defined]

	class SettingsPanel(dpi.DpiScalingHelperMixinWithoutInit, wx.Panel):
		"""Igual que el de NVDA en lo que importa: crea el sizer y llama a makeSettings."""

		title = ""

		def __init__(self, parent: Any) -> None:
			super().__init__(parent)
			self.mainSizer = wx.BoxSizer(wx.VERTICAL)
			self.settingsSizer = wx.BoxSizer(wx.VERTICAL)
			self.makeSettings(self.settingsSizer)
			self.mainSizer.Add(self.settingsSizer, flag=wx.ALL | wx.EXPAND)
			self.SetSizer(self.mainSizer)

		def isValid(self) -> bool:
			return True

		def _validationErrorMessageBox(self, *a: Any, **k: Any) -> None:
			self.validationError = a

	sys.modules["gui.settingsDialogs"].SettingsPanel = SettingsPanel  # type: ignore[attr-defined]
	sys.modules.pop("hexapunto.panel", None)
	from hexapunto import panel

	frame = wx.Frame(None)
	yield types.SimpleNamespace(app=app, frame=frame, panel=panel)
	frame.Destroy()
	app.Destroy()


def test_panel_builds_loads_and_saves(env: Any, guiModules: Any) -> None:
	from hexapunto import ajustes

	panelModule = guiModules.panel
	p = panelModule.HexapuntoSettingsPanel(guiModules.frame)
	assert p.dots.GetSelection() == 0
	assert p.table.GetStringSelection().startswith("Automática")
	assert p.layout.GetCount() == 5
	p.dots.SetSelection(1)
	p.layout.SetSelection(1)
	p.volume.SetValue(35)
	p.oneHand.SetValue(True)
	p.onSave()
	assert ajustes.get("dots") == 8
	assert ajustes.get("layout") == "slate"
	assert ajustes.get("volume") == 35
	assert ajustes.get("oneHand") is True
	p._loadValues(defaults=True)
	assert p.dots.GetSelection() == 0 and p.volume.GetValue() == 80
	p.bellCells.SetValue(20)
	p.lineLength.SetValue(15)
	assert p.isValid() is False
	p.Destroy()


def test_custom_keys_dialog(env: Any, guiModules: Any) -> None:
	from hexapunto import distribuciones

	panelModule = guiModules.panel
	keys = dict(distribuciones.getLayout("perkins").keys)
	dialog = panelModule.CustomKeysDialog(guiModules.frame, keys, 6, None)
	assert len(dialog._buttons) == len(distribuciones.ALL_ROLES)
	assert "Punto 1" in dialog._buttons["dot1"].GetLabel()
	dialog.Destroy()


def test_key_capture_dialog_registers_and_unregisters(env: Any, guiModules: Any) -> None:
	import inputCore

	panelModule = guiModules.panel
	dialog = panelModule.KeyCaptureDialog(guiModules.frame, "Punto 1", True, None)
	assert dialog._onRawKey in inputCore.decide_handleRawKey.handlers
	assert dialog._onRawKey(vkCode=0x10, scanCode=0x2A, pressed=True) is True, "Mayúsculas no se captura"
	dialog._finish(0x21)
	assert dialog.scanCode == 0x21
	assert dialog._onRawKey not in inputCore.decide_handleRawKey.handlers
	dialog.Destroy()
