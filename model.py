# model.py


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

import json
import pandas as pd
import cairo
import cycle_layout as cl
import graph_tool.all as gt
import numpy as np
from numpy import log as ln
from numpy import power as np_power
from numpy import isin as np_isin
from numpy import ones as np_ones

colormap_rgba_norm = [
    (243/255, 195/255, 0/255,   1.0),  # Golden Yellow
    (135/255, 86/255,  146/255, 1.0),  # Purple
    (243/255, 132/255, 0/255,   1.0),  # Orange
    (161/255, 202/255, 241/255, 1.0),  # Light Sky Blue
    (190/255, 0/255,   50/255,  1.0),  # Crimson Red
    (194/255, 178/255, 128/255, 1.0),  # Sand
    (132/255, 132/255, 130/255, 1.0),  # Gray
    (0/255,   136/255, 86/255,  1.0),  # Forest Green
    (230/255, 143/255, 172/255, 1.0),  # Dusty Pink
    (0/255,   103/255, 165/255, 1.0),  # Royal Blue
    (249/255, 147/255, 121/255, 1.0),  # Salmon
    (101/255, 69/255,  34/255,  1.0),  # Dark Brown
    (246/255, 166/255, 0/255,   1.0),  # Amber
    (179/255, 68/255,  108/255, 1.0),  # Raspberry
    (220/255, 211/255, 0/255,   1.0),  # Chartreuse
    (136/255, 45/255,  23/255,  1.0),  # Brick Red
    (141/255, 182/255, 0/255,   1.0),  # Lime Green
    (96/255,  78/255,  151/255, 1.0),  # Slate Purple
    (226/255, 88/255,  34/255,  1.0),  # Burnt Orange
    (43/255,  61/255,  38/255,  1.0)]  # Dark Forest Green

# Consider removing Dark Forest Green from all three lists
# as it's very close to black and could be distracting

colormap_names = [
    "Golden Yellow", "Purple", "Orange", "Light Sky Blue", "Crimson Red",
    "Sand", "Gray", "Forest Green", "Dusty Pink", "Royal Blue",
    "Salmon", "Dark Brown", "Amber", "Raspberry", "Chartreuse",
    "Brick Red", "Lime Green", "Slate Purple", "Burnt Orange", "Dark Forest Green"]

colormap_hex = [
    "#F3C300", "#875692", "#F38400", "#A1CAF1", "#BE0032",
    "#C2B280", "#848482", "#008856", "#E68FAC", "#0067A5",
    "#F99379", "#654522", "#F6A600", "#B3446C", "#DCD300",
    "#882D17", "#8DB600", "#604E97", "#E25822", "#2B3D26"]

