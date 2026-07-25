# view.py

""" 

Network Cycle-oriented Relational Explorer and Visualizer (nCORE visualizer)

    Copyright (C) 2026  Tyler G. Southam


This program is free software: you can redistribute it and/or modify

it under the terms of the GNU General Public License as published by

the Free Software Foundation, either version 3 of the License, or

(at your option) any later version.


This program is distributed in the hope that it will be useful,

but WITHOUT ANY WARRANTY; without even the implied warranty of

MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the

GNU General Public License for more details.

 
You should have received a copy of the GNU General Public License

along with this program.  If not, see <https://www.gnu.org/licenses/>.

 
---- Contact: tyler.southam@utah.edu ----

"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Gdk, GObject, GLib
import graph_tool.all as gt
import cairo

class GraphView(Gtk.Window):
    """ Manages the GUI. GTK3 code goes here. """
    def __init__(self, controller):
        super().__init__(title="nCORE Visualizer")
        self.set_default_size(1080, 720)
        self.connect("destroy", Gtk.main_quit)
        self.current_filter_mode = "numeric"

        self.controller = controller

        # Main Layout
        hbox = Gtk.HBox(spacing=10)
        self.add(hbox)

        # Left column for controls - now using a notebook for tabs
        self.notebook = Gtk.Notebook()
        hbox.pack_start(self.notebook, False, False, 0)

        # Create File Operations tab
        file_tab = Gtk.VBox(spacing=10)
        file_tab.set_margin_left(10)
        file_tab.set_margin_right(10)
        file_tab.set_margin_top(10)
        file_tab.set_margin_bottom(10)

        # File type dropdown
        self.file_type_combo = Gtk.ComboBoxText()
        self.file_type_combo.append_text("FECD Cycles CSV")
        self.file_type_combo.append_text("Graph-tool binary")

        self.file_type_combo.set_tooltip_text("Select the type of file(s) to load")
        self.file_type_combo.set_active(0)
        file_tab.pack_start(self.file_type_combo, False, False, 0)
        
         # Apply existing graph postion toggable
        self.apply_existing_pos_check = Gtk.CheckButton(label="Apply existing graph position?")
        self.apply_existing_pos_check.set_active(False)
        self.apply_existing_pos_check.set_tooltip_text(
            "If enabled, the current active graph layout will be copied" \
            "to newly loaded graphs when vertex IDs match exactly.")
        file_tab.pack_start(self.apply_existing_pos_check, False, False, 0)
        
        # Open file button
        button_open = Gtk.Button(label="Load File(s)")
        button_open.connect("clicked", self.controller.on_open_files)
        file_tab.pack_start(button_open, False, False, 0)
 
        # Dropdown for loaded filenames
        self.file_dropdown = Gtk.ComboBoxText()
        self.file_dropdown.connect("changed", self.controller.on_file_selected)
        self.file_dropdown.set_tooltip_text("Select from loaded files to display")
        file_tab.pack_start(self.file_dropdown, False, False, 0)
        
        # Button HBox for Remove/Save
        btn_hbox = Gtk.HBox(spacing=10)
        file_tab.pack_start(btn_hbox, False, False, 0)
        
        button_remove = Gtk.Button(label="Remove")
        button_remove.set_tooltip_text("Remove the currently selected file from the view")
        button_remove.connect("clicked", self.controller.on_remove_file)
        btn_hbox.pack_start(button_remove, True, True, 0)
        
        button_save_gt = Gtk.Button(label="Save Graph (.gt)")
        button_save_gt.connect("clicked", self.controller.on_save_gt_file)
        button_save_gt.set_tooltip_text("Save the current graph in graph-tool's binary format for later reloading")
        btn_hbox.pack_start(button_save_gt, True, True, 0)
        
        # Save graph image controls
        self.filename_entry = Gtk.Entry(placeholder_text="graph.svg")
        file_tab.pack_start(self.filename_entry, False, False, 0)
        
        button_save_img = Gtk.Button(label="Save Graph View")
        button_save_img.connect("clicked", self.controller.on_save_image)
        button_save_img.set_tooltip_text("Save the current graph visualization as an image\n"
        "(SVG, PNG, PS, PDF currently supported)")
        file_tab.pack_start(button_save_img, False, False, 0)

        # Add File Operations tab to notebook
        self.notebook.append_page(file_tab, Gtk.Label(label="File Operations"))

        # Create Filtering tab
        filter_tab = Gtk.VBox(spacing=10)
        filter_tab.set_margin_left(10)
        filter_tab.set_margin_right(10)
        filter_tab.set_margin_top(10)
        filter_tab.set_margin_bottom(10)

        # Property List
        self.property_liststore = Gtk.ListStore(str)
        prop_treeview = Gtk.TreeView(model=self.property_liststore)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Properties", renderer, text=0)
        prop_treeview.append_column(column)
        self.property_selection = prop_treeview.get_selection()
        self.property_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.property_selection.connect("changed", self.controller.on_property_selected)
        
        prop_scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        prop_scroll.add(prop_treeview)
        filter_tab.pack_start(prop_scroll, True, True, 0)

        # Dynamic filter controls box
        self.filter_box = Gtk.VBox(spacing=5)
        filter_tab.pack_start(self.filter_box, False, False, 0)

        # Filter buttons
        filter_btn_hbox = Gtk.HBox(spacing=10)
        filter_tab.pack_start(filter_btn_hbox, False, False, 0)
        
        self.apply_filter_button = Gtk.Button(label="Add Filter")
        self.apply_filter_button.connect("clicked", self.controller.on_apply_filter)
        filter_btn_hbox.pack_start(self.apply_filter_button, True, True, 0)

        button_remove_filter = Gtk.Button(label="Remove Filter(s)")
        button_remove_filter.connect("clicked", self.controller.on_remove_filters)
        filter_btn_hbox.pack_start(button_remove_filter, True, True, 0)

        self.clear_all_filters_button = Gtk.Button(label="Clear All")
        self.clear_all_filters_button.connect("clicked", self.controller.on_clear_all_filters)
        filter_btn_hbox.pack_start(self.clear_all_filters_button, True, True, 0)

        # Conditional filtering buttons
        mode_box = Gtk.HBox(spacing=8)
        filter_tab.pack_start(mode_box, False, False, 0)

        mode_label = Gtk.Label(label="Combine:")
        mode_box.pack_start(mode_label, False, False, 0)

        self.operator_and_radio = Gtk.RadioButton.new_with_label_from_widget(None, "AND")
        self.operator_or_radio = Gtk.RadioButton.new_with_label_from_widget(self.operator_and_radio, "OR")
        self.operator_and_radio.set_active(True)

        mode_box.pack_start(self.operator_and_radio, False, False, 0)
        mode_box.pack_start(self.operator_or_radio, False, False, 0)

        self.not_check = Gtk.CheckButton(label="NOT")
        filter_tab.pack_start(self.not_check, False, False, 0)

        # Active filters list
        self.active_filters_liststore = Gtk.ListStore(str, str, str, str, int) # Logic, type, property name, value, index
        self.active_filters_treeview = Gtk.TreeView(model=self.active_filters_liststore)
        column_names = ["Logic", "Type", "Property", "Value", "ID"]
        
        for i, title in enumerate(column_names):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_resizable(True) #optional: allows users to resize columns
            self.active_filters_treeview.append_column(column)

        self.active_filters_treeview.set_headers_visible(True)
        self.active_filters_selection = self.active_filters_treeview.get_selection()
        self.active_filters_selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        active_filters_scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        active_filters_scroll.add(self.active_filters_treeview)
        filter_tab.pack_start(active_filters_scroll, True, True, 0)

        # Add Filtering tab to notebook
        self.notebook.append_page(filter_tab, Gtk.Label(label="Filtering"))

        # Create Display Tab
        display_tab = Gtk.VBox(spacing=10)
        display_tab.set_margin_left(10)
        display_tab.set_margin_right(10)
        display_tab.set_margin_top(10)
        display_tab.set_margin_bottom(10)

        # Hide isolated verts button
        self.hide_isolated_check = Gtk.CheckButton(label="Hide isolated vertices")
        self.hide_isolated_check.connect("toggled", self.controller.on_hide_isolated_toggled)
        display_tab.pack_start(self.hide_isolated_check, False, False, 0)
        
        # Cycle table columns
        """ To change either the static or dynamic cycle table layout, edit this list """

        self.cycle_table_columns = [
            {"title": "Path ID", "key": "path_ID"},
            {"title": "Direction", "key": "path_direction"},
            {"title": "Color", "key": "color"},
            {"title": "Flow", "key": "flow", "format": "float"},
            {"title": "Flux %", "key": "flux_pct", "format": "percent"}]
        
        self.dynamic_cycle_left_columns = [
            {"title": "Path ID", "key": "path_ID"},
            {"title": "Direction", "key": "path_direction"},
        ]
        self.dynamic_cycle_right_columns = [
            {"title": "Flux %", "key": "flux_pct", "format": "percent"},
        ]
        self.dynamic_cycle_column_options = []
        self.dynamic_cycle_selected_keys = ["color", "flow"]
        self.dynamic_cycle_column_combos = []
        self._updating_dynamic_column_combos = False

        # Storing for Recolor Code
        self.recolor_cycle_rows = []
        self.recolor_color_options = []
        self._updating_recolor_cycle_combo = False
        self._updating_recolor_color_combo = False

        summary_frame = Gtk.Frame(label="Cycle Flux Summary")
        summary_box = Gtk.VBox(spacing=4)
        summary_frame.add(summary_box)
        display_tab.pack_start(summary_frame, False, False, 0)

        self.cycle_summary_liststore, self.cycle_summary_tree = self._build_cycle_table(self.cycle_table_columns)

        cycle_scroll = Gtk.ScrolledWindow()
        cycle_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        cycle_scroll.set_min_content_height(200)
        cycle_scroll.add(self.cycle_summary_tree)
        summary_box.pack_start(cycle_scroll, False, False, 0)

        # Set up Dynamic Table
        dynamic_summary_frame = Gtk.Frame(label="Active Cycle Summary")
        dynamic_summary_box = Gtk.VBox(spacing=4)
        dynamic_summary_frame.add(dynamic_summary_box)
        display_tab.pack_start(dynamic_summary_frame, False, False, 0)
        dynamic_column_control_box = Gtk.HBox(spacing=6)
        dynamic_summary_box.pack_start(dynamic_column_control_box, False, False, 0)

        # Going Column by Column 
        dynamic_column_control_box.pack_start(Gtk.Label(label="Column 1:"), False, False, 0)
        dynamic_col_1_combo = Gtk.ComboBoxText()
        dynamic_col_1_combo.connect("changed", self.on_dynamic_cycle_column_combo_changed)
        dynamic_column_control_box.pack_start(dynamic_col_1_combo, True, True, 0)
        self.dynamic_cycle_column_combos.append(dynamic_col_1_combo)

        # You can clone below for more data columns
        dynamic_column_control_box.pack_start(Gtk.Label(label="Column 2:"), False, False, 0)
        dynamic_col_2_combo = Gtk.ComboBoxText()
        dynamic_col_2_combo.connect("changed", self.on_dynamic_cycle_column_combo_changed)
        dynamic_column_control_box.pack_start(dynamic_col_2_combo, True, True, 0)
        self.dynamic_cycle_column_combos.append(dynamic_col_2_combo)

        self.dynamic_summary_liststore, self.dynamic_cycle_tree = self._build_cycle_table(self._get_dynamic_cycle_table_columns())

        dynamic_cycle_scroll = Gtk.ScrolledWindow()
        dynamic_cycle_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        dynamic_cycle_scroll.set_min_content_height(200)
        dynamic_cycle_scroll.add(self.dynamic_cycle_tree)
        dynamic_summary_box.pack_start(dynamic_cycle_scroll, False, False, 0)

        # Recolor Cycle Controls
        recolor_frame = Gtk.Frame(label="Recolor Cycle")
        recolor_box = Gtk.VBox(spacing=6)
        recolor_frame.add(recolor_box)
        display_tab.pack_start(recolor_frame, False, False, 0)

        recolor_cycle_row = Gtk.HBox(spacing=6)
        recolor_box.pack_start(recolor_cycle_row, False, False, 0)

        recolor_cycle_row.pack_start(Gtk.Label(label="Path ID:"), False, False, 0)
        self.recolor_cycle_combo = Gtk.ComboBoxText()
        self.recolor_cycle_combo.connect("changed", self.on_recolor_cycle_combo_changed)
        recolor_cycle_row.pack_start(self.recolor_cycle_combo, True, True, 0)

        recolor_direction_row = Gtk.HBox(spacing=6)
        recolor_box.pack_start(recolor_direction_row, False, False, 0)

        recolor_direction_row.pack_start(Gtk.Label(label="Direction:"), False, False, 0)
        self.recolor_direction_combo = Gtk.ComboBoxText()
        recolor_direction_row.pack_start(self.recolor_direction_combo, True, True, 0)

        # The default Gtk.ComboBox popup can grow past the available screen
        # height. Using a controlled popover instead.
        self.recolor_color_active_index = 0

        recolor_color_row = Gtk.HBox(spacing=6)
        recolor_box.pack_start(recolor_color_row, False, False, 0)

        recolor_color_row.pack_start(Gtk.Label(label="Color:"), False, False, 0)

        self.recolor_color_button = Gtk.Button()
        self.recolor_color_button.set_size_request(180,-1)
        self.recolor_color_button_label = Gtk.Label(label="Select Color...")
        self.recolor_color_button_label.set_xalign(0.0)
        self.recolor_color_button.add(self.recolor_color_button_label)
        self.recolor_color_button.connect("clicked", self.on_recolor_color_button_clicked)
        recolor_color_row.pack_start(self.recolor_color_button, False, False, 0)

        self.recolor_color_popover = Gtk.Popover()
        self.recolor_color_popover.set_relative_to(self.recolor_color_button)
        self.recolor_color_popover.set_position(Gtk.PositionType.BOTTOM)

        self.recolor_color_scroll = Gtk.ScrolledWindow()
        self.recolor_color_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.recolor_color_scroll.set_size_request(220, 180)

        self.recolor_color_options_box = Gtk.VBox(spacing=0)
        self.recolor_color_scroll.add(self.recolor_color_options_box)
        self.recolor_color_popover.add(self.recolor_color_scroll)

        self._set_recolor_color_active_index(0)
        self.recolor_apply_button = Gtk.Button(label="Apply Recolor")
        self.recolor_apply_button.connect("clicked", self.controller.on_apply_cycle_recolor)
        recolor_box.pack_start(self.recolor_apply_button, False, False, 0)

        # Create legend within Display Page
        legend_frame = Gtk.Frame(label="Legend")
        legend_box = Gtk.VBox(spacing=6)
        legend_frame.add(legend_box)
        display_tab.pack_start(legend_frame, False, False, 0)
        legend_box.pack_start(self.make_legend_row("Solid", [], True), False, False, 0)
        legend_box.pack_start(self.make_legend_row("FLS", [2.5, 2.0], True), False, False, 0)
        legend_box.pack_start(self.make_legend_row("RLS", [0.5, 0.5], True), False, False, 0)
        legend_box.pack_start(self.make_legend_row("FLS + RLS", [0.5, 0.5, 1.5, 1.5], True), False, False, 0)

        # What actually creates the display tab
        self.notebook.append_page(display_tab, Gtk.Label(label="Display"))

        # Right side for the graph widget
        self.graph_area = Gtk.Box()
        hbox.pack_start(self.graph_area, True, True, 0)

        # --- Widgets for filter_box (created once, shown/hidden as needed)
        self.min_entry = Gtk.Entry()
        self.max_entry = Gtk.Entry()
        self.value_dropdown = Gtk.ComboBoxText()
        self.numeric_filter_widgets = [Gtk.Label(label="Min:"), self.min_entry, Gtk.Label(label="Max:"), self.max_entry]
        self.categorical_filter_widgets = [Gtk.Label(label="Select Value:"), self.value_dropdown]
        self.show_all()

    def _decorate_cycle_column_spec(self, column_spec):
        decorated_spec = dict(column_spec)

        if decorated_spec.get("key") == "color":
            decorated_spec["render"] = "color_swatch"
            decorated_spec["color_key"] = "color_hex"

        return decorated_spec

    def _build_cycle_table(self, column_specs):
        liststore = Gtk.ListStore(*([str] * len(column_specs)))
        tree = Gtk.TreeView(model=liststore)
        self._set_cycle_tree_columns(tree, column_specs)
        return liststore, tree

    def _set_cycle_tree_columns(self, tree, column_specs):
        for column in tree.get_columns():
            tree.remove_column(column)

        for i, raw_column_spec in enumerate(column_specs):
            column_spec = self._decorate_cycle_column_spec(raw_column_spec)
            renderer = Gtk.CellRendererText()
            if column_spec.get("render") == "color_swatch":
                column = Gtk.TreeViewColumn(column_spec["title"], renderer)
                column.set_cell_data_func(renderer, self._render_color_swatch_cell,i)
                column.set_fixed_width(80)
                column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            else:
                column = Gtk.TreeViewColumn(column_spec["title"], renderer, text=i)

            column.set_resizable(True)
            tree.append_column(column)
        tree.set_headers_visible(True)

    def _render_color_swatch_cell(self, tree_column, cell, tree_model, tree_iter, column_index):
        color_hex = tree_model[tree_iter][column_index]
        cell.set_property("text","")
        if color_hex:
            rgba = Gdk.RGBA()

            if rgba.parse(color_hex):
                cell.set_property("cell-background-rgba", rgba)
                cell.set_property("cell-background-set", True)
                return
        cell.set_property("cell-background-set", False)

    def _render_recolor_color_combo_swatch(self, combo, cell, tree_model, tree_iter, data):
        """ Render the color dropdown's first cell as a color swatch """
        color_hex = tree_model[tree_iter][1]

        if color_hex:
            rgba = Gdk.RGBA()

            if rgba.parse(color_hex):
                cell.set_property("text", "      ")
                cell.set_property("cell-background-rgba", rgba)
                cell.set_property("cell-background-set", True)
                return

        cell.set_property("text", "")
        cell.set_property("cell-background-set", False)

    def _make_recolor_color_markup(self, name="", color_hex=""):
        """Return markup for a color row/button label."""
        safe_name = GLib.markup_escape_text(str(name)) if name else "Select color..."

        if color_hex:
            rgba = Gdk.RGBA()
            if rgba.parse(str(color_hex)):
                safe_hex = GLib.markup_escape_text(str(color_hex))
                return f'<span foreground="{safe_hex}">&#9632;</span> {safe_name}'

        return safe_name

    def _set_recolor_color_active_index(self, active_index):
        """Set selected recolor color.

        Index convention:
        0 means no color selected.
        1..N map to self.recolor_color_options[index - 1].
        """

        self.recolor_color_active_index = active_index

        if active_index <= 0:
            self.recolor_color_button_label.set_text("Select Color...")
            return

        option_index = active_index - 1
        if option_index >= len(self.recolor_color_options):
            self.recolor_color_active_index = 0
            self.recolor_color_button_label.set_markup(
                self._make_recolor_color_markup()
            )
            return

        color_option = self.recolor_color_options[option_index]
        self.recolor_color_button_label.set_markup(
            self._make_recolor_color_markup(
                color_option.get("name", ""),
                color_option.get("hex", ""),
            )
        )

    def _add_recolor_color_popover_button(self, name, color_hex, active_index):
        """Add one clickable color row to the recolor color popover."""
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect("clicked", self.on_recolor_color_option_clicked, active_index)

        label = Gtk.Label()
        label.set_xalign(0.0)
        label.set_margin_left(6)
        label.set_margin_right(6)
        label.set_margin_top(3)
        label.set_margin_bottom(3)
        label.set_markup(self._make_recolor_color_markup(name, color_hex))

        button.add(label)
        self.recolor_color_options_box.pack_start(button, False, False, 0)

    def _rebuild_recolor_color_popover(self):
        """Rebuild the scrollable color list inside the popover."""
        for child in self.recolor_color_options_box.get_children():
            self.recolor_color_options_box.remove(child)

        self._add_recolor_color_popover_button("Select color...", "", 0)

        for active_index, color_option in enumerate(self.recolor_color_options, start=1):
            self._add_recolor_color_popover_button(
                color_option.get("name", ""),
                color_option.get("hex", ""),
                active_index,
            )

        self.recolor_color_options_box.show_all()

    def on_recolor_color_button_clicked(self, widget):
        """Show the controlled color popover."""
        self.recolor_color_popover.show_all()

        if hasattr(self.recolor_color_popover, "popup"):
            self.recolor_color_popover.popup()

    def on_recolor_color_option_clicked(self, widget, active_index):
        """Handle a color selection from the popover."""
        self._set_recolor_color_active_index(active_index)

        if hasattr(self.recolor_color_popover, "popdown"):
            self.recolor_color_popover.popdown()
        else:
            self.recolor_color_popover.hide()

    def _get_dynamic_cycle_table_columns(self):
        middle_columns = []

        for i, key in enumerate(self.dynamic_cycle_selected_keys):
            middle_columns.append(
                self._get_dynamic_column_spec_by_key(key, default_title=f"Column {i + 1}")
            )
        return (self.dynamic_cycle_left_columns + middle_columns + self.dynamic_cycle_right_columns)
    
    def _get_dynamic_column_spec_by_key(self, key, default_title="Column"):
        if not key:
            return {"title": default_title, "key": ""}
        for spec in self.dynamic_cycle_column_options:
            if spec.get("key") == key:
                return spec

        fallback_titles = { 
            "color": "Color",
            "flow": "Flow",
        }
        fallback_formats = {"flow": "float"}
        spec = { "title": fallback_titles.get(key,default_title), "key": key}
        if key in fallback_formats:
            spec["format"] = fallback_formats[key]
        return spec

    def _format_cycle_table_value(self, row, column_spec):
        column_spec = self._decorate_cycle_column_spec(column_spec)
        if column_spec.get("render") == "color_swatch":
            color_key = column_spec.get("color_key", "color_hex")
            return str(row.get(color_key,""))

        key = column_spec["key"]
        value = row.get(key, "")
        if value is None:
            return ""
        try:
            if value != value:
                return ""
        except Exception:
            pass

        format_type = column_spec.get("format")

        if format_type == "float":
            try:
                return f"{float(value):.6g}"
            except (TypeError, ValueError):
                return str(value)
        if format_type == "percent":
            try:
                return f"{100.0 * float(value):.2f}%"
            except (TypeError, ValueError):
                return str(value)
            
        return str(value)

    def _update_cycle_table(self, liststore, summary_rows, column_specs):
        liststore.clear()
        for row in summary_rows:
            display_values = [
                self._format_cycle_table_value(row, column_spec) for column_spec in column_specs]
            liststore.append(display_values)

    def _refresh_dynamic_cycle_table_columns(self):
        self._set_cycle_tree_columns(self.dynamic_cycle_tree, self._get_dynamic_cycle_table_columns())

    def update_recolor_color_options(self, color_options):
        """For populating Color Dropdown Menu"""

        self.recolor_color_options = color_options or []
        self._updating_recolor_color_combo = True

        self._rebuild_recolor_color_popover()
        self._set_recolor_color_active_index(0)

        self._updating_recolor_color_combo = False

    def update_recolor_cycle_options(self, summary_rows):
        "For populating paths for recolor feature"
        self.recolor_cycle_rows = summary_rows or []

        previous_path = self.recolor_cycle_combo.get_active_text()
        previous_direction = self.recolor_direction_combo.get_active_text()
        path_ids = []

        for row in self.recolor_cycle_rows:
            path_id = str(row.get("path_ID", ""))
            if path_id and path_id not in path_ids:
                path_ids.append(path_id)

        self._updating_recolor_cycle_combo = True
        self.recolor_cycle_combo.remove_all()
        self.recolor_cycle_combo.append_text("")

        for path_id in path_ids:
            self.recolor_cycle_combo.append_text(path_id)
        if previous_path in path_ids:
            self.recolor_cycle_combo.set_active(path_ids.index(previous_path)+ 1)
            self._populate_recolor_direction_options(previous_path, previous_direction)
        else:
            self.recolor_cycle_combo.set_active(0)
            self._populate_recolor_direction_options("","")

        self._updating_recolor_cycle_combo = False

    def _populate_recolor_direction_options(self, path_id, preferred_direction=""):
        """For populating directions for Recolor, based on currently selected path_id"""
        directions = []
        for row in self.recolor_cycle_rows:
            row_path_id = str(row.get("path_ID", ""))
            if row_path_id != str(path_id):
                continue
        
            direction = str(row.get("path_direction",""))
            if direction and direction not in directions:
                directions.append(direction)
        self.recolor_direction_combo.remove_all()
        self.recolor_direction_combo.append_text("")

        for direction in directions:
            self.recolor_direction_combo.append_text(direction)
        if preferred_direction in directions:
            self.recolor_direction_combo.set_active(directions.index(preferred_direction))
        else:
            self.recolor_direction_combo.set_active(0)
        self.recolor_direction_combo.set_sensitive(bool(directions))

    def on_recolor_cycle_combo_changed(self, widget):
        if self._updating_recolor_cycle_combo:
            return
        selected_path = self.recolor_cycle_combo.get_active_text()

        if not selected_path:
            self._populate_recolor_direction_options("","")
            return

        self._populate_recolor_direction_options(selected_path, "")

    def get_recolor_selection(self):
        """Return selected recolor inputs, None if user has not selected"""
        path_id = self.recolor_cycle_combo.get_active_text()
        path_direction = self.recolor_direction_combo.get_active_text()
        color_index = self.recolor_color_active_index

        if not path_id:
            return None
        if not path_direction:
            return None
        if color_index <= 0:
            return None

        option_index = color_index - 1
        if option_index >= len(self.recolor_color_options):
            return None

        color_option = self.recolor_color_options[option_index]

        return { 
            "path_ID": path_id,
            "path_direction": path_direction,
            "color_name": color_option.get("name",""),
            "color_hex": color_option.get("hex",""),
            "color_rgba": color_option.get("rgba", None),
        }

    def reset_recolor_controls(self):
        """"Clear Recolor Controls upon applying"""
        self.recolor_cycle_combo.set_active(0)
        self._populate_recolor_direction_options("","")
        self._set_recolor_color_active_index(0)

    def update_file_dropdown(self, filenames, active_index):
        self.file_dropdown.handler_block_by_func(self.controller.on_file_selected)
        self.file_dropdown.remove_all()
        for name in filenames:
            self.file_dropdown.append_text(name)
        self.file_dropdown.set_active(active_index)
        self.file_dropdown.handler_unblock_by_func(self.controller.on_file_selected)

    def update_property_list(self, properties):
        self.property_liststore.clear()
        for prop in properties:
            self.property_liststore.append([prop])
    
    def update_dynamic_cycle_column_options(self, column_options):
        self.dynamic_cycle_column_options = column_options or []

        option_keys = [spec.get("key", "") for spec in self.dynamic_cycle_column_options]
        previous_keys = list(self.dynamic_cycle_selected_keys)
        default_keys = ["color", "flow"]
        selected_keys = []

        for i, default_key in enumerate(default_keys):
            previous_key = previous_keys[i] if i < len(previous_keys) else ""

            if previous_key in option_keys:
                selected_keys.append(previous_key)
            elif default_key in option_keys:
                selected_keys.append(default_key)
            elif option_keys:
                selected_keys.append(option_keys[0])
            else:
                selected_keys.append("")
        self.dynamic_cycle_selected_keys = selected_keys
        self._updating_dynamic_column_combos = True

        for combo_index, combo in enumerate(self.dynamic_cycle_column_combos):
            combo.remove_all()

            for spec in self.dynamic_cycle_column_options:
                combo.append_text(spec.get("title", spec.get("key", "")))
            selected_key = self.dynamic_cycle_selected_keys[combo_index]
            if selected_key in option_keys:
                combo.set_active(option_keys.index(selected_key))
                combo.set_sensitive(True)
            else:
                combo.set_active(-1)
                combo.set_sensitive(False)

        self._updating_dynamic_column_combos = False
        self._refresh_dynamic_cycle_table_columns()

    def on_dynamic_cycle_column_combo_changed(self, widget):
        if self._updating_dynamic_column_combos:
            return
        try:
            combo_index = self.dynamic_cycle_column_combos.index(widget)
        except ValueError:
            return
        active_index = widget.get_active()
        if active_index < 0:
            return
        if active_index >= len(self.dynamic_cycle_column_options):
            return
        self.dynamic_cycle_selected_keys[combo_index] = self.dynamic_cycle_column_options[active_index]["key"]
        self._refresh_dynamic_cycle_table_columns()
        self.controller.on_dynamic_cycle_columns_changed()

    def update_cycle_summary(self, summary_rows):
        self._update_cycle_table(self.cycle_summary_liststore, summary_rows, self.cycle_table_columns)
        
    def update_dynamic_cycle_summary(self, summary_rows):
        self._update_cycle_table(self.dynamic_summary_liststore, summary_rows, self._get_dynamic_cycle_table_columns())
        self.update_recolor_cycle_options(summary_rows)

    def display_graph(self, widget):
        for child in self.graph_area.get_children():
            self.graph_area.remove(child)
        if widget:
            self.graph_area.pack_start(widget, True, True, 0)
            widget.show()
    
    def get_selected_property(self):
        model, tree_iter = self.property_selection.get_selected()
        if tree_iter:
            prop_string = model[tree_iter][0]
            prop_type, prop_name = prop_string.split(": ")
            return prop_type, prop_name
        return None, None
    
    def update_filter_controls(self, prop_map):
        # Clear old widgets
        for widget in self.filter_box.get_children():
            widget.hide()
            self.filter_box.remove(widget)

        if prop_map is None:
            return
        
        prop_type = prop_map.python_value_type()
        # Drop missing values before building filter controls.
        # Numeric missing values are NaN.
        # String missing values are stored as "".
        clean_values = []

        for value in list(prop_map):
            if value is None:
                continue

            # NaN is not equal to itself.
            try:
                if value != value:
                    continue
            except Exception:
                pass

            if isinstance(value, str) and value == "":
                continue

            clean_values.append(value)

        if prop_type in {int, float}:
            if not clean_values:
                return
            self.current_filter_mode = "numeric"
            numeric_values = [float(v) for v in clean_values]
            min_val, max_val = min(numeric_values), max(numeric_values)
            self.min_entry.set_text(str(min_val))
            self.max_entry.set_text(str(max_val))
            for widget in self.numeric_filter_widgets:
                self.filter_box.pack_start(widget, False, False, 0)
        else:
            self.current_filter_mode = "categorical"
            self.value_dropdown.remove_all()
            values = [str(v) for v in clean_values]
            try:
                values = sorted(set(values))
            except Exception:
                values = list(set(values))
            for val in values:
                self.value_dropdown.append_text(val)
            if values:
                self.value_dropdown.set_active(0)
            for widget in self.categorical_filter_widgets:
                self.filter_box.pack_start(widget, False, False, 0)
        self.filter_box.show_all()

    def get_filter_values(self):
        # Determine which controls are visible to get correct values
        operator = "OR" if self.operator_or_radio.get_active() else "AND"
        negated = self.not_check.get_active()
        if self.current_filter_mode == "numeric":
            return {"min_val": self.min_entry.get_text(), "max_val": self.max_entry.get_text(), "operator": operator, "negated": negated}
        return {"value": self.value_dropdown.get_active_text(), "operator": operator, "negated": negated}
    
    def draw_legend_sample(self, widget, ctx, dash_style, draw_arrow):
        alloc = widget.get_allocation()
        y = alloc.height / 2

        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(2)

        # Simple dash handling for legend display
        if dash_style:
            ctx.set_dash([8.0 * x for x in dash_style], 0.0)
        else:
            ctx.set_dash([], 0.0)

        ctx.move_to(10, y)
        ctx.line_to(100, y)
        ctx.stroke()

        if draw_arrow:
            # small arrowhead at the end
            ctx.set_dash([])
            ctx.move_to(100, y)
            ctx.line_to(92, y - 4)
            ctx.line_to(92, y + 4)
            ctx.close_path()
            ctx.fill()

    def make_legend_row(self, label, dash_style, draw_arrow=False):
        row = Gtk.HBox(spacing=8)
        area = Gtk.DrawingArea()
        area.set_size_request(160, 34)
        area.connect("draw", self.draw_legend_sample, dash_style, draw_arrow)
        row.pack_start(area, False, False, 0)
        row.pack_start(Gtk.Label(label=label), False, False, 0)
        return row 
