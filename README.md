This repository houses the public releases of nCORE visualizer to accompany the MsRKM software.

Currently, main.py launches a GTK GUI and can process a .csv file to a pandas dataframe, then pass the relevant data to cycle_layout.py to obtain initial coordinates for each state (node) represented in the input file, then load a visualization of the graph to the GUI. Any number of attributes can be added to the graph following the CSV format noted below. Important and recently added features can be seen at the bottom of the README

DEPENDENCIES:
  - python=3.11
  - numpy
  - matplotlib
  - scipy
  - graph-tool
  - pandas

INSTALLATION:
- Graph-tool must be installed using conda-forge (available for Linux and MacOS systems; WSL must be used for Windows).        Within CONFIG.txt, there is an environment file that can be used to install all dependencies as shown below. This will       create a conda env named "graph_viz_env" that will be used to run the program. Ensure the .yml file is in cwd, then run
```
conda env create -f environment.yml
conda activate graph_viz_env
```

NODE IMAGES:
- Images used for nodes in the graph are expected to be in a folder called "Data" using the following naming convention:
  - node_* --> * = the ID such that *.png is the image file associated
- We have provided two sets of images: "Data" holds all images (16) for a 4-site ion channel (protein image), and              "Data_Default_Placeholder" which has generic circled number images compatible with up to 64 nodes.
  - An image_generator script has been added to "Data_Default_Placeholder" so one can generate any number of node images that     they need
  - "Data_Default_Placeholder" is now the main fallback if "Data" cannot be found

RUNNING THE CODE:
- Install dependencies as noted above
- Run using: "python3 main.py" as any other Python script
- Click the "Load File(s)" button to open the file load dialog and choose a .csv file for now (Use the example .CSV provided   in the Data directory)
- Ensure "Data" folder exists in cwd and that node images are inside
- Manipulate the graph using the mouse buttons and keyboard as described in these paragraphs from the graph-tool               documentation (https://graph-tool.skewed.de/static/doc/autosummary/graph_tool.draw.GraphWidget.html).
  >Note that the keybinds require "focus" on the graph window itself -- use tab to ensure you're in the right window.
  - The graph drawing can be panned by dragging with the middle mouse button pressed. The graph may be zoomed by scrolling       with the mouse wheel, or equivalent (if the “shift” key is held, the vertex/edge sizes are scaled accordingly). The          layout may be rotated by dragging while holding the “control” key. Pressing the “r” key centers and zooms the layout         around the graph. By pressing the “a” key, the current translation, scaling, and rotation transformations are applied to      the vertex positions themselves, and the transformation matrix is reset (if this is never done, the given position           properties are never modified).
  - Individual vertices may be selected by pressing the left mouse button. The currently selected vertex follows the mouse       pointer. To stop the selection, the right mouse button must be pressed. Alternatively, a group of vertices may be            selected by holding the “shift” button while the pointer is dragged, while pressing the left button. The selected            vertices may be moved by dragging the pointer with the left button pressed. They may be rotated by holding the               “control” key and scrolling with the mouse. If the key “z” is pressed, the layout is zoomed to fit the selected vertices     only.
  - (Use with caution on large networks) If the key “s” is pressed, the dynamic spring-block layout is activated. Vertices       that are currently selected are not updated.

CSV FILE FORMAT: 
- The CSV format has been generalized to handle any type of network with any number of nodes/edges/attributes. These           attributes can be edge-level (some specific v1-v2), vertex-level (some specific v1), or path-level (some specific cycle,     0-1-2-0). Below will show exactly what's expected for the CSV file, and the example file can be viewed to supplement your    understanding.

- The top row holds all of the identifiers, and each row below is a given cycle within the network (Note that one can use a    single row if they do not have a path-driven network.

- Top row: node_id (all node_id cols first), then Flux. These are the only required columns 
  >(Flux controls edge weights; if no flux values for your network, treat it as a weights column). 
	- Two additional `<attr>` have been hard-coded by name (but do not have to be used): "F.L.S", "R.L.S"
	  - These are the Flux Limiting and Rate Limiting steps, respectively
	- To add any additional attribute, follow the conventions below:
	  -  Path Level = `path_<attr>` where `<attr>` can be any `<attr>` describing entire paths
		-  Edge Level = `edge_<src_id>_<tgt_id>_<attr>`, edges that don't contain a value are handled properly
		-  Vertex Level = `vertex_<node_id>_<attr>`, proper handling of missing values
	- Direction has been taken into account and can be added by "path_direction". If not specified, direction will be filled       as "F"

GT FILE FORMAT:
- .gt is the built-in binary file format provided by Graph-tool. This format is used to save the current layout of a graph, which can be helpful for constructing template layouts or saving work to pick up later. All path-level metadata is now handled properly and will save with the .gt format.

CONDITIONAL FILTERING: 
- AND/OR + NOT filtering options have been added. Due to the nature of the code, OR statements must come first before AND      statements. Currently, you cannot mix AND OR statements as shown below:
  - OR… AND… OR… OR… AND… 
  >This results in improper grouping of conditions. All OR statements must come before any AND constraints. The only outlier     to this rule is the first conditional statement, which can be either AND/OR.

TIPS AND TRICKS: 
- One can create template layouts for graphs that have a matching # of nodes
  - Set up the graph, save as .gt, load that .gt, select "Apply Current Graph Position", and load the graph of interest. The     benefit of this is that the template is now reusable
- One can use the 's' keybind to open a search bar within any table

EXAMPLES FOLDER:
- The examples folder holds various scripts that can be used
  - animation_zombies.py is an example script from the graph-tool documentation (https://graph-tool.skewed.de/static/doc/demos/animation/animation.html) which shows some of the animation capabilities of graph-tool.        animation_zombies_refactor.py is a chatGPT reorganization of the animation_zombies.py script.  When run, each opens a GTK    window which then shows an animation of an illness spreading through a social network with the hiding/unhiding of nodes      and edges, the use and changing of images for each node, and highlighting of nodes.
    - animation_sirs.py is another script from the same graph-tool documentation page
    - LayoutMath_1.1.ipynb is a Jupyter notebook from which the cycle_layout.py script was written.  The main difference is        that the Jupyter notebook shows a matplotlib plot of the calculated positions for quick visualization of the script          output

DEVELOPMENT TESTS:
- The Developement_Tests folder contains scripts and data which may or may not run, but may have some useful bits and pieces.
- In particular, graph-tool_GTK.py is a quick prototype of the GUI with a tabbed main window and the ability to generate and visualize a random graph.


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
