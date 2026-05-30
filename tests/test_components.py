"""UI 组件包专项测试。

测试 FlowScroll.ui.components 包中各子模块的导入与基础逻辑。
由于单元测试环境通常没有 QApplication，此处主要验证：
1. 模块导入路径正确
2. 类定义存在且继承关系正确
3. 纯逻辑方法（如 _parse_keywords 等）的行为
"""


class TestComponentsImport:
    """测试 components 包可通过 __init__.py 正确重导出所有组件类。"""

    def test_package_exports_hotkey_edit(self):
        from FlowScroll.ui.components import HotkeyEdit

        assert HotkeyEdit.__name__ == "HotkeyEdit"

    def test_package_exports_upward_combo_box(self):
        from FlowScroll.ui.components import UpwardComboBox

        assert UpwardComboBox.__name__ == "UpwardComboBox"

    def test_package_exports_no_wheel_slider(self):
        from FlowScroll.ui.components import NoWheelSlider

        assert NoWheelSlider.__name__ == "NoWheelSlider"

    def test_package_exports_no_wheel_spinbox(self):
        from FlowScroll.ui.components import NoWheelSpinBox

        assert NoWheelSpinBox.__name__ == "NoWheelSpinBox"

    def test_package_exports_speed_curve_widget(self):
        from FlowScroll.ui.components import SpeedCurveWidget

        assert SpeedCurveWidget.__name__ == "SpeedCurveWidget"


class TestComponentsInheritance:
    """验证各组件正确的继承链，确保它们来自对应的 Qt 基类。"""

    def test_hotkey_edit_inherits_qkey_sequence_edit(self):
        from PySide6.QtWidgets import QKeySequenceEdit
        from FlowScroll.ui.components import HotkeyEdit

        assert issubclass(HotkeyEdit, QKeySequenceEdit)

    def test_upward_combo_box_inherits_q_combo_box(self):
        from PySide6.QtWidgets import QComboBox
        from FlowScroll.ui.components import UpwardComboBox

        assert issubclass(UpwardComboBox, QComboBox)

    def test_no_wheel_slider_inherits_q_slider(self):
        from PySide6.QtWidgets import QSlider
        from FlowScroll.ui.components import NoWheelSlider

        assert issubclass(NoWheelSlider, QSlider)

    def test_no_wheel_spinbox_inherits_q_double_spinbox(self):
        from PySide6.QtWidgets import QDoubleSpinBox
        from FlowScroll.ui.components import NoWheelSpinBox

        assert issubclass(NoWheelSpinBox, QDoubleSpinBox)


class TestSpeedCurveWidgetConstants:
    """验证 SpeedCurveWidget 的静态常量与纯逻辑属性。"""

    def test_speed_curve_has_canvas_height_constant(self):
        from FlowScroll.ui.components import SpeedCurveWidget

        assert hasattr(SpeedCurveWidget, "CANVAS_HEIGHT")
        assert isinstance(SpeedCurveWidget.CANVAS_HEIGHT, (int, float))
        assert SpeedCurveWidget.CANVAS_HEIGHT > 0

    def test_speed_curve_has_max_distance_constant(self):
        from FlowScroll.ui.components import SpeedCurveWidget

        assert hasattr(SpeedCurveWidget, "MAX_DISTANCE")
        assert isinstance(SpeedCurveWidget.MAX_DISTANCE, (int, float))
        assert SpeedCurveWidget.MAX_DISTANCE > 0

    def test_speed_curve_has_sample_step_constant(self):
        from FlowScroll.ui.components import SpeedCurveWidget

        assert hasattr(SpeedCurveWidget, "SAMPLE_STEP")
        assert isinstance(SpeedCurveWidget.SAMPLE_STEP, (int, float))
        assert SpeedCurveWidget.SAMPLE_STEP > 0

    def test_speed_curve_sample_step_less_than_max_distance(self):
        from FlowScroll.ui.components import SpeedCurveWidget

        # 采样步长必须小于最大距离，否则无法绘制曲线
        assert SpeedCurveWidget.SAMPLE_STEP < SpeedCurveWidget.MAX_DISTANCE


class TestHotkeyEditMouseConstants:
    """验证 HotkeyEdit 的鼠标快捷键映射常量。"""

    def test_hotkey_edit_has_mouse_hotkeys_mapping(self):
        from FlowScroll.ui.components import HotkeyEdit

        assert hasattr(HotkeyEdit, "MOUSE_HOTKEYS")
        assert isinstance(HotkeyEdit.MOUSE_HOTKEYS, dict)
        assert len(HotkeyEdit.MOUSE_HOTKEYS) >= 2  # 至少支持 X1/X2

    def test_hotkey_edit_mouse_hotkeys_values_are_valid(self):
        from FlowScroll.ui.components import HotkeyEdit

        valid_values = {"mouse_x1", "mouse_x2", "mouse_middle"}
        for value in HotkeyEdit.MOUSE_HOTKEYS.values():
            assert value in valid_values, f"无效的鼠标快捷键标识: {value}"
