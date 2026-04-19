"""ScrollEngine 与 PowerCurveStrategy 的单元测试。"""

import math
import time
import threading
from collections import deque
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from FlowScroll.core.scroller import PowerCurveStrategy, default_scroll_strategy
from FlowScroll.core.config import STATE_LOCK, cfg, runtime, GlobalConfig
from FlowScroll.constants import (
    ENGINE_TICK_INTERVAL,
    ENGINE_IDLE_POLL_INTERVAL,
    INERTIA_STOP_THRESHOLD,
    SCROLL_HISTORY_WINDOW,
)


class TestPowerCurveStrategy:
    """测试 PowerCurveStrategy 的滚动速度计算：死区、方向、反转、对角线分配。"""

    def _make_config(self, **overrides):
        defaults = {
            "dead_zone": 20.0,
            "sensitivity": 2.0,
            "speed_factor": 2.0,
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_zero_displacement_inside_dead_zone(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=20.0)
        sx, sy = strategy.calculate_scroll_speed(0, 0, 0, config, 0.00005)
        assert sx == 0.0
        assert sy == 0.0

    def test_small_displacement_inside_dead_zone(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=20.0)
        sx, sy = strategy.calculate_scroll_speed(5, 5, 7.07, config, 0.00005)
        assert sx == 0.0
        assert sy == 0.0

    def test_displacement_exactly_at_dead_zone_boundary(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=20.0)
        sx, sy = strategy.calculate_scroll_speed(0, 20, 20.0, config, 0.00005)
        assert sx == 0.0
        assert sy == 0.0

    def test_downward_scroll_direction(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        sx, sy = strategy.calculate_scroll_speed(0, 50, 50, config, multiplier)
        assert sx == 0.0
        assert sy < 0

    def test_rightward_scroll_direction(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        sx, sy = strategy.calculate_scroll_speed(50, 0, 50, config, multiplier)
        assert sx > 0
        assert sy == 0.0

    def test_reverse_y(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        _, normal_sy = strategy.calculate_scroll_speed(0, 50, 50, config, multiplier)
        _, reversed_sy = strategy.calculate_scroll_speed(
            0, 50, 50, config, multiplier, reverse_y=True
        )
        assert reversed_sy == -normal_sy

    def test_reverse_x(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        normal_sx, _ = strategy.calculate_scroll_speed(50, 0, 50, config, multiplier)
        reversed_sx, _ = strategy.calculate_scroll_speed(
            50, 0, 50, config, multiplier, reverse_x=True
        )
        assert reversed_sx == -normal_sx

    def test_speed_scales_with_effective_distance(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=10.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        _, sy1 = strategy.calculate_scroll_speed(0, 20, 20, config, multiplier)
        _, sy2 = strategy.calculate_scroll_speed(0, 40, 40, config, multiplier)
        assert abs(sy2) > abs(sy1)

    def test_sensitivity_exponent(self):
        strategy = PowerCurveStrategy()
        config_linear = self._make_config(
            dead_zone=0.0, sensitivity=1.0, speed_factor=1.0
        )
        config_quad = self._make_config(
            dead_zone=0.0, sensitivity=2.0, speed_factor=1.0
        )
        multiplier = 1.0
        _, sy_lin = strategy.calculate_scroll_speed(
            0, 50, 50, config_linear, multiplier
        )
        _, sy_quad = strategy.calculate_scroll_speed(0, 50, 50, config_quad, multiplier)
        assert abs(sy_quad) > abs(sy_lin)

    def test_platform_multiplier_affects_speed(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        _, sy_small = strategy.calculate_scroll_speed(0, 50, 50, config, 0.00005)
        _, sy_large = strategy.calculate_scroll_speed(0, 50, 50, config, 0.0001)
        assert abs(sy_large) > abs(sy_small)

    def test_diagonal_scroll_distributes_proportionally(self):
        strategy = PowerCurveStrategy()
        config = self._make_config(dead_zone=0.0, sensitivity=1.0, speed_factor=1.0)
        multiplier = 1.0
        sx, sy = strategy.calculate_scroll_speed(50, 50, 70.71, config, multiplier)
        assert abs(sx) > 0
        assert abs(sy) > 0
        assert abs(sx - (-sy)) < 1e-10

    def test_default_strategy_is_power_curve(self):
        assert isinstance(default_scroll_strategy, PowerCurveStrategy)


class TestScrollEngineInertia:
    """测试 ScrollEngine 惯性逻辑：摩擦力计算、速度衰减、进入/中断条件。"""

    def _make_engine(self):
        from FlowScroll.core.engine import ScrollEngine

        bridge = MagicMock()
        mouse_ctrl = MagicMock()
        engine = ScrollEngine(bridge, mouse_ctrl)
        engine.inertia_active = False
        engine.inertia_vx = 0.0
        engine.inertia_vy = 0.0
        return engine

    def test_compute_friction_half_life(self):
        from FlowScroll.core.engine import ScrollEngine

        friction = ScrollEngine._compute_friction(500)
        assert 0.0 < friction < 1.0
        ticks = 500 / 4.0
        expected = math.pow(0.5, 1.0 / ticks)
        assert abs(friction - expected) < 1e-12

    def test_compute_friction_zero_half_life_fallback(self):
        from FlowScroll.core.engine import ScrollEngine

        friction = ScrollEngine._compute_friction(0)
        assert friction == 0.9

    def test_compute_friction_negative_half_life_fallback(self):
        from FlowScroll.core.engine import ScrollEngine

        friction = ScrollEngine._compute_friction(-100)
        assert friction == 0.9

    def test_interrupt_inertia_resets_state(self):
        engine = self._make_engine()
        engine.inertia_active = True
        engine.inertia_vx = 5.0
        engine.inertia_vy = 3.0

        engine.interrupt_inertia()

        assert engine.inertia_active is False
        assert engine.inertia_vx == 0.0
        assert engine.inertia_vy == 0.0

    def test_interrupt_inertia_clears_history(self):
        engine = self._make_engine()
        engine._scroll_history.append((time.monotonic(), 1.0, 2.0))
        engine._mouse_pos_history.append((time.monotonic(), 100, 200))

        engine.interrupt_inertia()

        assert len(engine._scroll_history) == 0
        assert len(engine._mouse_pos_history) == 0

    def test_interrupt_inertia_idempotent_when_not_active(self):
        engine = self._make_engine()
        engine.inertia_active = False
        engine.interrupt_inertia()
        assert engine.inertia_active is False

    def test_history_uses_deque(self):
        engine = self._make_engine()
        assert isinstance(engine._scroll_history, deque)
        assert isinstance(engine._mouse_pos_history, deque)

    def test_prune_history_removes_old_entries(self):
        engine = self._make_engine()
        now = time.monotonic()
        engine._scroll_history.append((now - 1.0, 1.0, 1.0))
        engine._scroll_history.append((now - 0.05, 2.0, 2.0))
        engine._scroll_history.append((now, 3.0, 3.0))

        engine._prune_history(engine._scroll_history, now)

        assert len(engine._scroll_history) == 2
        assert engine._scroll_history[0][1] == 2.0
        assert engine._scroll_history[1][1] == 3.0

    def test_get_max_speed_from_history_returns_max_vector(self):
        engine = self._make_engine()
        engine._scroll_history.append((time.monotonic(), 1.0, 0.0))
        engine._scroll_history.append((time.monotonic(), 0.0, 5.0))
        engine._scroll_history.append((time.monotonic(), 3.0, 4.0))

        vx, vy = engine._get_max_speed_from_history()

        speed_sq = vx * vx + vy * vy
        assert speed_sq == 25.0

    def test_get_max_speed_from_history_empty(self):
        engine = self._make_engine()
        vx, vy = engine._get_max_speed_from_history()
        assert vx == 0.0
        assert vy == 0.0

    def test_get_mouse_speed_px_per_s_basic(self):
        engine = self._make_engine()
        now = time.monotonic()
        engine._mouse_pos_history.append((now - 0.1, 0, 0))
        engine._mouse_pos_history.append((now, 100, 0))

        speed = engine._get_mouse_speed_px_per_s()

        assert abs(speed - 1000.0) < 1.0

    def test_get_mouse_speed_px_per_s_insufficient_samples(self):
        engine = self._make_engine()
        engine._mouse_pos_history.append((time.monotonic(), 0, 0))
        speed = engine._get_mouse_speed_px_per_s()
        assert speed == 0.0

    def test_try_enter_inertia_disabled(self):
        engine = self._make_engine()
        with STATE_LOCK:
            cfg.enable_inertia = False
        engine._scroll_history.append((time.monotonic(), 5.0, 5.0))
        engine._mouse_pos_history.append((time.monotonic(), 0, 0))
        engine._mouse_pos_history.append((time.monotonic(), 100, 100))

        engine._try_enter_inertia()

        assert engine.inertia_active is False

    def test_try_enter_inertia_mouse_speed_below_threshold(self):
        engine = self._make_engine()
        with STATE_LOCK:
            cfg.enable_inertia = True
            cfg.inertia_threshold = 1000.0
        now = time.monotonic()
        engine._scroll_history.append((now, 5.0, 5.0))
        engine._mouse_pos_history.append((now - 1.0, 0, 0))
        engine._mouse_pos_history.append((now, 10, 10))

        engine._try_enter_inertia()

        assert engine.inertia_active is False

    def test_try_enter_inertia_scroll_speed_too_low(self):
        engine = self._make_engine()
        with STATE_LOCK:
            cfg.enable_inertia = True
            cfg.inertia_threshold = 1.0
        now = time.monotonic()
        engine._scroll_history.append((now, 0.01, 0.01))
        engine._mouse_pos_history.append((now - 0.1, 0, 0))
        engine._mouse_pos_history.append((now, 1000, 0))

        engine._try_enter_inertia()

        assert engine.inertia_active is False

    def test_try_enter_inertia_success(self):
        engine = self._make_engine()
        with STATE_LOCK:
            cfg.enable_inertia = True
            cfg.inertia_threshold = 1.0
        now = time.monotonic()
        engine._scroll_history.append((now, 10.0, 20.0))
        engine._mouse_pos_history.append((now - 0.1, 0, 0))
        engine._mouse_pos_history.append((now, 1000, 0))

        engine._try_enter_inertia()

        assert engine.inertia_active is True
        assert engine.inertia_vx == 10.0
        assert engine.inertia_vy == 20.0

    def test_try_enter_inertia_clears_history_on_success(self):
        engine = self._make_engine()
        with STATE_LOCK:
            cfg.enable_inertia = True
            cfg.inertia_threshold = 1.0
        now = time.monotonic()
        engine._scroll_history.append((now, 10.0, 20.0))
        engine._mouse_pos_history.append((now - 0.1, 0, 0))
        engine._mouse_pos_history.append((now, 1000, 0))

        engine._try_enter_inertia()

        assert len(engine._scroll_history) == 0
        assert len(engine._mouse_pos_history) == 0

    def test_history_lock_prevents_concurrent_clear_and_append(self):
        engine = self._make_engine()
        engine._scroll_history.append((time.monotonic(), 1.0, 1.0))

        append_done = threading.Event()
        clear_done = threading.Event()
        errors = []

        def append_loop():
            try:
                for _ in range(200):
                    with engine._history_lock:
                        engine._scroll_history.append((time.monotonic(), 1.0, 1.0))
            except Exception as e:
                errors.append(e)
            finally:
                append_done.set()

        def clear_loop():
            try:
                for _ in range(50):
                    engine.interrupt_inertia()
            except Exception as e:
                errors.append(e)
            finally:
                clear_done.set()

        t1 = threading.Thread(target=append_loop)
        t2 = threading.Thread(target=clear_loop)
        t1.start()
        t2.start()
        append_done.wait(timeout=5)
        clear_done.wait(timeout=5)

        assert errors == []

    def test_update_friction(self):
        from FlowScroll.core.engine import ScrollEngine

        engine = self._make_engine()
        with STATE_LOCK:
            cfg.inertia_friction_ms = 1000
        engine.update_friction()
        expected = ScrollEngine._compute_friction(1000)
        assert abs(engine.friction - expected) < 1e-12


class TestScrollEngineIntegration:
    """测试 ScrollEngine 的线程属性与端到端滚动流程。"""

    def test_engine_starts_as_daemon_thread(self):
        from FlowScroll.core.engine import ScrollEngine

        bridge = MagicMock()
        mouse_ctrl = MagicMock()
        engine = ScrollEngine(bridge, mouse_ctrl)
        assert engine.daemon is True

    def test_engine_has_history_lock(self):
        from FlowScroll.core.engine import ScrollEngine

        bridge = MagicMock()
        mouse_ctrl = MagicMock()
        engine = ScrollEngine(bridge, mouse_ctrl)
        assert hasattr(engine, "_history_lock")
        assert isinstance(engine._history_lock, type(threading.Lock()))

    def test_active_mode_error_sleeps_before_retry(self, monkeypatch):
        from FlowScroll.core.engine import ScrollEngine

        bridge = MagicMock()
        mouse_ctrl = MagicMock()
        type(mouse_ctrl).position = property(
            lambda _self: (_ for _ in ()).throw(RuntimeError("mouse failed"))
        )
        engine = ScrollEngine(bridge, mouse_ctrl)
        engine._snapshot_config = lambda: (
            True,
            (0, 0),
            False,
            0.0,
            1.0,
            1.0,
            False,
            False,
        )

        sleep_calls = []

        def fake_sleep(interval):
            sleep_calls.append(interval)
            raise StopIteration()

        monkeypatch.setattr(time, "sleep", fake_sleep)

        with pytest.raises(StopIteration):
            engine.run()

        assert sleep_calls == [ENGINE_IDLE_POLL_INTERVAL]
