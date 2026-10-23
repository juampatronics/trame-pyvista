"""Anywidget container widget for client-side PyVista rendering.

This module exposes a self-contained :mod:`anywidget` frontend for the
trame/vtk.js ``OfflineLocalView`` viewer, so a PyVista scene can be
displayed inline in any Jupyter notebook (or other anywidget-compatible
environment) without keeping a trame server process alive.

The scene is serialized with the same vtk.js offline format used by
``plotter.trame.export_vtksz`` and rendered entirely in the browser by
the vendored viewer bundle (``trame_pyvista/static/viewer.js``, generated
from trame-vtk by ``scripts/refresh_viewer.py``).

Example
-------
::

    import pyvista as pv
    from trame_pyvista.anywidget import from_plotter

    pl = pv.Plotter()
    pl.add_mesh(pv.Sphere())
    from_plotter(pl)

The widget is also available as a plotter helper and as the
``anywidget`` Jupyter backend:

::

    pl.trame.to_anywidget()
    pl.show(backend='anywidget')
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

from anywidget import AnyWidget
import traitlets.traitlets as _t

if TYPE_CHECKING:
    from pyvista.plotting.plotter import BasePlotter

__all__ = [
    'PyVistaWidget',
    'from_plotter',
    'show_anywidget',
]

_STATIC_DIR = Path(__file__).resolve().parent / 'static'


def _build_esm() -> str:
    """Concatenate the widget module with the vendored viewer bundle.

    anywidget evaluates the ``_esm`` string as a single ES module, so
    relative imports would not resolve; both files must therefore form
    one self-contained module.
    """
    widget = (_STATIC_DIR / 'widget.js').read_text(encoding='utf-8')
    viewer = (_STATIC_DIR / 'viewer.js').read_text(encoding='utf-8')
    return f'{widget}\n{viewer}'


_ESM = _build_esm()


def _encode_scene(plotter: BasePlotter) -> str:
    """Serialize a plotter to a base64 vtk.js offline scene (zip)."""
    content = plotter.trame.export_vtksz(filename=None, format='zip')
    if not isinstance(content, (bytes, bytearray, memoryview)):  # pragma: no cover
        msg = f'Unexpected export_vtksz return type: {type(content)!r}'  # pragma: no cover
        raise TypeError(msg)  # pragma: no cover
    return base64.b64encode(bytes(content)).decode('ascii')


class PyVistaWidget(AnyWidget):  # type: ignore[valid-type]
    """Container widget rendering a PyVista scene with vtk.js.

    The scene payload is the base64 encoding of the zip produced by
    ``plotter.trame.export_vtksz``. The scene is created once and
    rendered entirely client-side; updating ``data`` with a newly
    exported scene replaces the displayed one.
    """

    _esm = _ESM

    #: Base64-encoded vtk.js offline scene (``export_vtksz`` zip).
    data = _t.Unicode('').tag(sync=True)  # type: ignore[valid-type,union-attr]
    #: Height of the render area in pixels.
    height = _t.Int(450).tag(sync=True)  # type: ignore[valid-type,union-attr]

    def __init__(
        self,
        plotter: BasePlotter | None = None,
        *,
        data: str | None = None,
        height: int = 450,
        **kwargs,
    ):
        """Create the widget, optionally from a PyVista plotter.

        Parameters
        ----------
        plotter : pyvista.Plotter, optional
            When given (and ``data`` is not), the plotter's scene is
            serialized with the vtk.js offline format and embedded.
        data : str, optional
            Base64-encoded scene payload. Overrides ``plotter``.
        height : int, optional
            Height of the render area in pixels (default 450).
        **kwargs
            Forwarded to the ipywidgets base class.
        """
        if plotter is not None and data is None:
            data = _encode_scene(plotter)
        super().__init__(data=data or '', height=height, **kwargs)


def from_plotter(
    plotter: BasePlotter,
    *,
    height: int = 450,
    **kwargs,
):  # numpydoc ignore=RT01
    """Create an :class:`PyVistaWidget` from a PyVista plotter.

    Parameters
    ----------
    plotter : pyvista.Plotter
        The plotter whose scene is serialized and rendered.
    height : int, optional
        Height of the render area in pixels (default 450).
    **kwargs
        Forwarded to :class:`PyVistaWidget`.

    Returns
    -------
    PyVistaWidget
        The widget instance; display it in Jupyter (e.g. the last
        expression of a cell).
    """
    return PyVistaWidget(plotter, height=height, **kwargs)


def show_anywidget(
    plotter: BasePlotter,
    screenshot: str | Path | None = None,
    **kwargs,
):  # numpydoc ignore=RT01
    """Display a plotter in Jupyter via the anywidget container.

    Registered under the name ``anywidget`` (see the
    ``pyvista.jupyter_backends`` entry points), so
    ``plotter.show(jupyter_backend='anywidget')`` works.

    The scene is rendered live in the browser, so the ``screenshot``
    argument that PyVista forwards to Jupyter backends is accepted but
    ignored.

    Parameters
    ----------
    plotter : pyvista.Plotter
        The plotter to display.
    screenshot : str | Path, optional
        Accepted for compatibility with PyVista's backend protocol and
        ignored, because the scene is rendered client-side.
    **kwargs
        Forwarded to :func:`from_plotter`.

    Returns
    -------
    PyVistaWidget
        The widget instance.
    """
    del screenshot  # rendered live; static image unused
    return from_plotter(plotter, **kwargs)
