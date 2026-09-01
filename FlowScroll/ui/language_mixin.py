"""语言管理 Mixin。

将 MainWindow 中的语言切换逻辑提取到独立的 Mixin 类，
提供语言切换、UI 重新翻译等操作的统一接口。

使用示例::

    class MainWindow(LanguageMixin, QMainWindow):
        pass

    # 在主窗口中调用
    self.show_language_menu()
    self._apply_language("zh-CN")
"""

from PySide6.QtWidgets import QMenu, QScrollArea
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction

from FlowScroll.core.config import STATE_LOCK, cfg
from FlowScroll.i18n import set_ui_language, tr


class LanguageMixin:
    """语言管理 Mixin，提供统一的语言操作接口。

    所有语言相关的操作都通过此 Mixin 提供，包括：
    - 构建语言菜单
    - 同步菜单选中状态
    - 显示语言菜单
    - 应用语言切换（含 UI 冻结/解冻机制）
    - 重建标签页

    依赖的主窗口属性:
        self.btn_language: 语言按钮
        self.language_menu: 语言菜单
        self.action_lang_auto/zh/en: 语言动作
        self.tray_manager: 托盘管理器
        self.header_subtitle: 副标题标签
        self.tab_widget: 标签页控件
        self.ui_widgets: UI 控件字典
        self.ui_text_widgets: 文本控件字典
        self.ctrl: 控制器实例
    """

    def _build_language_menu(self):
        """构建语言切换菜单（自动/中文/英文）。"""
        self.language_menu = QMenu(self)
        self.action_lang_auto = QAction(tr("main.language.auto"), self)
        self.action_lang_zh = QAction(tr("main.language.zh"), self)
        self.action_lang_en = QAction(tr("main.language.en"), self)
        for action in (self.action_lang_auto, self.action_lang_zh, self.action_lang_en):
            action.setCheckable(True)
            self.language_menu.addAction(action)

        self.action_lang_auto.triggered.connect(lambda: self._apply_language("auto"))
        self.action_lang_zh.triggered.connect(lambda: self._apply_language("zh-CN"))
        self.action_lang_en.triggered.connect(lambda: self._apply_language("en-US"))
        self._sync_language_menu_checks()

    def _sync_language_menu_checks(self):
        """根据配置同步语言菜单的选中状态。"""
        with STATE_LOCK:
            configured = getattr(cfg, "ui_language", "auto")
        self.action_lang_auto.setChecked(configured == "auto")
        self.action_lang_zh.setChecked(configured == "zh-CN")
        self.action_lang_en.setChecked(configured == "en-US")

    def show_language_menu(self) -> None:
        """在语言按钮下方弹出语言选择菜单。"""
        if not hasattr(self, "language_menu"):
            self._build_language_menu()
        self._sync_language_menu_checks()
        self.language_menu.exec(self.btn_language.mapToGlobal(self.btn_language.rect().bottomLeft()))

    def _apply_language(self, language_code: str):
        """切换 UI 语言并持久化配置，采用就地更新以避免标签重建闪烁。"""
        set_ui_language(language_code)
        self.save_presets_to_file()

        # 冻结渲染，防止标签页重建过程中产生中间闪烁
        self.setUpdatesEnabled(False)

        # 保存滚动区域位置，避免切换后内容跳回顶部
        scroll_area = self.centralWidget().findChild(QScrollArea) if self.centralWidget() else None
        scroll_pos = scroll_area.verticalScrollBar().value() if scroll_area else 0

        try:
            self._retranslate_in_place()
        finally:
            if scroll_area:
                scroll_area.verticalScrollBar().setValue(scroll_pos)
            # 在下一个事件循环重新启用渲染并强制刷新，确保重建操作全部完成
            QTimer.singleShot(0, self._unfreeze_ui)

    def _unfreeze_ui(self) -> None:
        """语言切换完成后重新启用界面渲染并刷新。"""
        self.setUpdatesEnabled(True)
        self.repaint()

    def _retranslate_in_place(self):
        """就地更新可翻译的 UI 文本，避免销毁/重建标签页导致的闪烁。

        采用混合策略：
        - 主窗口 chrome（标题、副标题、语言按钮、托盘）就地更新
        - 标签页标题就地更新
        - 需要重建的内部内容通过受控方式刷新
        """
        from FlowScroll.ui.tabs_builder import build_parameter_tab, build_advanced_tab

        # ---- 主窗口 chrome ----
        self.setWindowTitle(f"FlowScroll v{self.ctrl.version_label}")
        self.header_subtitle.setText(tr("main.subtitle"))
        self.btn_language.setText(tr("main.language.button"))
        self.tray_manager.retranslate_ui()
        self._build_language_menu()
        self._refresh_update_indicator()

        # ---- 标签页标题（就地更新，不销毁内容）----
        if hasattr(self, "tab_widget"):
            self.tab_widget.setTabText(0, tr("main.tab.parameters"))
            self.tab_widget.setTabText(1, tr("main.tab.advanced"))

        # ---- 重建内部内容（受控重建，渲染已冻结）----
        # 内部控件的文本（如按钮、标签、提示）需要完整重建才能正确翻译
        saved_index = self.tab_widget.currentIndex() if hasattr(self, "tab_widget") else 0
        self.tab_widget.blockSignals(True)
        self.tab_widget.clear()
        self.ui_widgets = {}

        tab1_widget = build_parameter_tab(self)
        self.tab_widget.addTab(tab1_widget, tr("main.tab.parameters"))
        tab2_widget = build_advanced_tab(self)
        self.tab_widget.addTab(tab2_widget, tr("main.tab.advanced"))

        self.tab_widget.setCurrentIndex(max(0, min(saved_index, self.tab_widget.count() - 1)))
        self.tab_widget.blockSignals(False)
        self.update_tab_height(self.tab_widget.currentIndex())
        self.sync_ui_from_config()
        self.refresh_input_hook_status_ui()
