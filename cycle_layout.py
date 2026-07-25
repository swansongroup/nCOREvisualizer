# cycle_layout.py 

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

import numpy as np

# Pre-defined centers for each quadrant of 2D space
quad1_centers = [(2.000, 0.000), (1.414, 1.414), (0.000, 2.000), (4.000, 0.000), (3.696, 1.531),
                 (2.828, 2.828), (1.531, 3.696), (0.000, 4.000), (6.000, 0.000), (5.796, 1.553),
                 (5.196, 3.000), (4.243, 4.243), (3.000, 5.196), (1.553, 5.796), (0.000, 6.000),
                 (8.000, 0.000), (7.846, 1.561), (7.391, 3.061), (6.652, 4.445), (5.657, 5.657),
                 (4.445, 6.652), (3.061, 7.391), (1.531, 7.846), (0.000, 8.000)]
quad2_centers = [(-2.000, 0.000), (-1.414, 1.414), (-0.000, 2.000), (-4.000, 0.000), (-3.696, 1.531),
                 (-2.828, 2.828), (-1.531, 3.696), (-0.000, 4.000), (-6.000, 0.000), (-5.796, 1.553),
                 (-5.196, 3.000), (-4.243, 4.243), (-3.000, 5.196), (-1.553, 5.796), (-0.000, 6.000),
                 (-8.000, 0.000), (-7.846, 1.561), (-7.391, 3.061), (-6.652, 4.445), (-5.657, 5.657),
                 (-4.445, 6.652), (-3.061, 7.391), (-1.531, 7.846), (-0.000, 8.000)]
quad3_centers = [(-2.000, -0.000), (-1.414, -1.414), (-0.000, -2.000), (-4.000, -0.000), (-3.696, -1.531),
                 (-2.828, -2.828), (-1.531, -3.696), (-0.000, -4.000), (-6.000, -0.000), (-5.796, -1.553),
                 (-5.196, -3.000), (-4.243, -4.243), (-3.000, -5.196), (-1.553, -5.796), (-0.000, -6.000),
                 (-8.000, -0.000), (-7.846, -1.561), (-7.391, -3.061), (-6.652, -4.445), (-5.657, -5.657),
                 (-4.445, -6.652), (-3.061, -7.391), (-1.531, -7.846), (-0.000, -8.000)]
quad4_centers = [(2.000, -0.000), (1.414, -1.414), (0.000, -2.000), (4.000, -0.000), (3.696, -1.531),
                 (2.828, -2.828), (1.531, -3.696), (0.000, -4.000), (6.000, -0.000), (5.796, -1.553),
                 (5.196, -3.000), (4.243, -4.243), (3.000, -5.196), (1.553, -5.796), (0.000, -6.000),
                 (8.000, -0.000), (7.846, -1.561), (7.391, -3.061), (6.652, -4.445), (5.657, -5.657),
                 (4.445, -6.652), (3.061, -7.391), (1.531, -7.846), (0.000, -8.000)]


def generate_polygon_coords(n, mean, cycle_direction, radius=1, center=(0, 0)):
    """Generates coordinates based on a regular n-sided polygon."""
    # The number space from 0 to 2pi is offset based on the angle relative to the x-axis of the vector pointing from
    # the new center to the mean. The start and end points are adjusted before evenly dividing it by n and then
    # converting those n numbers to 2D points around a cirlce.  The adjusted start and end points effectively leave
    # an opening in the circle of points, facing the mean.
    
    start = 0
    end = 2 * np.pi
    offset = 0
    
    # for any cycle after the initial cycle, set the start and end to leave an open spot in the polygon 
    # facing the mean in relation to the posistion of the new center
    if center != (0,0):
        vector =  np.array(mean) - np.array(center)
        offset = np.arctan2(vector[1],vector[0])
        if n == 1:
            start = np.pi
            end = 1.75 * np.pi
        elif n == 2:
            start = np.pi / 2
            end = 1.5 * np.pi
        else:
            start = np.pi / 4
            end = 1.75 * np.pi
        endpoint = True
    
    theta = np.linspace(start + offset, end + offset, n, endpoint=False) # divide the space from start to end by n
    if cycle_direction == -1: # match the rotation of the new points to the rotation of the existing points
        theta = theta[::-1]
    # calculate cartesian coordinates from 
    x = radius * np.cos(theta) + center[0]
    y = radius * np.sin(theta) + center[1]
    return list(zip(x, y))

def _generate_center_arc(radius, quadrant):
    """ Generate new arc of centers for any given quadrant"""

    point_count = int(round(radius)) + 1
    theta = np.linspace(0, np.pi/2, point_count, endpoint=True)

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    if quadrant == 1:
        points = zip(x, y)    
    elif quadrant == 2:
        points = zip(-x, y)
    elif quadrant == 3:
        points = zip(-x, -y)
    elif quadrant == 4:
        points = zip(x, -y)
    else:
        raise ValueError( f"Invalid quadrant: {quadrant}")
    
    return [(float(round(px, 3)), float(round(py, 3))) for px,py in points]

