from pathlib import Path

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.data_store import DataStore
from app.engine import BinderEngine
from app.hotkeys import get_keyboard, is_hotkey_valid, normalize_hotkey
from app.log_store import append_event
from .bind_editor_dialog import BindEditorDialog
from .hotkey_editor_dialog import HotkeyEditorDialog
from .logs_window import LogsWindow
from .update_dialog import UpdateDialog
from .pages import binds, help as help_page, hotkeys, import_export, personalization, profiles, settings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Binder")
        self.setMinimumSize(1100, 720)
        self.logs_window: LogsWindow | None = None
        self._settings_hotkey_handles: list[int] = []
        self.store = DataStore()
        self.engine = BinderEngine(append_event)
        self.engine.start()

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.stack = self._build_stack()

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 14, 14, 12)
        header_layout.setSpacing(10)

        logo_label = QLabel()
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "majestic_transparent.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(
                56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(pixmap)

        title = QLabel("Binder")
        title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        layout.addWidget(header)
        layout.addSpacing(6)

        buttons = [
            "Профили",
            "Бинды",
            "Hotkeys / Макросы",
            "Персонализация",
            "Настройки",
            "Импорт/Экспорт",
            "Помощь / Changelog",
        ]

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(16, 10, 16, 0)
        nav_layout.setSpacing(22)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for idx, name in enumerate(buttons):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(btn)
            btn.setMinimumHeight(34)
            nav_layout.addWidget(btn)

        layout.addWidget(nav_container)
        layout.addStretch(1)
        self.nav_group.buttons()[0].setChecked(True)
        return sidebar

    def _build_stack(self) -> QStackedWidget:
        stack = QStackedWidget()
        self.profiles_page = profiles.ProfilesPage()
        self.profiles_page.create_requested.connect(self.handle_profile_create)
        self.profiles_page.activate_requested.connect(self.handle_profile_activate)
        self.profiles_page.rename_requested.connect(self.handle_profile_rename)
        self.profiles_page.delete_requested.connect(self.handle_profile_delete)
        stack.addWidget(self.profiles_page)

        self.binds_page = binds.BindsPage()
        self.binds_page.add_requested.connect(self.open_bind_editor_create)
        self.binds_page.edit_requested.connect(self.open_bind_editor_edit)
        self.binds_page.delete_requested.connect(self.handle_bind_delete_clicked)
        self.binds_page.copy_requested.connect(self.handle_bind_copy)
        self.binds_page.import_requested.connect(self.handle_binds_import)
        self.binds_page.binder_toggled.connect(self.handle_binder_toggle)
        stack.addWidget(self.binds_page)

        self.hotkeys_page = hotkeys.HotkeysPage()
        self.hotkeys_page.add_requested.connect(self.open_hotkey_editor_create)
        self.hotkeys_page.edit_requested.connect(self.open_hotkey_editor_edit)
        self.hotkeys_page.delete_requested.connect(self.handle_hotkey_delete_clicked)
        self.hotkeys_page.test_requested.connect(self.handle_hotkey_test)
        stack.addWidget(self.hotkeys_page)

        self.personalization_page = personalization.PersonalizationPage()
        self.personalization_page.changed.connect(self.handle_personalization_changed)
        stack.addWidget(self.personalization_page)

        self.settings_page = settings.SettingsPage()
        self.settings_page.logs_requested.connect(self.open_logs_window)
        self.settings_page.settings_changed.connect(self.handle_settings_changed)
        stack.addWidget(self.settings_page)

        self.import_export_page = import_export.ImportExportPage()
        self.import_export_page.export_requested.connect(self.handle_export_profile)
        self.import_export_page.import_new_requested.connect(self.handle_import_new_profile)
        self.import_export_page.import_merge_requested.connect(self.handle_import_into_profile)
        stack.addWidget(self.import_export_page)

        help_page_widget, update_btn = help_page.build_page()
        self.help_page = help_page_widget
        update_btn.clicked.connect(self.open_update_dialog)
        stack.addWidget(help_page_widget)
        self.refresh_all()
        return stack

    def open_logs_window(self) -> None:
        if self.logs_window is None:
            self.logs_window = LogsWindow()
        self.logs_window.show()
        self.logs_window.raise_()
        self.logs_window.activateWindow()

    def open_update_dialog(self) -> None:
        dialog = UpdateDialog(self)
        dialog.exec()

    def open_bind_editor_create(self) -> None:
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        variables = profile.get("variables", {})
        dialog = BindEditorDialog(
            self,
            mode="create",
            existing_triggers=self.store.trigger_set(),
            allowed_prefixes=settings_data.get("trigger_prefixes", ["."]) or ["."],
            allow_no_prefix=bool(settings_data.get("allow_no_prefix", False)),
            variables=variables,
        )
        dialog.saved.connect(self.handle_bind_saved)
        dialog.exec()

    def open_bind_editor_edit(self, bind_id: str) -> None:
        bind_data = self.store.get_bind(bind_id)
        if not bind_data:
            return
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        variables = profile.get("variables", {})
        dialog = BindEditorDialog(
            self,
            mode="edit",
            existing_triggers=self.store.trigger_set(exclude_id=bind_id),
            bind_data=bind_data,
            allowed_prefixes=settings_data.get("trigger_prefixes", ["."]) or ["."],
            allow_no_prefix=bool(settings_data.get("allow_no_prefix", False)),
            variables=variables,
        )
        dialog.saved.connect(self.handle_bind_saved)
        dialog.deleted.connect(self.handle_bind_deleted)
        dialog.exec()

    def handle_profile_create(self) -> None:
        name, ok = QInputDialog.getText(self, "Создать профиль", "Название профиля:")
        if not ok or not name.strip():
            return
        profile = self.store.add_profile(name.strip())
        append_event(
            {
                "type": "profile_created",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"name": profile.get("name")},
            }
        )
        self.refresh_all()

    def handle_profile_activate(self, profile_id: str) -> None:
        if not profile_id:
            return
        self.store.set_active_profile(profile_id)
        profile = self.store.get_profile(profile_id)
        append_event(
            {
                "type": "profile_switched",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"name": profile.get("name")},
            }
        )
        self.refresh_all()

    def handle_profile_rename(self, profile_id: str) -> None:
        profile = self.store.get_profile(profile_id)
        name, ok = QInputDialog.getText(
            self, "Переименовать профиль", "Новое название:", text=profile.get("name", "")
        )
        if not ok or not name.strip():
            return
        if self.store.rename_profile(profile_id, name.strip()):
            append_event(
                {
                    "type": "profile_renamed",
                    "entity": "profile",
                    "profile_id": profile_id,
                    "profile_name": name.strip(),
                    "meta": {"name": name.strip()},
                }
            )
            self.refresh_all()

    def handle_profile_delete(self, profile_id: str) -> None:
        if len(self.store.list_profiles()) <= 1:
            QMessageBox.information(self, "Удаление профиля", "Нельзя удалить последний профиль.")
            return
        profile = self.store.get_profile(profile_id)
        result = QMessageBox.question(
            self,
            "Удалить профиль",
            f"Удалить профиль '{profile.get('name', '')}'?",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return
        if self.store.delete_profile(profile_id):
            append_event(
                {
                    "type": "profile_deleted",
                    "entity": "profile",
                    "profile_id": profile_id,
                    "profile_name": profile.get("name", ""),
                    "meta": {"name": profile.get("name", "")},
                }
            )
            self.refresh_all()

    def handle_bind_saved(self, payload: dict) -> None:
        active_profile = self.store.get_active_profile()
        bind_data = {k: v for k, v in payload.items() if k != "replace_existing"}
        existing = None
        if payload.get("replace_existing"):
            for item in self.store.list_binds():
                if item.get("trigger") == payload.get("trigger") and item.get("id") != payload.get("id"):
                    existing = item
                    break

        if bind_data.get("id"):
            before = self.store.get_bind(bind_data["id"])
            self.store.update_bind(bind_data["id"], bind_data)
            event_type = "bind_edited"
            meta = {
                "trigger": bind_data.get("trigger"),
                "title": bind_data.get("title"),
                "before": before,
                "after": bind_data,
            }
        else:
            if existing:
                self.store.delete_bind(existing["id"])
            created = self.store.add_bind(bind_data)
            event_type = "bind_added"
            meta = {
                "trigger": created.get("trigger"),
                "title": created.get("title"),
            }

        append_event(
            {
                "type": event_type,
                "entity": "bind",
                "profile_id": active_profile.get("id"),
                "profile_name": active_profile.get("name"),
                "meta": meta,
            }
        )
        self.refresh_binds()

    def open_hotkey_editor_create(self) -> None:
        profile = self.store.get_active_profile()
        settings = profile.get("settings", {})
        dialog = HotkeyEditorDialog(
            self,
            mode="create",
            commit_keys=set(settings.get("commit_keys", [])),
            triggers=self.store.trigger_set(profile.get("id")),
            settings_hotkeys=settings.get("hotkeys", {}),
        )
        dialog.saved.connect(self.handle_hotkey_saved)
        dialog.test_requested.connect(self.handle_hotkey_test_steps)
        dialog.exec()

    def open_hotkey_editor_edit(self, hotkey_id: str) -> None:
        hotkey_data = self.store.get_hotkey(hotkey_id)
        if not hotkey_data:
            return
        profile = self.store.get_active_profile()
        settings = profile.get("settings", {})
        dialog = HotkeyEditorDialog(
            self,
            mode="edit",
            hotkey_data=hotkey_data,
            commit_keys=set(settings.get("commit_keys", [])),
            triggers=self.store.trigger_set(profile.get("id")),
            settings_hotkeys=settings.get("hotkeys", {}),
        )
        dialog.saved.connect(self.handle_hotkey_saved)
        dialog.test_requested.connect(self.handle_hotkey_test_steps)
        dialog.exec()

    def handle_hotkey_saved(self, payload: dict) -> None:
        profile = self.store.get_active_profile()
        hotkey_data = dict(payload)
        if hotkey_data.get("id"):
            before = self.store.get_hotkey(hotkey_data["id"])
            self.store.update_hotkey(hotkey_data["id"], hotkey_data)
            event_type = "macro_edited"
            meta = {"before": before, "after": hotkey_data}
        else:
            created = self.store.add_hotkey(hotkey_data)
            event_type = "macro_created"
            meta = {"hotkey_id": created.get("id"), "title": created.get("title")}

        append_event(
            {
                "type": event_type,
                "entity": "hotkey",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": meta,
            }
        )
        self.refresh_hotkeys()

    def handle_hotkey_delete_clicked(self, hotkey_id: str) -> None:
        result = QMessageBox.question(
            self,
            "Удалить макрос",
            "Удалить выбранный макрос?",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if result == QMessageBox.Yes:
            self.handle_hotkey_deleted(hotkey_id)

    def handle_hotkey_deleted(self, hotkey_id: str) -> None:
        profile = self.store.get_active_profile()
        before = self.store.get_hotkey(hotkey_id)
        if self.store.delete_hotkey(hotkey_id):
            append_event(
                {
                    "type": "macro_deleted",
                    "entity": "hotkey",
                    "profile_id": profile.get("id"),
                    "profile_name": profile.get("name"),
                    "meta": {
                        "hotkey_id": hotkey_id,
                        "title": before.get("title") if before else "",
                    },
                }
            )
            self.refresh_hotkeys()

    def handle_hotkey_test(self, hotkey_id: str) -> None:
        hotkey = self.store.get_hotkey(hotkey_id)
        if not hotkey:
            return
        self.handle_hotkey_test_steps(hotkey.get("steps", []), title=hotkey.get("title", ""))

    def handle_hotkey_test_steps(self, steps: list[dict], title: str = "") -> None:
        if not self.engine.available:
            QMessageBox.information(self, "Hotkeys", "Доступно только на Windows.")
            return
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        if not settings_data.get("binder_enabled", True):
            QMessageBox.information(self, "Hotkeys", "Binder выключен. Включите для запуска макроса.")
            return
        self.engine.run_macro_steps(steps, title=title)

    def handle_bind_deleted(self, bind_id: str) -> None:
        active_profile = self.store.get_active_profile()
        before = self.store.get_bind(bind_id)
        if self.store.delete_bind(bind_id):
            append_event(
                {
                    "type": "bind_deleted",
                    "entity": "bind",
                    "profile_id": active_profile.get("id"),
                    "profile_name": active_profile.get("name"),
                    "meta": {
                        "trigger": before.get("trigger") if before else "",
                        "title": before.get("title") if before else "",
                    },
                }
            )
            self.refresh_binds()

    def handle_bind_delete_clicked(self, bind_id: str) -> None:
        result = QMessageBox.question(
            self,
            "Удалить бинд",
            "Удалить выбранный бинд?",
            QMessageBox.Yes | QMessageBox.Cancel,
        )
        if result == QMessageBox.Yes:
            self.handle_bind_deleted(bind_id)

    def handle_bind_copy(self, bind_id: str) -> None:
        bind_data = self.store.get_bind(bind_id)
        if not bind_data:
            return
        base_trigger = bind_data.get("trigger", "")
        suffix = 2
        new_trigger = f"{base_trigger}_copy"
        existing = self.store.trigger_set()
        while new_trigger in existing:
            suffix += 1
            new_trigger = f"{base_trigger}_copy{suffix}"
        new_bind = dict(bind_data)
        new_bind.pop("id", None)
        new_bind["trigger"] = new_trigger
        new_bind["title"] = f"{bind_data.get('title', '')} (копия)".strip()
        created = self.store.add_bind(new_bind)
        QApplication.clipboard().setText(created.get("content", ""))
        append_event(
            {
                "type": "bind_added",
                "entity": "bind",
                "profile_id": self.store.get_active_profile().get("id"),
                "profile_name": self.store.get_active_profile().get("name"),
                "meta": {"trigger": created.get("trigger"), "title": created.get("title"), "copied_from": bind_id},
            }
        )
        self.refresh_binds()

    def handle_binds_import(self) -> None:
        self.handle_import_into_profile(self.store.get_active_profile().get("id"))

    def handle_binder_toggle(self, enabled: bool) -> None:
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        settings_data["binder_enabled"] = enabled
        self.store.update_settings(profile.get("id"), settings_data)
        append_event(
            {
                "type": "settings_changed",
                "entity": "settings",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"binder_enabled": enabled},
            }
        )
        self.update_engine_config()

    def refresh_binds(self) -> None:
        if isinstance(self.binds_page, binds.BindsPage):
            profile = self.store.get_active_profile()
            settings_data = profile.get("settings", {})
            prefix = (settings_data.get("trigger_prefixes") or ["."])[0]
            self.binds_page.set_prefix(prefix)
            self.binds_page.set_binds(self.store.list_binds(profile.get("id")))
            self.binds_page.set_binder_enabled(settings_data.get("binder_enabled", True))
            self.binds_page.set_engine_available(self.engine.available)
        self.update_engine_config()

    def refresh_hotkeys(self) -> None:
        if isinstance(self.hotkeys_page, hotkeys.HotkeysPage):
            profile = self.store.get_active_profile()
            self.hotkeys_page.set_hotkeys(self.store.list_hotkeys(profile.get("id")))
        self.update_engine_config()

    def handle_personalization_changed(self, payload: dict) -> None:
        profile = self.store.get_active_profile()
        self.store.update_variables(profile.get("id"), payload)
        append_event(
            {
                "type": "personalization_changed",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": payload,
            }
        )
        self.update_engine_config()

    def handle_settings_changed(self, payload: dict) -> None:
        profile = self.store.get_active_profile()
        current = profile.get("settings", {})
        merged = {**current, **payload}
        self.store.update_settings(profile.get("id"), merged)
        append_event(
            {
                "type": "settings_changed",
                "entity": "settings",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": payload,
            }
        )
        self.refresh_binds()
        self.update_engine_config()

    def handle_export_profile(self, profile_id: str) -> None:
        profile = self.store.get_profile(profile_id)
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт профиля",
            f"{profile.get('name', 'profile')}.binder.json",
            "Binder Profile (*.binder.json);;JSON (*.json)",
        )
        if not filename:
            return
        data = self.store.export_profile(profile_id)
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        append_event(
            {
                "type": "export",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"file": filename},
            }
        )

    def handle_import_new_profile(self) -> None:
        data = self._read_import_file()
        if not data:
            return
        binds_count = 0
        if isinstance(data, list):
            profile_payload = dict(self.store.get_active_profile())
            profile_payload["name"] = "imported"
            profile_payload["binds"] = data
            profile = self.store.import_profile(profile_payload, name_override="imported")
            binds_count = len(data)
        else:
            name = data.get("name", "imported")
            profile = self.store.import_profile(data, name_override=name)
            binds_count = len(profile.get("binds", []))
        self.store.set_active_profile(profile.get("id"))
        append_event(
            {
                "type": "import",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {
                    "name": profile.get("name"),
                    "count": binds_count,
                    "added": binds_count,
                    "skipped": 0,
                    "conflicts": 0,
                },
            }
        )
        self.refresh_all()

    def handle_import_into_profile(self, profile_id: str) -> None:
        if not profile_id:
            return
        data = self._read_import_file()
        if not data:
            return
        if isinstance(data, list):
            binds_data = data
        elif isinstance(data, dict):
            binds_data = data.get("binds", [])
        else:
            binds_data = []
        if not binds_data:
            return
        mode = self._choose_conflict_mode()
        if not mode:
            return
        existing = {b.get("trigger"): b for b in self.store.list_binds(profile_id)}
        added = 0
        skipped = 0
        conflicts = 0
        for bind in binds_data:
            trigger = bind.get("trigger", "")
            if trigger in existing:
                conflicts += 1
                if mode == "replace":
                    self.store.update_bind(existing[trigger]["id"], bind, profile_id)
                    added += 1
                elif mode == "suffix":
                    suffix = 2
                    new_trigger = f"{trigger}_{suffix}"
                    while new_trigger in existing:
                        suffix += 1
                        new_trigger = f"{trigger}_{suffix}"
                    bind = dict(bind)
                    bind["trigger"] = new_trigger
                    self.store.add_bind(bind, profile_id)
                    existing[new_trigger] = bind
                    added += 1
                elif mode == "skip":
                    skipped += 1
                    continue
            else:
                self.store.add_bind(bind, profile_id)
                existing[trigger] = bind
                added += 1

        profile = self.store.get_profile(profile_id)
        append_event(
            {
                "type": "import",
                "entity": "bind",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {
                    "count": len(binds_data),
                    "added": added,
                    "skipped": skipped,
                    "conflicts": conflicts,
                    "mode": mode,
                },
            }
        )
        self.refresh_binds()

    def _read_import_file(self) -> dict | list | None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт профиля",
            "",
            "Binder Profile (*.binder.json);;JSON (*.json)",
        )
        if not filename:
            return None
        try:
            with open(filename, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return None

    def _choose_conflict_mode(self) -> str | None:
        box = QMessageBox(self)
        box.setWindowTitle("Конфликты триггеров")
        box.setText("Найдены совпадающие триггеры. Выберите режим импорта:")
        replace_btn = box.addButton("Заменить", QMessageBox.AcceptRole)
        suffix_btn = box.addButton("Добавить с суффиксом", QMessageBox.AcceptRole)
        skip_btn = box.addButton("Пропустить конфликтные", QMessageBox.DestructiveRole)
        cancel_btn = box.addButton("Отмена", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == replace_btn:
            return "replace"
        if clicked == suffix_btn:
            return "suffix"
        if clicked == skip_btn:
            return "skip"
        if clicked == cancel_btn:
            return None
        return None

    def update_engine_config(self) -> None:
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        binds_list = self.store.list_binds(profile.get("id"))
        variables = profile.get("variables", {})
        hotkeys_list = self.store.list_hotkeys(profile.get("id"))
        self.engine.update_config(profile, settings_data, binds_list, variables, hotkeys_list)
        self._refresh_settings_hotkeys(settings_data)

    def closeEvent(self, event) -> None:
        self.engine.stop()
        super().closeEvent(event)

    def refresh_all(self) -> None:
        profiles_list = self.store.list_profiles()
        active = self.store.get_active_profile()
        self.profiles_page.set_profiles(profiles_list, active.get("id"))
        settings_data = active.get("settings", {})
        prefix = (settings_data.get("trigger_prefixes") or ["."])[0]
        self.binds_page.set_prefix(prefix)
        self.binds_page.set_binds(self.store.list_binds(active.get("id")))
        self.binds_page.set_binder_enabled(settings_data.get("binder_enabled", True))
        self.binds_page.set_engine_available(self.engine.available)
        self.hotkeys_page.set_hotkeys(self.store.list_hotkeys(active.get("id")))
        self.personalization_page.set_values(active.get("variables", {}))
        self.settings_page.set_settings(settings_data)
        self.import_export_page.set_profiles(profiles_list, active.get("id"))
        self._refresh_help_sections(active)
        self.update_engine_config()

    def _refresh_help_sections(self, profile: dict) -> None:
        if not hasattr(self, "help_page"):
            return
        binds = profile.get("binds", []) or []
        dynamic = {"tips": [], "teleports": [], "news": [], "changelog": []}
        section_map = {
            "hints": "tips",
            "teleports": "teleports",
            "news": "news",
            "changelog": "changelog",
        }
        for bind in binds:
            section = section_map.get(bind.get("help_section"))
            if not section:
                continue
            title = bind.get("title") or bind.get("trigger") or "Бинд"
            category = bind.get("category") or "Без категории"
            content = str(bind.get("content", "") or "").strip()
            preview = content if len(content) <= 160 else f"{content[:157]}..."
            body = preview or "Без описания"
            dynamic[section].append(
                {
                    "title": title,
                    "category": category,
                    "body": body,
                }
            )
        if hasattr(self.help_page, "set_dynamic_items"):
            self.help_page.set_dynamic_items(dynamic)

    def _refresh_settings_hotkeys(self, settings: dict) -> None:
        kb = get_keyboard()
        if kb is None:
            return
        for handle in self._settings_hotkey_handles:
            try:
                kb.remove_hotkey(handle)
            except Exception:
                continue
        self._settings_hotkey_handles = []

        hotkeys = settings.get("hotkeys", {})
        handlers = {
            "toggle": (self._handle_toggle_hotkey, "Вкл/выкл binder"),
            "open": (self._handle_open_hotkey, "Открыть окно"),
            "profile_switch": (self._handle_profile_switch_hotkey, "Переключить профиль"),
        }
        errors: list[str] = []
        for key, (handler, label) in handlers.items():
            combo = normalize_hotkey(str(hotkeys.get(key, "")))
            if not combo:
                continue
            if not is_hotkey_valid(combo):
                errors.append(f"Некорректная комбинация для «{label}»: {combo}. Нажмите «Записать».")
                continue
            try:
                handle = kb.add_hotkey(combo, handler)
            except Exception:
                errors.append(f"Не удалось зарегистрировать «{label}»: {combo}. Нажмите «Записать».")
                continue
            self._settings_hotkey_handles.append(handle)
        self.settings_page.set_hotkey_errors(errors)

    def _handle_toggle_hotkey(self) -> None:
        profile = self.store.get_active_profile()
        settings_data = profile.get("settings", {})
        enabled = not settings_data.get("binder_enabled", True)
        settings_data["binder_enabled"] = enabled
        self.store.update_settings(profile.get("id"), settings_data)
        append_event(
            {
                "type": "settings_changed",
                "entity": "settings",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"binder_enabled": enabled},
            }
        )
        self.refresh_binds()

    def _handle_open_hotkey(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _handle_profile_switch_hotkey(self) -> None:
        profiles = self.store.list_profiles()
        if not profiles:
            return
        active = self.store.get_active_profile()
        ids = [p.get("id") for p in profiles]
        try:
            current_index = ids.index(active.get("id"))
        except ValueError:
            current_index = 0
        next_index = (current_index + 1) % len(ids)
        next_id = ids[next_index]
        self.store.set_active_profile(next_id)
        profile = self.store.get_profile(next_id)
        append_event(
            {
                "type": "profile_switched",
                "entity": "profile",
                "profile_id": profile.get("id"),
                "profile_name": profile.get("name"),
                "meta": {"name": profile.get("name")},
            }
        )
        self.refresh_all()
