"""Display/RHI profile regression without a physical GPU or Qt installation.

The actual driver/scene graph is additionally exercised by quick_probe in CI.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from vitalux import renderer, settings


def run():
    saved_path = settings.PATH
    original_environ = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory(prefix="vitalux-display-") as temp:
            settings.PATH = str(Path(temp) / "settings.json")
            assert renderer.desired() == renderer.SOFTWARE
            assert renderer.graphics_api(renderer.WAYLAND_VULKAN) == 'vulkan'
            assert renderer.display_api(renderer.WAYLAND_VULKAN) == 'wayland'
            assert renderer.display_api(renderer.WAYLAND_OPENGL) == 'wayland'
            assert renderer.display_api(renderer.X11_OPENGL) == 'xcb'
            assert len(renderer.CHOICES) == 6
            assert len(set(renderer.CHOICES)) == 6
            assert renderer.DESCRIPTIONS[renderer.SOFTWARE].startswith('CPU')
            assert renderer.DESCRIPTIONS[renderer.QT_RASTER].startswith('Qt Raster')
            assert renderer.LEGACY_QTQUICK not in renderer.CHOICES
            settings.set('render_backend', renderer.LEGACY_QTQUICK)
            assert renderer.desired() == renderer.QT_RASTER
            assert settings.get('render_backend') == renderer.QT_RASTER
            assert renderer.prepare_start() == renderer.QT_RASTER
            assert not settings.get('gpu_boot_pending', False)
            settings.set('render_backend', renderer.SOFTWARE)
            for choice, platform, rhi in (
                 (renderer.WAYLAND_OPENGL, 'wayland', 'opengl'),
                (renderer.WAYLAND_VULKAN, 'wayland', 'vulkan'),
                (renderer.X11_OPENGL, 'xcb', 'opengl'),
            ):
                settings.set_many({'render_backend': choice, 'gpu_boot_pending': False})
                env = {'WAYLAND_DISPLAY': 'wayland-test', 'XDG_RUNTIME_DIR': temp,
                       'DISPLAY': ':42'}
                with patch.dict(os.environ, env, clear=True), \
                     patch.object(renderer, '_probe', return_value=(True, '')) as probe:
                    assert renderer.prepare_start() == choice
                    probe.assert_called_once()
                    if platform:
                        assert os.environ['QT_QPA_PLATFORM'] == platform
                    assert os.environ['QSG_RHI_BACKEND'] == rhi
                    assert settings.get('gpu_boot_pending') is True
                    renderer.successful_start()
                    assert settings.get('gpu_boot_pending') is False
                    renderer._restore_environment()
                # Reconfiguration in another process: no environment leak.
                assert not renderer._saved_environment

            settings.set_many({'render_backend': renderer.WAYLAND_VULKAN,
                               'gpu_boot_pending': False})
            with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-test',
                                         'XDG_RUNTIME_DIR': temp}, clear=True), \
                 patch.object(renderer, '_probe', return_value=(False, 'SIGABRT 134')):
                assert renderer.prepare_start() == renderer.SOFTWARE
                assert 'QT_QPA_PLATFORM' not in os.environ
                assert 'QSG_RHI_BACKEND' not in os.environ
                assert settings.get('render_backend') == renderer.SOFTWARE
                assert not settings.get('gpu_boot_pending')
                assert '134' in renderer.warning()

            # Explicit Wayland and X11 profiles must not crash when unavailable.
            for choice in (renderer.WAYLAND_OPENGL, renderer.WAYLAND_VULKAN,
                           renderer.X11_OPENGL):
                settings.set_many({'render_backend': choice, 'gpu_boot_pending': False})
                with patch.dict(os.environ, {}, clear=True):
                    assert renderer.prepare_start() == renderer.SOFTWARE
                    assert settings.get('render_backend') == renderer.SOFTWARE
                    assert not settings.get('gpu_boot_pending')

            settings.set_many({'render_backend': renderer.WAYLAND_VULKAN,
                               'gpu_boot_pending': True})
            with patch.dict(os.environ, {}, clear=True):
                assert renderer.prepare_start() == renderer.SOFTWARE
                assert settings.get('render_backend') == renderer.SOFTWARE
                assert not settings.get('gpu_boot_pending')

            # Forced software mode remains accessible even after a GPU crash.
            settings.set_many({'render_backend': renderer.WAYLAND_VULKAN,
                               'gpu_boot_pending': False})
            with patch.dict(os.environ, {'VITALUX_RENDERER': 'software'}, clear=True):
                assert renderer.prepare_start() == renderer.SOFTWARE
                assert renderer.desired() == renderer.SOFTWARE
            print("Renderer profiles, RHI/QPA selection and safe fallback: OK")
    finally:
        settings.PATH = saved_path
        os.environ.clear()
        os.environ.update(original_environ)


if __name__ == '__main__':
    run()
