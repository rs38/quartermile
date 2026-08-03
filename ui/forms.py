"""
ui/forms.py – ipywidgets form builder for car selection and parameter tweaking.
"""

import copy
import ipywidgets as widgets

_TIRE_COMPOUNDS = ["all_season", "summer", "track", "drag_radial"]


def make_car_form(slot_label: str, default_key: str, car_database: dict):
    """
    Build an ipywidgets form for one car slot.

    Parameters
    ----------
    slot_label : str
        Label shown next to the preset dropdown (e.g. ``"Car 1"``).
    default_key : str
        Key in *car_database* to select on load.
    car_database : dict
        The car preset dictionary (e.g. ``CAR_DATABASE`` from ``quarter_mile_cars``).

    Returns
    -------
    tuple[widgets.VBox, callable]
        ``(box_widget, get_spec_fn)`` where ``get_spec_fn()`` returns
        ``(name, spec_dict)`` reflecting the current widget values.
    """
    db_keys = list(car_database.keys())
    preset_dd = widgets.Dropdown(
        options=db_keys, value=default_key,
        description=f"{slot_label}:",
        style={"description_width": "50px"},
        layout=widgets.Layout(width="210px"),
    )
    pt_label = widgets.Label(layout=widgets.Layout(margin="2px 0 0 8px"))
    mass_txt = widgets.FloatText(
        description="Mass (kg):",
        style={"description_width": "80px"}, layout=widgets.Layout(width="220px"),
    )
    cmpd_dd = widgets.Dropdown(
        options=_TIRE_COMPOUNDS, description="Tire cmpd:",
        style={"description_width": "80px"}, layout=widgets.Layout(width="220px"),
    )
    tirw_sl = widgets.IntSlider(
        min=185, max=345, step=5, description="Width (mm):",
        style={"description_width": "80px"}, layout=widgets.Layout(width="310px"),
    )
    # ICE-only widgets
    lrpm_sl = widgets.IntSlider(
        min=500, max=4000, step=100, description="Launch RPM:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    srpm_sl = widgets.IntSlider(
        min=3000, max=8500, step=100, description="Shift RPM:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    stim_sl = widgets.FloatSlider(
        min=0.05, max=0.60, step=0.05, readout_format=".2f",
        description="Shift time s:",
        style={"description_width": "90px"}, layout=widgets.Layout(width="310px"),
    )
    ice_vbox = widgets.VBox([lrpm_sl, srpm_sl, stim_sl])

    def _populate(key: str) -> None:
        spec = car_database[key]
        pt = spec["powertrain"]
        pt_label.value = f"  {pt['type'].upper()} · {pt['driving_axles'].upper()}"
        mass_txt.value = spec["vehicle"]["mass"]
        cmpd_dd.value = spec["vehicle"]["tire"].get("compound", "summer")
        tirw_sl.value = spec["vehicle"]["tire"]["width_mm"]
        is_ice = pt["type"].upper() == "ICE"
        ice_vbox.layout.display = "" if is_ice else "none"
        if is_ice:
            gb = pt["gearbox"]
            m0 = pt.get("motors", [{}])[0]
            lrpm_sl.value = gb.get("launch_rpm", m0.get("min_rpm", 900))
            srpm_sl.value = gb.get("shift_rpm", m0.get("max_rpm", 7000))
            stim_sl.value = gb.get("shift_time_s", 0.30)

    _populate(default_key)
    preset_dd.observe(lambda ch: _populate(ch["new"]), names="value")

    def get_spec():
        key = preset_dd.value
        spec = copy.deepcopy(car_database[key])
        spec["vehicle"]["mass"] = mass_txt.value
        spec["vehicle"]["tire"]["compound"] = cmpd_dd.value
        spec["vehicle"]["tire"]["width_mm"] = tirw_sl.value
        if spec["powertrain"]["type"].upper() == "ICE":
            gb = spec["powertrain"]["gearbox"]
            gb["launch_rpm"] = lrpm_sl.value
            gb["shift_rpm"] = srpm_sl.value
            gb["shift_time_s"] = stim_sl.value
        return key, spec

    box = widgets.VBox(
        [widgets.HBox([preset_dd, pt_label]), mass_txt, cmpd_dd, tirw_sl, ice_vbox],
        layout=widgets.Layout(
            border="1px solid #ccc", padding="8px",
            margin="4px", min_width="340px",
        ),
    )
    return box, get_spec
