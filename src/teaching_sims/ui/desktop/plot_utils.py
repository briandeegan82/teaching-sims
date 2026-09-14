"""Shared Dear PyGui plot helpers."""

from __future__ import annotations

import dearpygui.dearpygui as dpg


def fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


def fit_axes(*axis_tags: str) -> None:
    """Fit each plot axis to the series data currently bound to it."""
    for tag in axis_tags:
        if dpg.does_item_exist(tag):
            dpg.fit_axis_data(tag)
