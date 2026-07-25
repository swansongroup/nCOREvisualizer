# controller.py

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

from numpy import logical_or as np_logical_or
from gi.repository import Gtk
import graph_tool.all as gt
from numpy import logical_and as np_logical_and
from numpy import ones as np_ones

class GraphController:
    """ Connects the Model and the View. """
    def __init__(self, model):
        self.model = model
        self.view = None
        # The graph widgets are stored here, as they are GUI elements
        # but are tied to specific graph data from the model.
        self.graph_widgets = [] 
        self.previous_property_selection = None
        self.graph_ui_states = []
        self._restoring_graph_ui = False

    def set_view(self, view):
        self.view = view

    def on_open_files(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose file(s)", parent=self.view,
            action=Gtk.FileChooserAction.OPEN, select_multiple=True
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        # TODO: Add file filters... (In original code somewhere)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            file_format = self.view.file_type_combo.get_active_text()

            apply_existing_pos = self.view.apply_existing_pos_check.get_active()
            saved_layout = None
            saved_source_name = None 

            if apply_existing_pos and self.model.active_index != -1:
                source_g = self.model.get_current_graph(0)
                if source_g is not None:
                    saved_layout = self._pull_layout_from_graph(source_g)
                    saved_source_name = self.model.get_filenames_short()[self.model.active_index]

            newly_loaded_indices = self.model.load_files(filenames, file_format)
            
            # Create new GraphViews and widgets for newly loaded graphs
            # Pad out the GraphViews and graph_widgets lists to the length of the newly loaded indices
            while len(self.model.GraphViews) <= newly_loaded_indices[-1]:
                self.model.GraphViews.append(None)
            while len(self.graph_widgets) <= newly_loaded_indices[-1]:
                self.graph_widgets.append(None)
            while len(self.graph_ui_states) <= newly_loaded_indices[-1]:
                self.graph_ui_states.append(self._default_graph_ui_state())

            applied_count = 0

            for index in newly_loaded_indices:
                g = self.model.graphs[index]

                if saved_layout is not None:
                    if self._apply_layout_to_graph(g, saved_layout):
                        applied_count += 1

                gv = gt.GraphView(g, vfilt=g.vp['mask'], efilt=g.ep['mask'])
                self.model.GraphViews[index] = gv
                widget = self._create_graph_widget(gv)
                self.graph_widgets[index] = widget

            if saved_layout is not None:
                if applied_count > 0:
                    print(f"Successfully applied layout from '{saved_source_name}' to {applied_count} newly loaded graph(s).")
                else:
                    print("Copy layout was enabled but no matching Vertex set was found")
            self.view.apply_existing_pos_check.set_active(False)
            
            # Redraw all widgets to reflect potential global rescaling
            for w in self.graph_widgets:
                if w: 
                    w.regenerate_surface()

            self._sync_view_with_model()

        dialog.destroy()
    
    def on_file_selected(self, widget):
        index = widget.get_active()

        if index == self.model.active_index:
            return
        self._save_current_graph_ui_state()

        if not self.model.set_active_index(index):
            self._sync_view_with_model(clear_filter_box=True)
            return
        
        self._sync_view_with_model(clear_filter_box=True)

    def on_remove_file(self, widget):
        if self.model.active_index != -1:
            self.graph_widgets.pop(self.model.active_index)

            if self.model.active_index < len(self.graph_ui_states):
                self.graph_ui_states.pop(self.model.active_index)
        
        self.model.remove_active_file()
        self._sync_view_with_model(clear_filter_box=True)

    def on_save_gt_file(self, widget):
        if self.model.active_index == -1: return
        
        dialog = Gtk.FileChooserDialog(title="Save Graph (.gt)", parent=self.view, action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        short_name = self.model.get_filenames_short()[self.model.active_index]
        dialog.set_current_name(f"{short_name.rsplit('.', 1)[0]}.gt")

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.model.save_graph_to_gt(filename)
        dialog.destroy()

    def on_save_image(self, widget):
        filename = self.view.filename_entry.get_text()
        if not filename: return
        self.model.save_graph_to_image(filename)
    
    def on_property_selected(self, selection):
        # This logic prevents the signal from firing twice
        current_selection = selection.get_selected_rows()
        if self.previous_property_selection == current_selection:
            return
        self.previous_property_selection = current_selection

        prop_type, prop_name = self.view.get_selected_property()
        if not prop_name:
            self.view.update_filter_controls(None)
            return

        graph = self.model.get_current_graph()
        if graph:
            prop_map = graph.vp[prop_name] if prop_type == "Vertex" else graph.ep[prop_name]
            self.view.update_filter_controls(prop_map)

    def on_apply_filter(self, widget):
        prop_type, prop_name = self.view.get_selected_property()
        if not prop_name: return
        filter_vals = self.view.get_filter_values()
        filter_vals, mask_array, index = self.model.apply_filter(prop_type, prop_name, **filter_vals)
        logic_label = f"{filter_vals['operator']}{' NOT' if filter_vals['negated'] else ''}"
        self.view.active_filters_liststore.append([
            logic_label,
            prop_type,
            prop_name,
            str(filter_vals["value"]),
            index
        ])
        self._refresh_current_graph_after_state_change()

    def on_clear_all_filters(self, widget):
        self.model.clear_all_filters()
        self.view.active_filters_liststore.clear()
        self._refresh_current_graph_after_state_change()

    def on_dynamic_cycle_columns_changed(self):
        self._save_current_graph_ui_state()
        self.view.update_dynamic_cycle_summary(self.model.get_current_dynamic_cycle_summary())

    def _reset_filter_editor_controls(self):
        self.view.operator_and_radio.set_active(True)
        self.view.not_check.set_active(False)
        self.previous_property_selection = None

    def on_apply_cycle_recolor(self, widget):
        selection = self.view.get_recolor_selection()

        if selection is None:
            return
        changed = self.model.apply_cycle_recolor(
            selection["path_ID"],
            selection["path_direction"],
            selection["color_name"],
            selection["color_hex"],
            selection["color_rgba"],
        )
        if not changed: 
            return
        self.view.update_cycle_summary(self.model.get_current_cycle_summary())
        self._redraw_current_graph()
        self.view.reset_recolor_controls()
        
    def on_remove_filters(self, widget):
        # Get the filter ids 
        liststore, paths = self.view.active_filters_selection.get_selected_rows()
        if len(paths) == 0:
            print("No filters selected to remove")
            return
        #filter_ids = [path[-1] for path in paths] # original code, trying way below
        filter_ids = []
        for path in paths:
            tree_iter = liststore.get_iter(path)
            filter_id = liststore.get_value(tree_iter, 4)
            filter_ids.append(filter_id)

        # Remove filters from liststore
        for path in reversed(paths):
            # Get the GtkTreeIter for the current path
            iter = liststore.get_iter(path)
            liststore.remove(iter)

        # Remove filters from active filters list
        self.model.remove_filters(filter_ids)
        self._refresh_current_graph_after_state_change()

    def recalculate_all_filters(self):
        graph = self.model.get_current_graph(0)
        gv = self.model.get_current_graph(1)
        if not graph:
            return
        
        self._reset_graph_masks()

        filters = self.model.active_filters[self.model.active_index]
        if not filters:
            if gv:
                gv.set_filters(graph.ep["mask"], graph.vp["mask"])
            return

        # Build a lookup by stable filter ID
        filter_lookup = {f['index']: f for f in filters}

        vertex_result = None
        edge_result = None

        # Read rows in displayed order so row order matters
        # If nothing is selected, use the whole model order
        ordered_ids = [row[-1] for row in self.view.active_filters_liststore]

        if not ordered_ids:
            ordered_ids = [f["index"] for f in filters]

        for filt_id in ordered_ids:
            filt = filter_lookup.get(int(filt_id))
            if not filt:
                continue

            mask = filt['mask']
            if filt.get('negated', False):
                mask = ~mask

            operator = filt.get('operator', 'AND')

            if filt['type'] == 'Vertex':
                if vertex_result is None:
                    vertex_result = mask
                elif operator == 'OR':
                    vertex_result = np_logical_or(vertex_result, mask)
                else:
                    vertex_result = np_logical_and(vertex_result, mask)

            elif filt['type'] == 'Edge':
                if edge_result is None:
                    edge_result = mask
                elif operator == 'OR':
                    edge_result = np_logical_or(edge_result, mask)
                else:
                    edge_result = np_logical_and(edge_result, mask)

        if vertex_result is not None:
            graph.vp['mask'].set_values(vertex_result)
        else:
            graph.vp['mask'].a = True

        if edge_result is not None:
            graph.ep['mask'].set_values(edge_result)
        else:
            graph.ep['mask'].a = True

        gv = self.model.get_current_graph(1)
        if gv:
            gv.set_filters(graph.ep['mask'], graph.vp['mask'])

    # Private helper methods
    def _sync_view_with_model(self, clear_filter_box=False):
        """Updates the entire view based on the current model state."""
        
        if self.model.active_index == -1:
            self.view.display_graph(None)
            self.view.update_file_dropdown([], -1)
            self.view.update_property_list([])
            self.view.active_filters_liststore.clear()
            self.view.update_cycle_summary([])
            self.view.update_dynamic_cycle_summary([])
            self.view.update_filter_controls(None)
            return
        
        active_graph = self.model.get_current_graph(1)
        if active_graph and self.model.active_index < len(self.graph_widgets):
            active_widget = self.graph_widgets[self.model.active_index]
            self.view.display_graph(active_widget)
        else:
            self.view.display_graph(None)

        # first restore graph-specific GUI state
        self._restore_current_graph_ui_state()

        # then rebuild file/prop UI
        self.view.update_file_dropdown(
            self.model.get_filenames_short(),
            self.model.active_index
        )
        self.view.update_property_list(self.model.get_current_properties())

        # Then rebuild visible filters
        self._rebuild_active_filters_liststore_from_model()

        # Then dynamic table col choices
        self.view.update_dynamic_cycle_column_options(
            self.model.get_current_path_summary_columns()
        )

        # static display-side widgets
        self.view.update_recolor_color_options(self.model.get_cycle_color_options())
        self.view.update_cycle_summary(self.model.get_current_cycle_summary())

        # Recalc real mask, apply, redraw, update all from filtered graphview
        self._refresh_current_graph_after_state_change()

        if clear_filter_box:
            self._reset_filter_editor_controls()
            self.view.update_filter_controls(None)

    def _default_graph_ui_state(self):
        return {
            "hide_isolated": False,
            "dynamic_cycle_selected_indices": ["color", "flow"],
        }

    def _save_current_graph_ui_state(self):
        if self.view is None:
            return
        if self.model.active_index == -1:
            return
        if self.model.active_index >= len(self.graph_ui_states):
            return
        
        self.graph_ui_states[self.model.active_index] = {
            "hide_isolated": self.view.hide_isolated_check.get_active(),
        "dynamic_cycle_selected_keys": list(self.view.dynamic_cycle_selected_keys),
        }

    def _restore_current_graph_ui_state(self):
        if self.view is None:
            return
        if self.model.active_index == -1:
            return
        if self.model.active_index >= len(self.graph_ui_states):
            return
        
        state = self.graph_ui_states[self.model.active_index]

        self._restoring_graph_ui = True
        try:
            self.view.hide_isolated_check.set_active(bool(state.get("hide_isolated", False)))
            self.view.dynamic_cycle_selected_keys = list(state.get("dynamic_cycle_selected_keys", ["color", "flow"]))
        finally:
            self._restoring_graph_ui = False

    def _format_filter_value_for_row(self, filt):
        value = filt.get("value", "")

        if isinstance(value, list):
            if len(value) == 1:
                return str(value[0])
            return str(value)

        return str(value)

    def _rebuild_active_filters_liststore_from_model(self):
        self.view.active_filters_liststore.clear()

        if self.model.active_index == -1:
            return
        if self.model.active_index >= len(self.model.active_filters):
            return
        
        for filt in self.model.active_filters[self.model.active_index]:
            logic_label = ( f"{filt.get('operator', 'AND')}" f"{' NOT' if filt.get('negated', False) else ''}") # this

            self.view.active_filters_liststore.append([
                logic_label,
                filt.get("type", ""),
                filt.get("name", ""),
                self._format_filter_value_for_row(filt),
                int(filt.get("index", -1)),
            ])

    def _create_graph_widget(self, g):
        return gt.GraphWidget(g, pos=g.vp.pos,
                              vertex_shape="circle", vertex_color=[1, 1, 1, 0],
                              vertex_fill_color=[1, 1, 1, 0], vertex_size=g.vp.size,
                              vertex_surface=g.vp.vertex_sfcs, edge_color=g.ep.color,
                              edge_pen_width=g.ep.weight, edge_dash_style=g.ep.dash_style, edge_end_marker="arrow",
                              edge_marker_size=30)
    
    def _redraw_current_graph(self):
        if self.model.active_index != -1:
            widget = self.graph_widgets[self.model.active_index]
            widget.regenerate_surface()
            widget.queue_draw()
            self.view.display_graph(widget)
            self.view.update_dynamic_cycle_summary(self.model.get_current_dynamic_cycle_summary())

    def _pull_layout_from_graph(self, g):
        """Take (x,y) from graphs current pos"""
        if not g or "ids" not in g.vp or "pos" not in g.vp:
            return None
        
        layout = {}
        for v in g.vertices():
            node_id = str(g.vp["ids"][v])
            try: 
                pos = g.vp["pos"][v]
                layout[node_id] = (float(pos[0]), float(pos[1]))
            except Exception:
                return None
        return layout

    def _apply_layout_to_graph(self, g, layout):
        """Apply saved (x,y) to newly loaded graph"""
        if not g or not layout or "ids" not in g.vp:
            return False
        graph_ids = [str(g.vp["ids"][v]) for v in g.vertices()]
        if len(graph_ids) != len(layout):
            return False
        if set(graph_ids) != set(layout.keys()):
            return False
        
        new_pos = g.new_vp("vector<float>")
        for v in g.vertices():
            node_id = str(g.vp["ids"][v])
            new_pos[v] = layout[node_id]
        
        g.vp["init_pos"] = new_pos
        g.vp["pos"] = new_pos
        return True

    def _reset_graph_masks(self):
        graph = self.model.get_current_graph(0)
        if not graph:
            return
        graph.vp['mask'].set_values(np_ones(graph.num_vertices()))
        graph.ep['mask'].set_values(np_ones(graph.num_edges()))
        gv = self.model.get_current_graph(1)
        if gv:
            gv.set_filters(graph.ep['mask'], graph.vp['mask'])

    def _set_hide_isolated_silent(self, active):
        if self.view is None:
            return

        self._restoring_graph_ui = True
        try:
            self.view.hide_isolated_check.set_active(bool(active))
        finally:
            self._restoring_graph_ui = False

    def _refresh_current_graph_after_state_change(self):
        self.recalculate_all_filters()

        if self.view.hide_isolated_check.get_active():
            applied = self.apply_isolated_vertex_visibility()
            if not applied:
                print(
                    "Hide isolated vertices was not applied because it would "
                    "hide every visible node. Reverting checkbox to off"
                )
                self._set_hide_isolated_silent(False)

                graph = self.model.get_current_graph(0)
                gv = self.model.get_current_graph(1)
                if graph is not None and gv is not None:
                    gv.set_filters(graph.ep["mask"], graph.vp["mask"])
                
        self._redraw_current_graph()

    def on_hide_isolated_toggled(self, widget):
        if self._restoring_graph_ui:
            return

        self._refresh_current_graph_after_state_change()
        self._save_current_graph_ui_state()
    
    def apply_isolated_vertex_visibility(self):
        graph = self.model.get_current_graph(0)
        gv = self.model.get_current_graph(1)
        if graph is None or gv is None:
            return

        # If the box is off, just restore the normal real filters.
        if not self.view.hide_isolated_check.get_active():
            gv.set_filters(graph.ep["mask"], graph.vp["mask"])
            return True

        base_vertex_mask = graph.vp["mask"]
        base_edge_mask = graph.ep["mask"]

        # Start from the current real vertex mask, but do not overwrite it.
        display_vertex_mask = graph.new_vp("bool")
        display_vertex_mask.set_values(False)

        connected_vertices = graph.new_vp("bool")
        connected_vertices.set_values(False)

        for e in graph.edges():
            s = e.source()
            t = e.target()

            if base_edge_mask[e] and base_vertex_mask[s] and base_vertex_mask[t]:
                connected_vertices[s] = True
                connected_vertices[t] = True

        visible_vertex_count = 0

        for v in graph.vertices():
            keep = bool(base_vertex_mask[v]) and bool(connected_vertices[v])
            display_vertex_mask[v] = keep

            if keep:
                visible_vertex_count += 1

        if visible_vertex_count == 0:
            gv.set_filters(base_edge_mask, base_vertex_mask)
            return False

        # Apply only to the GraphView.
        gv.set_filters(base_edge_mask, display_vertex_mask)
        return True
