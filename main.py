# main.py

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
from gi.repository import Gtk
from model import GraphModel
from view import GraphView
from controller import GraphController

if __name__ == "__main__":
    # 1. Create the Model to hold the data
    app_model = GraphModel()
    
    # 2. Create the Controller and give it the Model
    app_controller = GraphController(model=app_model)
    
    # 3. Create the View and give it the Controller
    app_view = GraphView(controller=app_controller)
    
    # 4. Give the Controller a reference to the View
    app_controller.set_view(app_view)

    print(
        """--- nCORE visualizer Copyright (C) 2026 Tyler G. Southam ---
This is free software, and you are welcome to redistribute it
under certain conditions. See the GNU GPLv3 license."""
    )
    
    # 5. Start the GTK main loop
    Gtk.main()