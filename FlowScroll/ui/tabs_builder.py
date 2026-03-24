from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QTextEdit,
    QComboBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from FlowScroll.core.config import cfg
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.helpers import create_card, create_h_line, add_slider_row, add_toggle_row
import os

def build_parameter_tab(main_window):
    tab1_widget = QWidget()
    tab1_layout = QVBoxLayout(tab1_widget)
    tab1_layout.setContentsMargins(0, 16, 0, 0)
    tab1_layout.setSpacing(20)
    tab1_layout.setAlignment(Qt.AlignTop)

    core_card, core_layout = create_card()

    main_window.ui_widgets["sensitivity"] = add_slider_row(
        core_layout,
        "sensitivity",
        "ic_speed.svg",
        "加速度曲线 (Sensitivity)",
        cfg.sensitivity,
        1.0,
        5.0,
        lambda v: setattr(cfg, "sensitivity", v),
        decimals=1,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["speed_factor"] = add_slider_row(
        core_layout,
        "speed_factor",
        "ic_power.svg",
        "基础速度倍率 (Base Speed)",
        cfg.speed_factor,
        0.01,
        10.00,
        lambda v: setattr(cfg, "speed_factor", v),
        decimals=2,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["dead_zone"] = add_slider_row(
        core_layout,
        "dead_zone",
        "ic_target.svg",
        "中心死区缓冲 (Dead Zone)",
        cfg.dead_zone,
        0.0,
        100.0,
        lambda v: setattr(cfg, "dead_zone", v),
        decimals=1,
    )
    core_layout.addWidget(create_h_line())
    main_window.ui_widgets["overlay_size"] = add_slider_row(
        core_layout,
        "overlay_size",
        "ic_size.svg",
        "导航指示器大小 (UI Size)",
        cfg.overlay_size,
        30,
        150,
        lambda v: (
            setattr(cfg, "overlay_size", v),
            main_window.bridge.update_size.emit(int(v)),
            main_window.bridge.preview_size.emit(),
        ),
        decimals=0,
    )

    tab1_layout.addWidget(core_card)

    # --- Author Info ---
    author_layout = QHBoxLayout()
    author_layout.setAlignment(Qt.AlignCenter)

    main_window.btn_github = QPushButton()
    main_window.btn_github.setCursor(Qt.PointingHandCursor)
    main_window.btn_github.setObjectName("BtnIcon")

    # Load and set GitHub SVG Icon
    gh_path = resource_path(
        os.path.join("FlowScroll", "resources", "github_icon.svg")
    )
    if os.path.exists(gh_path):
        main_window.btn_github.setIcon(QIcon(gh_path))
        main_window.btn_github.setIconSize(QSize(20, 20))

    main_window.btn_github.setText(" GitHub · 某不科学的高数")
    import webbrowser
    main_window.btn_github.clicked.connect(
        lambda: webbrowser.open(getattr(main_window, 'github_url', "https://github.com/CyrilPeng/FlowScroll"))
    )

    author_layout.addWidget(main_window.btn_github)
    tab1_layout.addLayout(author_layout)

    return tab1_widget


def build_advanced_tab(main_window):
    tab2_widget = QWidget()
    tab2_layout = QVBoxLayout(tab2_widget)
    tab2_layout.setContentsMargins(0, 16, 0, 0)
    tab2_layout.setSpacing(20)
    tab2_layout.setAlignment(Qt.AlignTop)

    adv_card, adv_layout = create_card()

    # --- Horizontal Hotkey Row ---
    row_horizontal = QWidget()
    row_horizontal_layout = QHBoxLayout(row_horizontal)
    row_horizontal_layout.setContentsMargins(0, 0, 0, 0)
    row_horizontal_layout.setSpacing(12)

    chk_horizontal = QCheckBox("启用横向穿梭模式")
    chk_horizontal.setChecked(cfg.enable_horizontal)
    chk_horizontal.toggled.connect(lambda v: setattr(cfg, "enable_horizontal", v))
    chk_horizontal.setFocusPolicy(Qt.NoFocus)
    chk_horizontal.setCursor(Qt.PointingHandCursor)
    main_window.ui_widgets["enable_horizontal"] = chk_horizontal
    row_horizontal_layout.addWidget(chk_horizontal)
    row_horizontal_layout.addStretch()

    main_window.lbl_hotkey = QLabel()
    main_window.lbl_hotkey.setStyleSheet(
        "color: #94A3B8; font-size: 13px; font-weight: 600;"
    )
    main_window.update_hotkey_label()
    row_horizontal_layout.addWidget(main_window.lbl_hotkey)

    btn_gear = QPushButton()
    btn_gear.setObjectName("BtnIcon")
    btn_gear.setCursor(Qt.PointingHandCursor)
    btn_gear.setToolTip("设置快捷键")
    gear_path = resource_path(os.path.join("FlowScroll", "resources", "ic_gear.svg"))
    if os.path.exists(gear_path):
        btn_gear.setIcon(QIcon(gear_path))
        btn_gear.setIconSize(QSize(16, 16))
    else:
        btn_gear.setText("⚙️")
    btn_gear.clicked.connect(main_window.open_hotkey_dialog)
    row_horizontal_layout.addWidget(btn_gear)

    adv_layout.addWidget(row_horizontal)
    adv_layout.addWidget(create_h_line())
    main_window.ui_widgets["minimize_to_tray"] = add_toggle_row(
        adv_layout,
        "minimize_to_tray",
        "关闭后最小化到托盘",
        cfg.minimize_to_tray,
        lambda v: setattr(cfg, "minimize_to_tray", v),
    )
    adv_layout.addWidget(create_h_line())

    # Autorun (not stored in cfg, so key=None)
    add_toggle_row(
        adv_layout,
        None,
        "开机自动启动并在后台运行",
        main_window.autostart.is_autorun(),
        main_window.toggle_autorun,
    )
    adv_layout.addWidget(create_h_line())

    # Inline Advanced Rules
    main_window.ui_widgets["disable_fullscreen"] = add_toggle_row(
        adv_layout,
        "disable_fullscreen",
        "全屏模式下禁用",
        cfg.disable_fullscreen,
        lambda v: setattr(cfg, "disable_fullscreen", v),
        style_sheet="color: #FCA5A5;",
    )

    adv_layout.addWidget(create_h_line())

    adv_layout.addWidget(
        QLabel("<span style='font-weight: 600; color: #E2E8F0;'>工作模式</span>")
    )

    # Radio button group for filter modes
    main_window.filter_button_group = QButtonGroup(main_window)

    # Global mode radio button
    main_window.radio_global = QRadioButton("全局模式")
    main_window.radio_global.setStyleSheet(
        "color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px;"
    )
    main_window.radio_global.setChecked(cfg.filter_mode == 0)
    main_window.radio_global.setCursor(Qt.PointingHandCursor)
    main_window.filter_button_group.addButton(main_window.radio_global, 0)
    adv_layout.addWidget(main_window.radio_global)

    # Blacklist mode radio button
    main_window.radio_blacklist = QRadioButton("黑名单模式")
    main_window.radio_blacklist.setStyleSheet(
        "color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px;"
    )
    main_window.radio_blacklist.setChecked(cfg.filter_mode == 1)
    main_window.radio_blacklist.setCursor(Qt.PointingHandCursor)
    main_window.filter_button_group.addButton(main_window.radio_blacklist, 1)
    adv_layout.addWidget(main_window.radio_blacklist)

    # Connect radio buttons
    main_window.filter_button_group.idClicked.connect(main_window.on_filter_mode_changed)

    adv_layout.addWidget(
        QLabel(
            f"<span style='font-weight: 600; color: #E2E8F0;'>黑名单</span><br><span style='color: #94A3B8; font-size: 12px;'>例如输入 'potplayer' 就可以禁止在该播放器中使用，修改即时生效。<br><img src='{resource_path(os.path.join('FlowScroll', 'resources', 'ic_lightbulb.svg'))}' width='12' height='12'> <b>提示：</b>每行输入一个，不区分大小写，可通过任务管理器查看进程名进行精准设置。</span>"
        )
    )
    main_window.text_edit = QTextEdit()
    main_window.text_edit.setPlainText("\n".join(cfg.filter_list))
    main_window.text_edit.textChanged.connect(main_window.on_filter_list_changed)
    main_window.text_edit.setMaximumHeight(80)
    main_window.text_edit.setEnabled(cfg.filter_mode != 0)
    adv_layout.addWidget(main_window.text_edit)

    tab2_layout.addWidget(adv_card)

    # Section: 预设管理 (Presets)
    lbl_preset = QLabel("配置预设 Presets")
    lbl_preset.setObjectName("SectionTitle")
    tab2_layout.addWidget(lbl_preset)

    preset_card, preset_layout_card = create_card()

    preset_row = QHBoxLayout()
    preset_row.setSpacing(12)

    main_window.combo_presets = QComboBox()
    main_window.combo_presets.addItems(list(main_window.presets.keys()))
    main_window.combo_presets.setCurrentText(main_window.current_preset_name)
    main_window.combo_presets.currentTextChanged.connect(main_window.load_selected_preset)
    main_window.combo_presets.setFocusPolicy(Qt.NoFocus)
    main_window.combo_presets.setCursor(Qt.PointingHandCursor)
    main_window.combo_presets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    main_window.combo_presets.setFixedHeight(38)
    preset_row.addWidget(main_window.combo_presets, 1)

    btn_save = QPushButton("保存为新预设")
    btn_save.setObjectName("BtnPrimary")
    btn_save.setFocusPolicy(Qt.NoFocus)
    btn_save.setCursor(Qt.PointingHandCursor)
    btn_save.clicked.connect(main_window.save_new_preset)
    preset_row.addWidget(btn_save)

    btn_del = QPushButton("删除")
    btn_del.setObjectName("BtnDanger")
    btn_del.setFocusPolicy(Qt.NoFocus)
    btn_del.setCursor(Qt.PointingHandCursor)
    btn_del.clicked.connect(main_window.delete_preset)
    preset_row.addWidget(btn_del)

    preset_layout_card.addLayout(preset_row)

    preset_layout_card.addWidget(create_h_line())
    btn_webdav = QPushButton(" WebDAV 云同步配置")
    btn_webdav.setObjectName("BtnAdv")
    btn_webdav.setCursor(Qt.PointingHandCursor)
    cloud_path = resource_path(os.path.join("FlowScroll", "resources", "ic_cloud.svg"))
    if os.path.exists(cloud_path):
        btn_webdav.setIcon(QIcon(cloud_path))
        btn_webdav.setIconSize(QSize(18, 18))
    btn_webdav.clicked.connect(main_window.open_webdav_settings)
    preset_layout_card.addWidget(btn_webdav)

    tab2_layout.addWidget(preset_card)

    # Add stretch to make content fit height
    tab2_layout.addStretch()

    return tab2_widget