def _extend_quadrant_centers(centers, quadrant, ring_step=2):
    """ Append new arc to existing list of centers
        --- Mutes list in place --- """

    if centers:
        outer_radius = max(max(abs(x), abs(y)) for x, y in centers)
        next_radius = ring_step * (int(round(outer_radius / ring_step)) + 1)
    
    new_centers = _generate_center_arc(next_radius, quadrant)

    for center in new_centers:
        if center not in centers:
            centers.append(center)
            
    return centers 

def choose_new_center(mean, previous_centers):
    # calculate closest pre-defined center in lists above based on the average of point1 and point2
    
    avg = np.array(mean)    

    # find preferred quadrant
    if mean[0] > 0 and mean[1] >= 0:
        primary = quad1_centers
        primary_quadrant = 1
    elif mean[0] <= 0 and mean[1] > 0:
        primary = quad2_centers
        primary_quadrant = 2
    elif mean[0] < 0 and mean[1] <= 0:
        primary = quad3_centers
        primary_quadrant = 3
    elif mean[0] >= 0 and mean[1] < 0:
        primary = quad4_centers
        primary_quadrant = 4
    else:
        # Protect against edge case (0,0)
        primary = quad1_centers
        primary_quadrant = 1

    # Try preferred center first
    available = [center for center in primary if center not in previous_centers]

    if not available:
        _extend_quadrant_centers(primary, primary_quadrant)
        available = [center for center in primary if center not in previous_centers]

    if available:
        cens = np.array(available)
        differences = np.linalg.norm(cens - avg, axis=1)
        return available[int(np.argmin(differences))]

    # If preferred is exhausted, look to next nearest center
    all_centers = quad1_centers + quad2_centers + quad3_centers + quad4_centers
    available = [center for center in all_centers if center not in previous_centers]
    if not available:
        raise ValueError("No centers remain in any quadrant")

    cens = np.array(available)
    differences = list(np.linalg.norm(cens - avg, axis=1))

    return available[int(np.argmin(differences))]
    
def check_cycle_direction(coords, points, center):
    # check the rotational direction of the existing points
    
    cen = np.array(center)
    angle_sum = 0

    # check angle between subsequent points using dot product, check direction with cross product.
    for i in range(0, len(points)-1):
        v1 = np.array(coords[points[i]]) - cen
        v2 = np.array(coords[points[i+1]]) - cen
        dot_product = np.dot(v1,v2)
        magnitude_v1 = np.linalg.norm(v1)
        magnitude_v2 = np.linalg.norm(v2)
        cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
        angle = np.arccos(cos_theta)
        cross_product = v1[0] * v2[1] - v1[1] * v2[0]
        if cross_product < 0:
            angle = -angle
        angle_sum += angle #sum angles from dot product corrected for direction
        
    # return rotational direction of points based on the summed angles
    if angle_sum < 0:
        return -1
    else:
        return 1
    
def place_points(cycles):
    """Generates coordinates for points based on cycles."""
    point_list = []
    point_coords = {}
    radius = 1

    new_center = (0,0)
    average = (0,0)
    old_centers = []
    
    for cycle in cycles:
        # determine which points have already been processed (existing_points)
        new_points = [p for p in cycle if p not in point_list]
        existing_points = [p for p in cycle if p in point_list]

        # if no new points to plot, move on to next cycle
        if not new_points:
          continue
      
        # if this is not the first cycle, then choose existing points to calculate mean to choose new center
        if len(existing_points) > 0:
            first_index = None
            last_index = None
            for i, point in enumerate(point_list):
                if point in cycle:
                    if first_index is None:
                        first_index = i
                    last_index = i
            lower = point_list[first_index - 1]
            upper = point_list[last_index + 1] if last_index < len(point_list)-1 else point_list[0]    
                
            p1 = point_coords[lower]
            p2 = point_coords[upper]
            average = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
            new_center = choose_new_center(average, old_centers)
            
        # if the cycle currently being processed does not use any already processed points, just use the previous mean
        elif len(existing_points) == 0 and len(point_list) > 0:
            new_center = choose_new_center(average, old_centers)
        
        n = len(new_points)
        # determine which direction the existing points circle
        cycle_direction = check_cycle_direction(point_coords, existing_points, new_center)
        # obtain coordinates for the new points
        polygon_coords = generate_polygon_coords(n, average, cycle_direction, radius, center=new_center)

        # Update the lists of coordinates, points, and already-used centers
        for i, point in enumerate(new_points):
                point_coords[point] = polygon_coords[i]
                point_list.append(point)
        old_centers.append(new_center)

    # shift coordinates to avoid negative coordinates
    minx = min(point_coords.values(), key=lambda point_coords: point_coords[0])[0]
    miny = min(point_coords.values(), key=lambda point_coords: point_coords[1])[1]
    for i in point_coords:
        point_coords[i] = (point_coords[i][0] - minx, point_coords[i][1] - miny)
        #print(f"{i}, {point_coords[i][0]}, {point_coords[i][1]}")
    
    # return coordinates for all the points in the processed cycles
    return point_coords

