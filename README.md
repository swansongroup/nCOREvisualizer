This repository houses the public releases of nCORE visualizer to accompany the MsRKM software.

Main.py launches a GTK GUI and calls model.py, view.py, and controller.py and initializes class instances for each. nCORE visualizer can process a CSV file to pandas dataframes, then pass the relevant data to cycle_layout.py to obtain initial coordinates for each state (vertex) represented in the input file, then load a visualization of the graph to the GUI. Any number of attributes can be added to the graph following the CSV format noted below. Important and recently added features can be seen at the bottom of the README

DEPENDENCIES:
  - python=3.11
  - graph-tool
  - numpy
  - scipy
  - pandas

INSTALLATION:
- Install your conda of choice (miniconda is recommended)
- Graph-tool must be installed using conda-forge (available for Linux and MacOS systems; WSL must be used for Windows). Within the environment_config/ directory, there is an environment.yml file that can be used to install all dependencies as shown below. This will create a conda env named "graph_viz_env" that will be used to run the program. Ensure the .yml file is in cwd, then run
```
conda env create -f environment.yml
conda activate graph_viz_env
```

NODE IMAGES:
- Images used for nodes in the graph are expected to be in a folder called "Data" using the following naming convention:
  - node_* --> * = the ID such that *.png is the image file associated with node_*.
- We have provided two sets of images: "Data" holds all images (16) for a 4-site ion channel (protein image), and "Data_Default_Placeholder" which has generic circled number images compatible with up to 64 nodes.
  - An image_generator script has been added to "Data_Default_Placeholder" so one can generate any number of generic numbered node images that they need
  - "Data_Default_Placeholder" is the main fallback if "Data" cannot be found

RUNNING THE CODE:
- Install dependencies as noted above
- Run using: "python3 main.py" as any other Python script
- Click the "Load File(s)" button to open the file load dialog and choose a CSV file for now (Try the example CSV provided in the Data directory)
- Ensure "Data" folder exists in cwd and that node images are inside
- Manipulate the graph using the mouse buttons and keyboard as described in the graph-tool documentation (https://graph-tool.skewed.de/static/doc/autosummary/graph_tool.draw.GraphWidget.html). An overview is provided below.

*Note: The following keybinds, except as noted require "focus" on the graph window. The keyboard focus defaults to the first GTK box in the GUI layout. Use `Tab` to switch keyboard focus between GTK boxes.*

| Action | Control |
| :--- | :--- |
| **Pan** | Drag with `Middle Mouse Button` |
| **Zoom** | `Scroll Wheel` (Hold `Shift` to scale node/edge sizes) |
| **Rotate** | Drag while holding `Ctrl` |
| **Center & Zoom** | Press `r` |
| **Apply Transform** | Press `a` (Applies current translation/scaling to vertex positions) |
| **Select Node** | `Left Click` (Right click to stop following pointer) |
| **Select Group** | Hold `Shift` + drag `Left Click` |
| **Zoom to Selection** | Press `z` |
| **Activate dynamic spring-block layout** | (use with caution on large networks) Press `s` (Currently-selected vertices are not updated) |
| **Search Table** | (for use in any GTK list/table) Press `s` |

CSV FILE FORMAT: 
- The CSV format has been generalized to handle any type of cycle-decomposed network with any number of nodes/edges/attributes. These attributes can be edge-level (some specific v1-v2), vertex-level (some specific v1), or path-level (some specific cycle, 0-1-2-0). Below will show exactly what is expected for the CSV file, and the example file can be viewed to supplement your understanding.

- The top row holds all of the identifiers, and each row below is a given cycle within the network.

- Top row: node_id (all node_id cols first), then Flux. These are the only required columns 
  >(Flux controls edge weights; if no flux values for your network, treat it as a weights column). 
	- Two additional `<attr>` have been hard-coded by name (but do not have to be used): "F.L.S", "R.L.S"
	  - These are the Flux Limiting and Rate Limiting steps, respectively
	- To add any additional attribute, follow the conventions below:
	  -  Path Level = `path_<attr>` where `<attr>` can be any `<attr>` describing entire paths
		-  Edge Level = `edge_<src_id>_<tgt_id>_<attr>`, edges that do not contain a value are handled properly
		-  Vertex Level = `vertex_<node_id>_<attr>`, proper handling of missing values
	- Direction has been taken into account and can be added by "path_direction". If not specified, direction will be filled as "F".

GT FILE FORMAT:
- .gt is the built-in binary file format provided by Graph-tool. This format is used to save the current layout of a graph, which can be helpful for constructing template layouts or saving work to pick up later. All path-level metadata is handled properly and will save with the .gt format.

CONDITIONAL FILTERING: 
- AND/OR + NOT filtering options have been added.

TIPS AND TRICKS: 
- One can create template layouts for graphs that have matching nodes
  - Set up the graph, save as .gt, load that .gt, select "Apply Current Graph Position", and load the graph of interest. The benefit of this is that the template is now reusable


----------------------------------------------------------------------------
Network Cycle-oriented Relational Explorer and Visualizer (nCORE visualizer)
- Copyright (C) 2026  Tyler G. Southam

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

--- Contact: tyler.southam@utah.edu ---
