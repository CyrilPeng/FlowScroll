from FlowScroll.core.config import cfg, set_config_attr
import os
import webbrowser

from FlowScroll.i18n import tr


def _persist_config_change(main_window, attr_name, value, after_change=None):
    """线程安全地更新配置属性并持久化到文件。通过 set_config_attr 加锁写入 cfg。"""
    set_config_attr(attr_name, value)
    if after_change is not None:
        after_change(value)
    main_window.save_presets_to_file()


def build_parameter_tab(main_window):
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
    )

    from FlowScroll.ui.components import UpwardComboBox, SpeedCurveWidget
    from FlowScroll.ui.helpers import create_card, create_h_line, add_slider_row
    from FlowScroll.ui.styles import (
        get_new_badge_style,
        get_hint_block_style,
    )
    from FlowScroll.ui.utils import resource_path

    tab1_widget = QWidget()
    tab1_layout = QVBoxLayout(tab1_widget)
    tab1_layout.setContentsMargins(0, 16, 0, 0)
    tab1_layout.setSpacing(20)
    tab1_layout.setAlignment(Qt.AlignTop)

    core_card, core_layout = create_card()

    # 实时速度曲线可视化组件
    # 拖动 sensitivity / dead_zone / speed_factor 任意滑块时
    # 曲线会实时重绘以反映最新的参数组合效果。
    speed_curve = SpeedCurveWidget()
    speed_curve.update_params(cfg.sensitivity, cfg.dead_zone, cfg.speed_factor)
    main_window.ui_widgets["speed_curve"] = speed_curve

    def _update_speed_curve(attr_name, value):
        """核心参数变化时，持久化并同步刷新速度曲线。"""
        _persist_config_change(main_window, attr_name, value)
        # 从 main_window.ui_widgets 取值以避免捕获时未注册的竞态
        curve = main_window.ui_widgets.get("speed_curve")
        if curve is not None:
            curve.update_params(cfg.sensitivity, cfg.dead_zone, cfg.speed_factor)

    main_window.ui_widgets["sensitivity"] = add_slider_row(
        core_layout,
        "sensitivity",
        "ic_speed.svg",
        tr("param.sensitivity"),
        cfg.sensitivity,
        1.0,
        5.0,
        lambda v: _update_speed_curve("sensitivity", v),
        decimals=1,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["speed_factor"] = add_slider_row(
        core_layout,
        "speed_factor",
        "ic_power.svg",
        tr("param.speed_factor"),
        cfg.speed_factor,
        0.01,
        10.00,
        lambda v: _update_speed_curve("speed_factor", v),
        decimals=2,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["dead_zone"] = add_slider_row(
        core_layout,
        "dead_zone",
        "ic_target.svg",
        tr("param.dead_zone"),
        cfg.dead_zone,
        0.0,
        100.0,
        lambda v: _update_speed_curve("dead_zone", v),
        decimals=1,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["overlay_size"] = add_slider_row(
        core_layout,
        "overlay_size",
        "ic_size.svg",
        tr("param.overlay_size"),
        cfg.overlay_size,
        20,
        150,
        lambda v: _persist_config_change(
            main_window,
            "overlay_size",
            v,
            after_change=lambda new_value: (
                main_window.ctrl.bridge.update_size.emit(int(new_value)),
                main_window.ctrl.bridge.preview_size.emit(),
            ),
        ),
        decimals=0,
    )

    # 在核心参数卡片尾部插入速度曲线可视化（带说明）
    core_layout.addWidget(create_h_line())
    curve_hint = QLabel(tr("param.speed_curve_hint"))
    curve_hint.setWordWrap(True)
    curve_hint.setStyleSheet(get_hint_block_style())
    core_layout.addWidget(curve_hint)
    core_layout.addWidget(speed_curve)

    tab1_layout.addWidget(core_card)

    # 预设管理区域。
    lbl_preset = QLabel(tr("tab.presets.title"))
    lbl_preset.setObjectName("SectionTitle")
    tab1_layout.addWidget(lbl_preset)

    preset_card, preset_layout_card = create_card()

    preset_row = QHBoxLayout()
    preset_row.setSpacing(12)

    main_window.combo_presets = UpwardComboBox()
    main_window.combo_presets.addItems(main_window._all_preset_names())
    from FlowScroll.core.config import get_preset_display_name
    main_window.combo_presets.setCurrentText(
        get_preset_display_name(main_window.ctrl.current_preset_name)
    )
    main_window.combo_presets.currentTextChanged.connect(
        main_window.load_selected_preset
    )
    main_window.combo_presets.setFocusPolicy(Qt.NoFocus)
    main_window.combo_presets.setCursor(Qt.PointingHandCursor)
    main_window.combo_presets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    main_window.combo_presets.setFixedHeight(38)
    preset_row.addWidget(main_window.combo_presets, 1)

    btn_save = QPushButton(tr("tab.presets.save"))
    btn_save.setObjectName("BtnPrimary")
    btn_save.setFocusPolicy(Qt.NoFocus)
    btn_save.setCursor(Qt.PointingHandCursor)
    save_icon_path = resource_path(os.path.join("FlowScroll", "resources", "ic_folder.svg"))
    if os.path.exists(save_icon_path):
        btn_save.setIcon(QIcon(save_icon_path))
        btn_save.setIconSize(QSize(16, 16))
    btn_save.clicked.connect(lambda: main_window.save_new_preset(main_window.prompt_new_preset_name()))
    preset_row.addWidget(btn_save)

    btn_del = QPushButton(tr("tab.presets.delete"))
    btn_del.setObjectName("BtnDanger")
    btn_del.setFocusPolicy(Qt.NoFocus)
    btn_del.setCursor(Qt.PointingHandCursor)
    btn_del.clicked.connect(main_window.delete_preset)
    preset_row.addWidget(btn_del)

    preset_layout_card.addLayout(preset_row)

    tab1_layout.addWidget(preset_card)

    # 作者与发布信息区域。
    author_layout = QHBoxLayout()
    author_layout.setAlignment(Qt.AlignCenter)
    author_layout.setSpacing(4)

    main_window.btn_github = QPushButton()
    main_window.btn_github.setCursor(Qt.PointingHandCursor)
    main_window.btn_github.setObjectName("BtnIcon")

    # 更新徽标，默认隐藏，在检测到状态变化后显示。
    main_window.btn_new_badge = QPushButton("NEW")
    main_window.btn_new_badge.setCursor(Qt.PointingHandCursor)
    main_window.btn_new_badge.setFocusPolicy(Qt.NoFocus)
    main_window.btn_new_badge.setStyleSheet(get_new_badge_style())
    main_window.btn_new_badge.setFixedHeight(20)
    main_window.btn_new_badge.setVisible(False)
    main_window.btn_new_badge.clicked.connect(
        lambda: webbrowser.open(
            getattr(
                main_window.ctrl,
                "github_url",
                "",
            )
            or "https://github.com/CyrilPeng/FlowScroll/releases"
        )
    )

    gh_path = resource_path(os.path.join("FlowScroll", "resources", "github_icon.svg"))
    if os.path.exists(gh_path):
        main_window.btn_github.setIcon(QIcon(gh_path))
        main_window.btn_github.setIconSize(QSize(20, 20))

    main_window.btn_github.setText(f" {tr('tab.author')}")

    main_window.btn_github.clicked.connect(
        lambda: webbrowser.open(
            getattr(main_window.ctrl, "github_url", "")
            or "https://github.com/CyrilPeng/FlowScroll"
        )
    )

    author_layout.addWidget(main_window.btn_new_badge)
    author_layout.addWidget(main_window.btn_github)
    tab1_layout.addLayout(author_layout)

    return tab1_widget


def build_advanced_tab(main_window):
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QIcon, QPainter, QPixmap
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QCheckBox,
        QPushButton,
    )

    from FlowScroll.ui.helpers import create_card, create_h_line, add_toggle_row
    from FlowScroll.ui.styles import get_hotkey_label_style, get_warning_banner_style
    from FlowScroll.ui.utils import resource_path

    tab2_widget = QWidget()
    tab2_layout = QVBoxLayout(tab2_widget)
    tab2_layout.setContentsMargins(0, 16, 0, 0)
    tab2_layout.setSpacing(20)
    tab2_layout.setAlignment(Qt.AlignTop)

    # ---- 滚动行为 ----
    lbl_scroll = QLabel(tr("tab.advanced.section.scroll_behavior"))
    lbl_scroll.setObjectName("SectionTitle")
    tab2_layout.addWidget(lbl_scroll)

    scroll_card, scroll_layout = create_card()

    main_window.input_hook_status_label = QLabel()
    main_window.input_hook_status_label.setWordWrap(True)
    main_window.input_hook_status_label.setVisible(False)
    main_window.input_hook_status_label.setStyleSheet(get_warning_banner_style())
    scroll_layout.addWidget(main_window.input_hook_status_label)
    scroll_layout.addWidget(create_h_line())

    # 横向滚动快捷键设置行。
    row_horizontal = QWidget()
    row_horizontal_layout = QHBoxLayout(row_horizontal)
    row_horizontal_layout.setContentsMargins(0, 0, 0, 0)
    row_horizontal_layout.setSpacing(12)

    chk_horizontal = QCheckBox(tr("tab.advanced.enable_horizontal"))
    chk_horizontal.setChecked(cfg.enable_horizontal)
    chk_horizontal.toggled.connect(
        lambda v: _persist_config_change(main_window, "enable_horizontal", v)
    )
    chk_horizontal.setFocusPolicy(Qt.NoFocus)
    chk_horizontal.setCursor(Qt.PointingHandCursor)
    main_window.ui_widgets["enable_horizontal"] = chk_horizontal
    row_horizontal_layout.addWidget(chk_horizontal)
    row_horizontal_layout.addStretch()

    main_window.lbl_hotkey = QLabel()
    main_window.lbl_hotkey.setStyleSheet(get_hotkey_label_style())
    main_window.update_hotkey_label()
    row_horizontal_layout.addWidget(main_window.lbl_hotkey)

    btn_gear = QPushButton()
    btn_gear.setObjectName("BtnIcon")
    btn_gear.setCursor(Qt.PointingHandCursor)
    gear_path = resource_path(os.path.join("FlowScroll", "resources", "ic_gear.svg"))
    if os.path.exists(gear_path):
        btn_gear.setIcon(QIcon(gear_path))
        btn_gear.setIconSize(QSize(16, 16))
    else:
        btn_gear.setText("\u2699")
    btn_gear.clicked.connect(main_window.open_hotkey_dialog)
    row_horizontal_layout.addWidget(btn_gear)
    main_window.ui_widgets["horizontal_hotkey_button"] = btn_gear

    scroll_layout.addWidget(row_horizontal)
    scroll_layout.addWidget(create_h_line())

    # 惯性滚动设置行。
    row_inertia = QWidget()
    row_inertia_layout = QHBoxLayout(row_inertia)
    row_inertia_layout.setContentsMargins(0, 0, 0, 0)
    row_inertia_layout.setSpacing(12)

    chk_inertia = QCheckBox(tr("tab.advanced.enable_inertia"))
    chk_inertia.setChecked(cfg.enable_inertia)
    chk_inertia.toggled.connect(
        lambda v: _persist_config_change(main_window, "enable_inertia", v)
    )
    chk_inertia.setFocusPolicy(Qt.NoFocus)
    chk_inertia.setCursor(Qt.PointingHandCursor)
    main_window.ui_widgets["enable_inertia"] = chk_inertia
    row_inertia_layout.addWidget(chk_inertia)
    row_inertia_layout.addStretch()

    btn_inertia_gear = QPushButton()
    btn_inertia_gear.setObjectName("BtnIcon")
    btn_inertia_gear.setCursor(Qt.PointingHandCursor)
    gear_path2 = resource_path(os.path.join("FlowScroll", "resources", "ic_gear.svg"))
    if os.path.exists(gear_path2):
        btn_inertia_gear.setIcon(QIcon(gear_path2))
        btn_inertia_gear.setIconSize(QSize(16, 16))
    else:
        btn_inertia_gear.setText("\u2699")
    btn_inertia_gear.clicked.connect(main_window.open_inertia_settings_dialog)
    row_inertia_layout.addWidget(btn_inertia_gear)

    scroll_layout.addWidget(row_inertia)
    scroll_layout.addWidget(create_h_line())

    btn_reverse_mode = QPushButton(tr("tab.advanced.reverse_btn"))
    btn_reverse_mode.setObjectName("BtnAdv")
    btn_reverse_mode.setCursor(Qt.PointingHandCursor)
    move_path = resource_path(os.path.join("FlowScroll", "resources", "ic_move.svg"))
    if os.path.exists(move_path):
        btn_reverse_mode.setIcon(QIcon(move_path))
        btn_reverse_mode.setIconSize(QSize(18, 18))
    btn_reverse_mode.clicked.connect(main_window.open_reverse_mode_dialog)
    scroll_layout.addWidget(btn_reverse_mode)

    btn_work_mode = QPushButton(tr("tab.advanced.work_mode_btn"))
    btn_work_mode.setObjectName("BtnAdv")
    btn_work_mode.setCursor(Qt.PointingHandCursor)
    gear_path = resource_path(os.path.join("FlowScroll", "resources", "ic_gear.svg"))
    if os.path.exists(gear_path):
        btn_work_mode.setIcon(QIcon(gear_path))
        btn_work_mode.setIconSize(QSize(18, 18))
    btn_work_mode.clicked.connect(main_window.open_work_mode_dialog)
    scroll_layout.addWidget(btn_work_mode)
    main_window.ui_widgets["work_mode_button"] = btn_work_mode

    tab2_layout.addWidget(scroll_card)

    # ---- 系统集成 ----
    lbl_system = QLabel(tr("tab.advanced.section.system"))
    lbl_system.setObjectName("SectionTitle")
    tab2_layout.addWidget(lbl_system)

    system_card, system_layout = create_card()

    main_window.ui_widgets["minimize_to_tray"] = add_toggle_row(
        system_layout,
        "minimize_to_tray",
        tr("tab.advanced.minimize_to_tray"),
        cfg.minimize_to_tray,
        lambda v: _persist_config_change(main_window, "minimize_to_tray", v),
    )
    system_layout.addWidget(create_h_line())

    add_toggle_row(
        system_layout,
        None,
        tr("tab.advanced.autorun"),
        main_window.ctrl.autostart.is_autorun(),
        main_window.toggle_autorun,
    )
    system_layout.addWidget(create_h_line())

    main_window.ui_widgets["disable_fullscreen"] = add_toggle_row(
        system_layout,
        "disable_fullscreen",
        tr("tab.advanced.disable_fullscreen"),
        cfg.disable_fullscreen,
        lambda v: _persist_config_change(main_window, "disable_fullscreen", v),
    )
    system_layout.addWidget(create_h_line())

    main_window.ui_widgets["hide_overlay"] = add_toggle_row(
        system_layout,
        "hide_overlay",
        tr("tab.advanced.hide_overlay"),
        cfg.hide_overlay,
        lambda v: _persist_config_change(main_window, "hide_overlay", v),
    )

    tab2_layout.addWidget(system_card)

    # ---- 数据与同步 ----
    lbl_data = QLabel(tr("tab.advanced.section.data_sync"))
    lbl_data.setObjectName("SectionTitle")
    tab2_layout.addWidget(lbl_data)

    data_card, data_layout = create_card()

    btn_app_filter = QPushButton(tr("tab.advanced.filter_mode_btn"))
    btn_app_filter.setObjectName("BtnAdv")
    btn_app_filter.setCursor(Qt.PointingHandCursor)
    filter_path = resource_path(
        os.path.join("FlowScroll", "resources", "ic_filter.svg")
    )
    if os.path.exists(filter_path):
        btn_app_filter.setIcon(QIcon(filter_path))
        btn_app_filter.setIconSize(QSize(18, 18))
    btn_app_filter.clicked.connect(main_window.open_filter_mode_dialog)
    data_layout.addWidget(btn_app_filter)
    main_window.ui_widgets["filter_mode_button"] = btn_app_filter

    btn_webdav = QPushButton(tr("tab.advanced.webdav_btn"))
    btn_webdav.setObjectName("BtnAdvSecondary")
    btn_webdav.setCursor(Qt.PointingHandCursor)
    cloud_path = resource_path(os.path.join("FlowScroll", "resources", "ic_cloud.svg"))
    if os.path.exists(cloud_path):
        base_icon = QIcon(cloud_path)
        source_pixmap = base_icon.pixmap(QSize(18, 18))
        shifted_pixmap = QPixmap(18, 20)
        shifted_pixmap.fill(Qt.transparent)
        painter = QPainter(shifted_pixmap)
        painter.drawPixmap(0, 3, source_pixmap)
        painter.end()
        btn_webdav.setIcon(QIcon(shifted_pixmap))
        btn_webdav.setIconSize(QSize(18, 20))
    btn_webdav.clicked.connect(main_window.open_webdav_settings)
    data_layout.addWidget(btn_webdav)

    btn_storage = QPushButton(tr("tab.advanced.config_path_btn"))
    btn_storage.setObjectName("BtnAdvSecondary")
    btn_storage.setCursor(Qt.PointingHandCursor)
    storage_path = resource_path(
        os.path.join("FlowScroll", "resources", "ic_folder.svg")
    )
    if os.path.exists(storage_path):
        btn_storage.setIcon(QIcon(storage_path))
        btn_storage.setIconSize(QSize(18, 18))
    btn_storage.clicked.connect(main_window.open_config_storage_dialog)
    main_window.ui_widgets["config_path_button"] = btn_storage
    data_layout.addWidget(btn_storage)

    tab2_layout.addWidget(data_card)

    main_window.refresh_input_hook_status_ui()
    main_window.refresh_config_storage_ui()

    tab2_layout.addStretch()

    return tab2_widget