class GraphModel:
    """ Manages all application data and core logic. No GUI code. """

    Data_Payload = "Data_Payload"
    Data_Payload_Version = 1

    def __init__(self):
        self.filenames = []
        self.graphs = []
        self.all_properties = []
        self.active_index = -1
        self.active_filters = []
        self.cycle_summaries = []
        self.cycle_summary_column_options = []
        self.GraphViews = [] #TODO: create graphview objects when loading files, then use the native set filter methods to set and change filters
        #TODO: change the graph widget to use the graphview object instead of the graph object
        #TODO: change how the graph view is updated back to how it was before the graphview object was introduced
        self.Default_Direction_Property = "path_direction" 
        self.Default_Direction_Value = "F"

    def _ensure_filter_masks(self, graph):
        """Ensure graph has bool mask controller expects"""
        
        if graph is None:
            return

        if "mask" not in graph.vp:
            graph.vp["mask"] = graph.new_vp("bool")
            graph.vp["mask"].set_values(np_ones(graph.num_vertices()))
        
        if "mask" not in graph.ep:
            graph.ep["mask"] = graph.new_vp("bool")
            graph.ep["mask"].set_values(np_ones(graph.num_edges()))

    def _next_filter_index_for_graph(self, graph_index):
        """Return next stable filter ID for one graph"""
        return int(
            max(
                (
                    filt.get("index", -1)
                    for filt in self.active_filters[graph_index]
                ),
                default=-1,
            )
            + 1
        )

    def _edge_property_as_string_array(self, graph, prop_name):
        """Return one edge prop as stripped str num array"""
        
        prop_map = graph.ep[prop_name]

        if prop_map.python_value_type() == str:
            values = prop_map.get_2d_array([0], dtype=str).flatten()
        else:
            values = [prop_map[e] for e in graph.edges()]
        
        return np.array([str(value).strip() for value in values], dtype=str)

    def _seed_default_direction_filter(self, graph_index, direction=None):
        """Preapplying direction == F before load so it populates on inital load"""
        direction = (
            self.Default_Direction_Value
            if direction is None
            else  str(direction).strip()
        )

        if not direction:
            return False
        if graph_index < 0:
            return False
        if graph_index >= len(self.graphs):
            return False
        if graph_index >= len(self.active_filters):
            return False
        
        graph = self.graphs[graph_index]
        self._ensure_filter_masks(graph)

        prop_name = self.Default_Direction_Property

        if prop_name not in graph.ep:
            return False
        edge_values = self._edge_property_as_string_array(graph, prop_name)
        mask_array = np_isin(edge_values, [direction])

        if not mask_array.any():
            print(
                f"Default direction filter was not added because no "
                f"{prop_name} == {direction!r} edges were found."
            )
            return False

        for filt in self.active_filters[graph_index]:
            if (
                filt.get("type") == "Edge"
                and filt.get("name") == prop_name
                and filt.get("value") == [direction]
                and filt.get("default_on_load", False)
            ):
                graph.vp["mask"].set_values(np_ones(graph.num_vertices()))
                graph.ep["mask"].set_values(mask_array)
                return False

        stored_filter = {
            "operator": "AND",
            "negated": False,
            "type": "Edge",
            "name": prop_name,
            "value": [direction],
            "mask": mask_array,
            "index": self._next_filter_index_for_graph(graph_index),
            "default_on_load": True,            
        }    

        self.active_filters[graph_index].append(stored_filter)
        graph.vp["mask"].set_values(np_ones(graph.num_vertices()))
        graph.ep["mask"].set_values(mask_array)

        return True

    def get_current_graph(self, mode=0):

        """
        mode 0: return the graph object
        mode 1: return the graphView object (if available)
        """

        if self.active_index == -1:
            return None

        match mode:
            case 0:
                return self.graphs[self.active_index]
            case 1:
                return self.GraphViews[self.active_index]
            case _:
                print(f"Invalid mode: {mode}")
                print(f"Please use 0 for graph object or 1 for GraphView object")
                return None
            
    def get_current_properties(self):
        if self.active_index != -1:
            return self.all_properties[self.active_index]
        return []

    def get_filenames_short(self):
        return [fn.replace('\\', '/').split('/')[-1] for fn in self.filenames]

    def get_current_cycle_summary(self):
        if self.active_index == -1:
            return []
        if self.active_index >= len(self.cycle_summaries):
            return []
        return self.cycle_summaries[self.active_index]

    def get_current_path_summary_columns(self):
        """ Pulls Path level <attr> to use for dynamic data table"""
        if self.active_index == -1:
            return []
        if self.active_index >= len(self.cycle_summary_column_options):
            return []
        return self.cycle_summary_column_options[self.active_index]
        
    def get_cycle_color_options(self):
        """Zip Color Options Together, Edges driven by RGBA, hex for View Side"""
        color_options = []

        for name, hex_value, rgba in zip(colormap_names, colormap_hex, colormap_rgba_norm):
            color_options.append({"name": str(name), "hex": str(hex_value), "rgba": tuple(rgba)})
        return color_options

    def get_current_dynamic_cycle_summary(self):
        if self.active_index == -1:
            return []
        if self.active_index >= len(self.cycle_summaries):
            return []
        
        g = self.get_current_graph(0)
        gv = self.get_current_graph(1)
        summary_rows = self.get_current_cycle_summary()

        if g is None or gv is None:
            return []
        if not summary_rows:
            return []
        
        # Dynamic cycle summaries only work when g has path_ID
        if "path_ID" not in g.ep:
            return []
                
        has_direction = "path_direction" in g.ep
        visible_groups = set()

        for edge in gv.edges():
            path_id = str(g.ep["path_ID"][edge])
            direction = str(g.ep["path_direction"][edge]) if has_direction else ""
            visible_groups.add((path_id, direction))

        dynamic_rows = []

        for row in summary_rows:
            path_id = str(row.get("path_ID", ""))
            direction = str(row.get("path_direction", "")) if has_direction else ""

            if (path_id, direction) in visible_groups:
                dynamic_rows.append(row)
        return dynamic_rows

    def _build_cycle_summary_column_options(self, cycle_summary):
        """Building choices for dropdowns in dynamic table"""
        if not cycle_summary:
            return []
        excluded_keys = { 
            "path_ID", "path_direction", "flux_pct", "Flow", "Color_hex",
        }
        keys = []
        for row in cycle_summary:
            for key in row.keys():
                if key in excluded_keys:
                    continue
                if key not in keys:
                    keys.append(key)
        preferred_order = [
            "color", "flow", "cycle_number", "FLS", "FLS_source",
            "FLS_target", "RLS", "RLS_source", "RLS_target",
        ]
        ordered_keys = []

        for key in preferred_order:
            if key in keys:
                ordered_keys.append(key)
        for key in keys:
            if key not in ordered_keys:
                ordered_keys.append(key)
        return [ self._make_cycle_summary_column_spec(key) for key in ordered_keys]

    def _make_cycle_summary_column_spec(self, key):
        title_overrides = {
            "path_ID": "Path ID",
            "path_direction": "Direction",
            "color": "Color",
            "flow": "Flow",
            "flux_pct": "Flux %",
            "cycle_number": "Cycle Number",
            "FLS": "FLS",
            "FLS_source": "FLS Source",
            "FLS_target": "FLS Target",
            "RLS": "RLS",
            "RLS_source": "RLS Source",
            "RLS_target": "RLS Target",
            }
        format_overrides = { 
            "flow": "float",
            "Flow": "float",
            "flux_pct": "percent",
        }
        spec = { "title": title_overrides.get(key, key.replace("_"," ").title()),
                "key": key,
                }
        if key in format_overrides:
            spec["format"] = format_overrides[key]
        return spec
    
    def _clean_cycle_summary_value(self, value):
        try: 
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        return value

    def _json_safe_value(self, value):
        """Convert pandas/numpy values into plain JSON-safe Python values.
        This keeps the .gt payload robust without changing the table model."""

        if isinstance(value, dict):
            return {
                str(k): self._json_safe_value(v)
                for k, v in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [self._json_safe_value(v) for v in value]

        if isinstance(value, np.ndarray):
            return [self._json_safe_value(v) for v in value.tolist()]

        if isinstance(value, np.generic):
            value = value.item()

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        try:
            json.dumps(value, allow_nan=False)
            return value
        except (TypeError, ValueError):
            return str(value)

    def _build_app_payload(self, graph_index):
        """Build the graph-level payload stored inside .gt files."""

        cycle_summary = []
        if 0 <= graph_index < len(self.cycle_summaries):
            cycle_summary = self.cycle_summaries[graph_index]

        return {
            "payload_version": self.Data_Payload_Version,
            "cycle_summary": self._json_safe_value(cycle_summary)}

    def _attach_app_payload_to_graph(self, graph_to_save, graph_index):
        """Attach the graph-level table payload to a graph-level property map."""

        payload = self._build_app_payload(graph_index)
        payload_json = json.dumps(payload, allow_nan=False)

        graph_to_save.gp[self.Data_Payload] = graph_to_save.new_gp(
            "string",
            val=payload_json)

    def _restore_cycle_summary_from_app_payload(self, graph):
        """Return cycle_summary restored from a .gt graph payload if present."""
        if graph is None:
            return []

        if self.Data_Payload not in graph.gp:
            return []

        try:
            payload_json = graph.gp[self.Data_Payload]
            payload = json.loads(payload_json)
        except Exception as exc:
            print(f"Warning: could not read app payload from .gt file: {exc}")
            return []

        version = payload.get("payload_version")
        if version != self.Data_Payload_Version:
            print(
                f"Warning: app payload version {version!r} found; "
                f"expected {self.APP_PAYLOAD_VERSION!r}. "
                "Attempting to load compatible fields."
            )

        cycle_summary = payload.get("cycle_summary", [])
        if not isinstance(cycle_summary, list):
            print("Warning: app payload cycle_summary is not a list.")
            return []

        clean_rows = []
        for row in cycle_summary:
            if isinstance(row, dict):
                clean_rows.append(row)
            else:
                print(f"Warning: skipping malformed cycle_summary row: {row!r}")

        return clean_rows

    def set_active_index(self, index):
        if 0 <= index < len(self.graphs):
            self.active_index = index
            return True
        self.active_index = -1
        return False

    def remove_active_file(self):
        if self.active_index == -1:
            return None
        
        self.all_properties.pop(self.active_index)
        self.GraphViews.pop(self.active_index)
        self.graphs.pop(self.active_index)
        self.active_filters.pop(self.active_index)
        self.cycle_summaries.pop(self.active_index)
        self.cycle_summary_column_options.pop(self.active_index)
        removed_filename = self.filenames.pop(self.active_index)

        # Reset active index if list is not empty
        self.active_index = 0 if self.filenames else -1
        return removed_filename

    def load_files(self, filenames, file_format):
        """Processes a list of files based on the selected format."""

        newly_loaded_indices = []
        for file in filenames:
            self.filenames.append(file)
            current_idx = len(self.filenames) - 1
            self.active_filters.append([])
            g = None
            cycle_summary = []

            if file_format == "FECD Cycles CSV":
                g, cycle_summary = self._load_graph_from_cycle_table_csv(file)
            elif file_format == "Graph-tool binary":
                g = gt.load_graph(file)
                self._restore_graph_properties(g)
                cycle_summary = self._restore_cycle_summary_from_app_payload(g)
            else:
                raise ValueError("File Type is not accepted")
            if g is not None:
                self.cycle_summaries.append(cycle_summary)
                self.cycle_summary_column_options.append(self._build_cycle_summary_column_options(cycle_summary))
                self.graphs.append(g)

                self._seed_default_direction_filter(current_idx, direction="F")

                # Trimming Filter Tree Below
                hidden_vertex_props = {"mask", "size", "init_pos", "pos", "vertex_images", "vertex_sfcs"}
                hidden_edge_props = {"mask", "weight", "dash_style", "color", "k_fwd", "k_rev", "k_int", "F_net",
                                    "F_fwd", "F_rev", "is_fls", "is_rls", "cycle_number", "Color_hex"}
                props = [f"Vertex: {p}" for p in g.vp.keys() if p not in hidden_vertex_props] + [f"Edge: {p}" for p in g.ep.keys() if p not in hidden_edge_props]

                self.all_properties.append(props)
                newly_loaded_indices.append(current_idx)

        # After loading, perform scaling across all relevant graphs
        self._scale_properties(self.graphs, "v", 'population', 100, 180)
        # F_net is used for scaling edges (!!)
        self._scale_properties(self.graphs, "e", 'F_net', 2, 8)
        
        if newly_loaded_indices:                
            self.active_index = newly_loaded_indices[-1] # Set active to last loaded

        return newly_loaded_indices
    
    def _restore_graph_properties(self, g):
        """Recreates Vertex Surfaces for graph-tool binary files 
           since they can't be saved directly."""
        
        vertex_sfcs = g.new_vp("object")
        for v in g.vertices():
            try:
                filename = g.vp["vertex_images"][v]
                vertex_sfcs[v] = cairo.ImageSurface.create_from_png(
                f"./Data/{filename}")
            except Exception as e:
                print(f"Warning: could not load node image {filename} from Data  --> {e}")
                try:
                    vertex_sfcs[v] = cairo.ImageSurface.create_from_png(f"./Data_Default_Placeholder/{filename}")
                except Exception as e2:
                    print(f"Warning: could not load placeholder image {filename} --> {e2}")
                    vertex_sfcs[v] = None
        g.vp["vertex_sfcs"] = vertex_sfcs

    def _parse_cycle_table_csv(self, filename):
        """Parse FECD cycles_table.csv → cycles list + fluxes + n_nodes.
        Matches the exact format you described (node_k columns + flux)."""
        df = pd.read_csv(filename)
        if 'flux' not in df.columns:
            raise ValueError("cycles_table.csv must contain a 'flux' column")

        node_cols = [col for col in df.columns if col.startswith('node_')]
        if not node_cols:
            raise ValueError("No node_* columns found in CSV")

        node_ids = [str(col[len('node_'):]).strip() for col in node_cols]
        if any(not node_id for node_id in node_ids):
            raise ValueError("Every node_* col must include a node ID after 'node_'")
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("Duplicate node IDs foudn in node_* cols")

        node_id_by_col = dict(zip(node_cols, node_ids))
        cycles = []
        fluxes = []
        fls_edges = []
        rls_edges = []
        source_row_indices = []
        has_fls = 'F.L.S' in df.columns
        has_rls = 'R.L.S' in df.columns

        for row_idx, row in df.iterrows():
            pos_to_node = {}
            for col in node_cols:
                pos = row[col]
                if pd.notna(pos):
                    try:
                        node_id = node_id_by_col[col]          # node_0 → 0, node_1 → 1, ...
                        position = int(pos)
                        pos_to_node[position] = node_id
                    except Exception:
                        continue
            if pos_to_node:
                # Reconstruct canonical cycle order by sorting on step position
                sorted_positions = sorted(pos_to_node.keys())
                cycle = [pos_to_node[p] for p in sorted_positions]
                cycles.append(cycle)
                fluxes.append(float(row['flux']))
                fls_edges.append(self._parse_edge_label(row['F.L.S']) if has_fls else None)
                rls_edges.append(self._parse_edge_label(row['R.L.S']) if has_rls else None)
                source_row_indices.append(row_idx)

        print(f"Loaded {len(cycles)} cycles with {len(node_ids)} nodes from {filename}")
        return cycles, fluxes, fls_edges, rls_edges, node_ids, df, source_row_indices

    def _build_dataframes_from_cycles(self, cycles, fluxes, fls_edges, rls_edges, node_ids, source_df, source_row_indices):
        """Build df_vertex, df_edge, df_path from parsed cycles. Updated to be generalized to any systems"""
        # Discover dynamic CSV columns
        vert_col_map = {}
        edge_col_map = {}

        # Keep path_direction, but do not allow generated path IDs/keys
        # to be overwritten by CSV columns.
        ignored_path_cols = {"path_ID", "path_id", "path_key"}
        path_cols = []

        for col in source_df.columns:
            if col.startswith("vert_"):
                parts = col.split("_", 2)
                if len(parts) == 3:
                    _, node_id, attr = parts
                    vert_col_map[col] = (str(node_id), attr)

            elif col.startswith("edge_"):
                parts = col.split("_", 3)
                if len(parts) == 4:
                    _, src, tgt, attr = parts
                    edge_col_map[col] = (str(src), str(tgt), attr)

            elif col.startswith("path_"):
                if col not in ignored_path_cols:
                    path_cols.append(col)

        # path_direction should always exist as a filterable path-level edge property.
        if "path_direction" not in path_cols:
            path_cols.insert(0, "path_direction")

        vert_attr_names = sorted(set(attr for _, attr in vert_col_map.values()))
        edge_attr_names = sorted(set(attr for _, _, attr in edge_col_map.values()))

        edge_lookup = {
            (src, tgt, attr): col
            for col, (src, tgt, attr) in edge_col_map.items()
        }

        # === Vertex table ===
        vertex_ids = [str(node_id) for node_id in node_ids]
        populations = [1.0] * len(vertex_ids)
        images = [f"{node_id}.png" for node_id in vertex_ids]

        surfaces = []
        for img_name in images:
            try:
                surfaces.append(cairo.ImageSurface.create_from_png(f'./Data/{img_name}'))
            except Exception as e:
                print(f"Warning: could not load node image {img_name} -> {e}")
                try: 
                    surfaces.append(cairo.ImageSurface.create_from_png(f"./Data_Default_Placeholder/{img_name}"))
                except Exception as e2:
                    print(f"Warning: could not load placeholder image {img_name} --> {e2}")
                    surfaces.append(None)

        df_vertex = pd.DataFrame({
            'Population': populations,
            'Images': images,
            'Surface': surfaces
        }, index=vertex_ids)

        # Add dynamic vertex columns.
        for attr in vert_attr_names:
            df_vertex[attr] = pd.NA

        # Fill dynamic vertex values.
        # Important: graph vertices are unique, so vertex props should be stable.
        # If the same vertex attr appears with conflicting values, keep the first.
        for row_idx in source_row_indices:
            row = source_df.loc[row_idx]

            for col, (node_id, attr) in vert_col_map.items():
                if node_id not in df_vertex.index:
                    continue

                value = row[col]
                if pd.isna(value):
                    continue

                old_value = df_vertex.at[node_id, attr]
                if pd.isna(old_value):
                    df_vertex.at[node_id, attr] = value
                elif old_value != value:
                    print(
                        f"Warning: conflicting vertex attr '{attr}' for vertex {node_id}. "
                        f"Keeping {old_value!r}, ignoring {value!r}."
                    )
        # === Path / Edge tables ===
        edge_table = []
        path_table = []
        path_table_indices = []

        base_edge_cols = [
            'Source_Vertex', 'Target_Vertex', 'Flow', 'Path_set', 'Path_id',
            'k_fwd', 'k_int', 'k_rev', 'F_fwd', 'F_rev', 'F_net',
            'is_fls', 'is_rls'
        ]
        generated_edge_cols = ['cycle_number', 'path_ID']

        # Avoid duplicate dataframe column names.
        reserved_edge_names = set(base_edge_cols + generated_edge_cols + path_cols)
        filtered_edge_attr_names = []
        for attr in edge_attr_names:
            if attr in reserved_edge_names:
                print(f"Warning: ignoring edge attr '{attr}' because it conflicts with a reserved column name.")
            else:
                filtered_edge_attr_names.append(attr)
        edge_attr_names = filtered_edge_attr_names

        dynamic_edge_cols = generated_edge_cols + path_cols + edge_attr_names

        for local_path_id, (cycle, flux, fls_edge, rls_edge, row_idx) in enumerate(
            zip(cycles, fluxes, fls_edges, rls_edges, source_row_indices)
        ):
            row = source_df.loc[row_idx]
            states = [str(node) for node in cycle]
            cycle_number = f"cycle_{row_idx}"

            # path_ID is the readable path sequence.
            path_ID = "-".join(states + [states[0]]) if states else ""

            # path_direction comes from CSV path_direction if available
            path_direction = "F"

            if "path_direction" in source_df.columns and pd.notna(row["path_direction"]):
                raw_direction = str(row["path_direction"]).strip()
                if raw_direction:
                    path_direction = raw_direction

            path_set_id = "cycle_set:0"
            path_id = local_path_id

            fls_label = f"{fls_edge[0]}-{fls_edge[1]}" if fls_edge is not None else None
            fls_source = fls_edge[0] if fls_edge is not None else None
            fls_target = fls_edge[1] if fls_edge is not None else None

            rls_label = f"{rls_edge[0]}-{rls_edge[1]}" if rls_edge is not None else None
            rls_source = rls_edge[0] if rls_edge is not None else None
            rls_target = rls_edge[1] if rls_edge is not None else None

            # Path values are stored in df_path and also copied to every edge row.
            path_values = []
            for col in path_cols:
                if col == "path_direction":
                    path_values.append(path_direction)
                elif col in source_df.columns:
                    value = row[col]
                    path_values.append(value if pd.notna(value) else pd.NA)
                else:
                    path_values.append(pd.NA)

            path_table.append([
                flux,
                states,
                [1.0] * len(states),
                [0.0] * len(states),
                [0.0] * len(states),
                [0.0] * len(states),
                [flux] * len(states),
                [flux] * len(states),
                [flux] * len(states),
                fls_label,
                fls_source,
                fls_target,
                rls_label,
                rls_source,
                rls_target,
                cycle_number,
                path_ID,
            ] + path_values)

            path_table_indices.append((path_set_id, path_id))

            # Edge rows: one row per transition in the path.
            for i in range(len(cycle)):
                src = states[i]
                tgt = states[(i + 1) % len(cycle)]

                is_fls = fls_edge is not None and src == fls_edge[0] and tgt == fls_edge[1]
                is_rls = rls_edge is not None and src == rls_edge[0] and tgt == rls_edge[1]

                base_edge_values = [
                    src,
                    tgt,
                    flux,
                    path_set_id,
                    path_id,
                    0.0,
                    0.0,
                    0.0,
                    flux,
                    flux,
                    flux,
                    is_fls,
                    is_rls,
                ]

                generated_values = [
                    cycle_number,
                    path_ID,
                ]

                # edge_<src>_<tgt>_<attr> only applies to the matching edge.
                edge_values = []
                for attr in edge_attr_names:
                    csv_col = edge_lookup.get((src, tgt, attr))
                    if csv_col is None:
                        edge_values.append(pd.NA)
                    else:
                        value = row[csv_col]
                        edge_values.append(value if pd.notna(value) else pd.NA)

                edge_table.append(base_edge_values + generated_values + path_values + edge_values)

        df_edge = pd.DataFrame(
            edge_table,
            columns=base_edge_cols + dynamic_edge_cols
        )

        path_columns = [
            'Flow', 'States', 'State_populations',
            'State_k_fwd', 'State_k_int', 'State_k_rev',
            'State_F_fwd', 'State_F_rev', 'State_F_net',
            'FLS', 'FLS_source', 'FLS_target',
            'RLS', 'RLS_source', 'RLS_target',
            'cycle_number', 'path_ID',
        ] + path_cols

        df_path = pd.DataFrame(
            data=path_table,
            index=pd.MultiIndex.from_tuples(path_table_indices, names=('Path_set', 'Path_id')),
            columns=path_columns
        )

        n = len(cycles)
        path_color_names = [colormap_names[i % len(colormap_names)] for i in range(n)]
        path_colors = [colormap_rgba_norm[i % len(colormap_rgba_norm)] for i in range(n)]
        path_color_hex = [colormap_hex[i % len(colormap_hex)] for i in range(n)]

        df_path['Color'] = path_colors
        df_path["Color_name"] = path_color_names
        df_path["Color_hex"] = path_color_hex

        path_style_by_id = {
        i: (path_colors[i], path_color_names[i], path_color_hex[i])
        for i in range(n) 
        }

        edge_colors = []
        edge_color_names = []
        edge_color_hexes = []

        for _, row in df_edge.iterrows():
            color, color_name, color_hex = path_style_by_id[row['Path_id']]
            edge_colors.append(color)
            edge_color_names.append(color_name)
            edge_color_hexes.append(color_hex)

        df_edge['Color'] = edge_colors
        df_edge['Color_name'] = edge_color_names
        df_edge['Color_hex'] = edge_color_hexes

        return df_vertex, df_edge, df_path
    
    def _parse_edge_label(self, edge_label):
        """Take CSV input like '1-2' and store as ('1', '2').
        Missing, blank, or malformed labels return None so older CSVs
        without FLS data still load safely."""

        if pd.isna(edge_label):
            return None
        edge_label = str(edge_label).strip()
        if not edge_label:
            return None
        try:
            src, tgt = edge_label.split('-', 1)
            return src.strip(), tgt.strip()
        except ValueError:
            print(f"Warning: could not parse edge label '{edge_label}'")
            return None

    def _load_graph_from_cycle_table_csv(self, filename):
        """Full loader for the new FECD format"""
        cycles, fluxes, fls_edges, rls_edges, node_ids, source_df, source_row_indices = self._parse_cycle_table_csv(filename)
        df_vertex, df_edge, df_path = self._build_dataframes_from_cycles(cycles, fluxes, fls_edges, rls_edges, node_ids, source_df, source_row_indices)

        # Build a display summary before df_path is discarded
        cycle_summary = []
        total_flow = float(df_path["Flow"].sum()) if len(df_path) > 0 else 0.0

        excluded_path_summary_cols = {
            "States", "State_populations", "State_k_fwd", "State_k_int",
            "State_k_rev", "State_F_fwd", "State_F_rev", "State_F_net",
            "Color", "Color_name",
        }

        for _, row in df_path.iterrows():
            flow = float(row["Flow"])
            flux_pct_system = flow / total_flow if total_flow else 0.0

            summary_row = {}

            for col in df_path.columns:
                if col in excluded_path_summary_cols:
                    continue
                summary_row[col] = self._clean_cycle_summary_value(row[col])

            summary_row["path_ID"] = str(row["path_ID"])
            summary_row["path_direction"] = str(row["path_direction"]) if "path_direction" in row else "N/A"
            summary_row["color"] = str(row["Color_name"]) if "Color_name" in row else str(row["Color"])
            summary_row["color_hex"] = str(row["Color_hex"]) if "Color_hex" in row else ""
            summary_row["flow"] = flow
            summary_row["flux_pct"] = flux_pct_system
            cycle_summary.append(summary_row)

        total_flow = float(df_path["Flow"].sum()) if len(df_path) > 0 else 0.0
        df_edge["Flux_pct_system"] = df_edge["Flow"] / total_flow if total_flow else 0.0
        init_coords = cl.place_points([row["States"] for _, row in df_path.iterrows()])
        graph = self._initialize_graph_object(df_vertex, df_edge, df_path, init_coords)
        return graph, cycle_summary

    def save_graph_to_gt(self, filename):
        if self.active_index == -1:
            return False
        
        graph_to_save = gt.Graph(self.graphs[self.active_index])
        self._attach_app_payload_to_graph(graph_to_save, self.active_index)    

        # Cairo surfaces can't be pickled, so remove them before saving
        if "vertex_sfcs" in graph_to_save.vp:
            del graph_to_save.vp["vertex_sfcs"]
        
        graph_to_save.save(filename, fmt='gt')
        return True

    def save_graph_to_image(self, filename):
        if self.active_index == -1: return False
        graph = self.get_current_graph(1)
        if not graph: return False
        
        filetype = "svg" # Default
        if filename.endswith(".png"): filetype = "png"
        elif filename.endswith(".pdf"): filetype = "pdf"
        elif filename.endswith(".ps"): filetype = "ps"
        elif not filename.endswith(".svg"): filename += ".svg"

        gt.graph_draw(graph, pos=graph.vp.pos, output_size=(2000, 2000),
                      output=filename, fmt=filetype, bg_color=None,
                      vertex_shape="circle", vertex_color=[1, 1, 1, 0],
                      vertex_fill_color=[1, 1, 1, 0], vertex_size=graph.vp.size,
                      vertex_surface=graph.vp.vertex_sfcs, edge_color=graph.ep.color,
                      edge_pen_width=graph.ep.weight, edge_dash_style=graph.ep.dash_style, edge_end_marker="arrow",
                      edge_marker_size=30)
        return True
    
    def apply_cycle_recolor(self, path_id, path_direction, color_name, color_hex, color_rgba):
        """Recolor every edge belonging to one path_id, path_direction"""
        if self.active_index == -1:
            return False
        g = self.get_current_graph(0)
        if g is None:
            return False
        if "path_ID" not in g.ep:
            return False
        has_direction = "path_direction" in g.ep
        has_color_name = "Color_name" in g.ep
        has_color_hex = "Color_hex" in g.ep

        matched = False

        for edge in g.edges():
            edge_path_id = str(g.ep["path_ID"][edge])
            edge_direction = str(g.ep["path_direction"][edge] if has_direction else "")

            if edge_path_id == str(path_id) and edge_direction == str(path_direction):
                g.ep["color"][edge] = color_rgba
                if has_color_name:
                    g.ep["Color_name"][edge] = str(color_name)
                if has_color_hex:
                    g.ep["Color_hex"][edge] = str(color_hex)
                matched = True

        if matched and self.active_index < len(self.cycle_summaries):
            for row in self.cycle_summaries[self.active_index]:
                if str(row.get("path_ID", "")) == str(path_id) and str(row.get("path_direction", "")) == str(path_direction):
                    row["color"] = str(color_name)
                    row["color_hex"] = str(color_hex)
        return matched

    def apply_filter(self, prop_map_type, prop_name, min_val=None, max_val=None, value=None, operator="AND", negated=False):
        graph = self.get_current_graph(0)
        GraphView = self.get_current_graph(1)
        if not graph or not GraphView: return #TODO: add checks and error messages to self.get_current_graph() instead of here
        
        is_vertex_prop = prop_map_type == "Vertex"
        prop_map = graph.vp[prop_name] if is_vertex_prop else graph.ep[prop_name]

        ptype = prop_map.python_value_type()
        is_numeric = ptype in {int, float}
        mask_array = None

        if is_numeric:
            min_v, max_v = float(min_val), float(max_val)
            mask_array = (prop_map.a >= min_v) & (prop_map.a <= max_v)
        elif ptype == str:
            all_values = prop_map.get_2d_array([0], dtype=str).flatten()
            mask_array = np_isin(all_values, value)
        else:
            plist = []
            for p in prop_map:
                plist.append(p)
            mask_array = np_isin(plist, value)

        value = [min_v, max_v] if is_numeric else [value]
        index = int(max((filt.get('index', -1) for filt in self.active_filters[self.active_index]), default=-1) + 1)

        stored_filter = {
        'operator': operator,
        'negated': negated,
        'type': prop_map_type,
        'name': prop_name,
        'value': value,
        'mask': mask_array,
        'index': index}

        self.active_filters[self.active_index].append(stored_filter)

        # Do not mutate the current graph mask here anymore.
        # Let the controller rebuild from the ordered filter list.
        return stored_filter, mask_array, index

    def clear_all_filters(self):
        graph = self.get_current_graph(0)
        if graph:
            graph.vp['mask'].set_values(np_ones(graph.num_vertices()))
            graph.ep['mask'].set_values(np_ones(graph.num_edges()))
        gv = self.get_current_graph(1)
        if gv:
            gv.set_filters(graph.ep['mask'], graph.vp['mask'])
        self.active_filters[self.active_index] = []

    def remove_filters(self, filter_ids):
        # Find and remove filters from active_filters list
        matching_indices = []
        for index, d in enumerate(self.active_filters[self.active_index]):
            if d.get('index') in filter_ids:
                matching_indices.append(index)
        for index in sorted(matching_indices, reverse=True):
            self.active_filters[self.active_index].pop(index)

    def set_GraphView(self):
        # get current graph
        graph = self.get_current_graph(0)
        # Create filtered GraphView
        filtered_graph_view = gt.GraphView(graph, vfilt=graph.vp['mask'], efilt=graph.ep['mask'])
        # Save the GraphView
        self.GraphViews[self.active_index] = filtered_graph_view

    # Private helper methods
    def _initialize_graph_object(self, df_vertex, df_edge, df_path, init_coords):
        """Create the graph-tool graph from df_vertex, df_edge, and df_path.
        Dynamic edge columns are included directly in graph construction.
        Dynamic vertex columns are attached after graph construction."""

        # Color handling; Checking if Color exists in df before adding
        if 'Color' not in df_path.columns:
            n = len(df_path)
            path_colors = [
                colormap_rgba_norm[i % len(colormap_rgba_norm)]
                for i in range(n)
            ]
            df_path['Color'] = path_colors

        if 'Color' not in df_edge.columns:
            edge_colors = [
                df_path.loc[(row['Path_set'], row['Path_id']), "Color"]
                for _, row in df_edge.iterrows()
            ]
            df_edge['Color'] = edge_colors

        # Old JSON and CSV files that do not have FLS/RLS should still run.
        if 'is_fls' not in df_edge.columns:
            df_edge['is_fls'] = False
        if 'is_rls' not in df_edge.columns:
            df_edge['is_rls'] = False

        # Base edge columns
        # These columns preserve the original graph construction behavior.
        base_edge_cols = [
            'Source_Vertex',
            'Target_Vertex',
            'Flow',
            'Path_set',
            'Path_id',
            'k_fwd',
            'k_int',
            'k_rev',
            'F_fwd',
            'F_rev',
            'F_net',
            'is_fls',
            'is_rls',
            'Color',
        ]

        missing_base_cols = [col for col in base_edge_cols if col not in df_edge.columns]
        if missing_base_cols:
            raise ValueError(f"df_edge is missing required columns: {missing_base_cols}")

        base_eprops = [
            ('flow', 'float'),
            ('path_set', 'string'),
            ('path', 'string'),
            ('k_fwd', 'float'),
            ('k_int', 'float'),
            ('k_rev', 'float'),
            ('F_fwd', 'float'),
            ('F_rev', 'float'),
            ('F_net', 'float'),
            ('is_fls', 'bool'),
            ('is_rls', 'bool'),
            ('color', 'vector<double>'),
        ]

        # Anything in df_edge that is not part of the base schema becomes a
        # dynamic edge property map, unless it would collide with an existing
        # internal graph property.
        reserved_edge_prop_names = {
            name for name, _ in base_eprops
        } | {
            'weight',
            'dash_style',
            'mask',
        }

        raw_extra_edge_cols = [
            col for col in df_edge.columns
            if col not in base_edge_cols
        ]

        df_edge_for_gt = df_edge[base_edge_cols].copy()

        # Normalize base columns for graph-tool.
        df_edge_for_gt['Source_Vertex'] = df_edge_for_gt['Source_Vertex'].astype(str)
        df_edge_for_gt['Target_Vertex'] = df_edge_for_gt['Target_Vertex'].astype(str)
        df_edge_for_gt['Path_set'] = df_edge_for_gt['Path_set'].astype(str)
        df_edge_for_gt['Path_id'] = df_edge_for_gt['Path_id'].astype(str)

        for col in ['Flow', 'k_fwd', 'k_int', 'k_rev', 'F_fwd', 'F_rev', 'F_net']:
            df_edge_for_gt[col] = pd.to_numeric(df_edge_for_gt[col], errors='coerce')

        df_edge_for_gt['is_fls'] = df_edge_for_gt['is_fls'].fillna(False).astype(bool)
        df_edge_for_gt['is_rls'] = df_edge_for_gt['is_rls'].fillna(False).astype(bool)
        extra_eprops = []

        for col in raw_extra_edge_cols:
            if col in reserved_edge_prop_names:
                print(f"Warning: skipping edge property '{col}' because it conflicts with an internal property.")
                continue

            series = df_edge[col]
            non_missing = series.dropna()

            # Treat True/False-like values as categorical strings
            bool_tokens = {"true", "false", "yes", "no", "y", "n"}
            is_bool_like = (
                len(non_missing) > 0
                and all(str(v).strip().lower() in bool_tokens for v in non_missing.tolist())
            )

            numeric = pd.to_numeric(non_missing, errors='coerce')
            is_numeric = (
                len(non_missing) > 0
                and not is_bool_like
                and numeric.notna().all()
            )

            if is_numeric:
                df_edge_for_gt[col] = pd.to_numeric(series, errors='coerce')
                extra_eprops.append((col, 'float'))
            else:
                df_edge_for_gt[col] = series.where(series.notna(), "").astype(str)
                extra_eprops.append((col, 'string'))

        # Build the graph
        g = gt.Graph(
            df_edge_for_gt.values.tolist(),
            hashed=True,
            directed=True,
            eprops=base_eprops + extra_eprops
        )

        # === Base vertex properties ===
        vp_ids = list(g.vp['ids'])
        id_to_index = {str(v_id): i for i, v_id in enumerate(vp_ids)}

        vertex_population = g.new_vp("float")
        init_pos = g.new_vp("vector<float>")
        vertex_images = g.new_vp("string")
        vertex_sfcs = g.new_vp("object")

        for v_id in vp_ids:
            v_key = str(v_id)
            v_index = id_to_index[v_key]

            if v_key not in df_vertex.index:
                raise ValueError(f"Vertex '{v_key}' is present in graph edges but missing from df_vertex.")

            init_pos[v_index] = init_coords.get(v_key, (0.0, 0.0))
            vertex_population[v_index] = float(df_vertex.loc[v_key, "Population"])
            vertex_images[v_index] = str(df_vertex.loc[v_key, "Images"])
            vertex_sfcs[v_index] = df_vertex.loc[v_key, "Surface"]

        pin_list = g.new_vp("bool")
        if len(df_path) > 0:
            for v_id in df_path.iloc[0].loc['States']:
                v_key = str(v_id)
                if v_key in id_to_index:
                    pin_list[id_to_index[v_key]] = True

        init_pos = gt.sfdp_layout(g, pin=pin_list, pos=init_pos, max_iter=3000)

        g.vp["population"] = vertex_population
        g.vp["init_pos"] = init_pos
        g.vp["pos"] = init_pos
        g.vp["vertex_images"] = vertex_images
        g.vp["vertex_sfcs"] = vertex_sfcs

        # Dynamic vertex properties from vert_<node>_<attr> columns that were added to df_vertex.
        base_vertex_cols = {'Population', 'Images', 'Surface'}
        reserved_vertex_prop_names = {
            'ids',
            'population',
            'init_pos',
            'pos',
            'vertex_images',
            'vertex_sfcs',
            'size',
            'mask',
        }
        vertex_extra_cols = [
            col for col in df_vertex.columns
            if col not in base_vertex_cols
            and col not in reserved_vertex_prop_names
        ]

        for col in vertex_extra_cols:
            if col in g.vp:
                print(f"Warning: skipping vertex property '{col}' because it already exists.")
                continue
            series = df_vertex[col]
            non_missing = series.dropna()
            bool_tokens = {"true", "false", "yes", "no", "y", "n"}
            is_bool_like = (
                len(non_missing) > 0
                and all(str(v).strip().lower() in bool_tokens for v in non_missing.tolist())
            )
            numeric = pd.to_numeric(non_missing, errors='coerce')
            is_numeric = (
                len(non_missing) > 0
                and not is_bool_like
                and numeric.notna().all()
            )
            if is_numeric:
                prop = g.new_vp('float')
                for v_id in vp_ids:
                    v_key = str(v_id)
                    v_index = id_to_index[v_key]
                    value = df_vertex.loc[v_key, col]
                    prop[v_index] = float(value) if pd.notna(value) else float('nan')
            else:
                prop = g.new_vp('string')
                for v_id in vp_ids:
                    v_key = str(v_id)
                    v_index = id_to_index[v_key]
                    value = df_vertex.loc[v_key, col]
                    prop[v_index] = "" if pd.isna(value) else str(value)
            g.vp[col] = prop

        # === Drawing/scaling helper properties ===
        g.ep['weight'] = g.new_ep('float')
        g.vp['size'] = g.new_vp('float')

        # Creating dashed line styles for FLS/RLS edges.
        g.ep['dash_style'] = g.new_ep('vector<double>')
        for e in g.edges():
            if g.ep['is_fls'][e] and g.ep['is_rls'][e]:
                g.ep['dash_style'][e] = [0.2, 0.1, 0.05, 0.1, 0.0] # [on, off, ... , ... offset]
            elif g.ep['is_fls'][e]:
                g.ep['dash_style'][e] = [0.2, 0.1, 0.0]
            elif g.ep['is_rls'][e]:
                g.ep['dash_style'][e] = [0.05, 0.05, 0.0]
            else:
                g.ep['dash_style'][e] = []
        g.ep['mask'] = g.new_ep('bool')
        g.vp['mask'] = g.new_vp('bool')
        g.vp['mask'].set_values(np_ones(g.num_vertices()))
        g.ep['mask'].set_values(np_ones(g.num_edges()))
        return g
    
    def _scale_properties(self, graphs, prop_type, prop_name, mi, ma):
        """Scale vertex sizes or edge weights with safe handling when all values are equal."""
        if not graphs:
            return

        property_matrix = []

        if prop_type in ("v", "vertex"):
            for graph in graphs:
                values = list(graph.vp[prop_name])
                property_matrix.append(values)

            all_values = [v for sublist in property_matrix for v in sublist]
            if not all_values:
                return

            global_min = min(all_values)
            global_max = max(all_values)
            log_min = ln(global_min)
            log_max = ln(global_max)
            # === SAFETY FIX ===
            if global_max == global_min:
                # All values are the same → assign constant size in the middle of the range
                default_size = (mi + ma) / 2
                for graph in graphs:
                    graph.vp.size = graph.vp[prop_name].transform(
                        lambda x: default_size, value_type='double')
                print(f"→ All {prop_name} values are identical. Using constant size = {default_size}")
                return

            power = 0.5
            for graph in graphs:
                graph.vp.size = graph.vp[prop_name].transform(
                    lambda x: mi + (ma - mi) * np_power((ln(x/global_min)) / (log_max - log_min), power) + 0.5,
                    value_type='double')

        elif prop_type in ("e", "edge"):
            for graph in graphs:
                values = list(graph.ep[prop_name])
                property_matrix.append(values)

            all_values = [v for sublist in property_matrix for v in sublist]
            global_min = min(all_values)
            global_max = max(all_values)
            log_min = ln(global_min)
            log_max = ln(global_max)

            if global_max == global_min:
                default_weight = (mi + ma) / 2
                for graph in graphs:
                    graph.ep.weight = graph.ep[prop_name].transform(
                        lambda x: default_weight, value_type='double')
                print(f"→ All {prop_name} values are identical. Using constant weight = {default_weight}")
                return

            power = 0.5
            for graph in graphs:
                graph.ep.weight = graph.ep[prop_name].transform(
                    lambda x: mi + (ma - mi) * np_power((ln(x/global_min)) / (log_max - log_min), power) + 0.5,
                    value_type='double')
