import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pyvista as pv
    from trame_pyvista.anywidget import from_plotter

    return from_plotter, pv


@app.cell
def _(from_plotter, pv):
    pl = pv.Plotter()
    pl.add_mesh(pv.Sphere())
    from_plotter(pl, height=320)
    return


if __name__ == "__main__":
    app.run()
