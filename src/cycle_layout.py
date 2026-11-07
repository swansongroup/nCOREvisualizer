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
import math

EPS = 1e-12

def _ring_positions(radius):
    count = 4 * (int(round(radius))+1) -4

    theta = np.linspace(
        0.0,
        2.0* np.pi,
        count,
        endpoint=False
                        )

    return [
        (
            float(radius * np.cos(angle)),
            float(radius * np.sin(angle))
        )
        for angle in theta
    ]

def _ensure_rings(rings, count, ring_step):
    while len(rings) < count:
        radius = ring_step * (len(rings) + 1)
        rings.append(_ring_positions(radius))

def _regular_polygon(n, center=(0.0, 0.0), radius=1.0):
    center = np.asarray(center, dtype=float)

    theta = np.linspace(
        0.0,
        2.0 * np.pi,
        n,
        endpoint=False
    )

    xy = center + radius * np.column_stack(
        (
            np.cos(theta),
            np.sin(theta)
        )
    )

    return [tuple(point) for point in xy]

def _open_polygon(n, center, reference, radius=1.0, gap_angle=np.pi/ 2.0):
    center = np.asarray(center, dtype=float)
    reference = np.asarray(reference, dtype=float)
    vector = reference - center

    if np.linalg.norm(vector) < EPS:
        vector = np.array([-1.0, 0.0])

    offset = np.arctan2(vector[1], vector[0])

    if n == 1:
        theta = np.array([
            offset + np.pi
        ])

    else:
        theta = np.linspace(
            offset + gap_angle / 2.0,
            offset + 2.0 * np.pi - gap_angle / 2.0,
            n, 
            endpoint=True
        )

    xy = center + radius * np.column_stack(
        (
            np.cos(theta),
            np.sin(theta)
        )
    )

    return [tuple(point) for point in xy]

def _graph_centroid(coords):
    return np.mean(
        np.asarray(
            list(coords.values()),
            dtype=float
        ),
        axis = 0
    )

def _unit(vector, fallback=(1.0,0.0)):
    vector = np.asarray(vector, dtype=float)
    magnitude = np.linalg.norm(vector)

    if magnitude < EPS:
        vector = np.asarray(
            fallback,
            dtype=float,
        )
        magnitude = np.linalg.norm(vector)

    return vector / magnitude

def _points_clear(points, coords, min_clearance):
    if not coords or min_clearance <= 0.0:
        return True

    placed = np.asarray(
        list(coords.values()),
        dtype=float
    )

    for point in points:
        point = np.asarray(
            point,
            dtype=float
        )

        distances = np.linalg.norm(
            placed - point,
            axis =1
        )

        if np.any(distances < min_clearance):
            return False

    return True

def _side_of_line(
        point,
        start,
        end
):

    point = np.asarray(point, dtype=float)
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)

    edge = end - start
    relative = point - start

    return float(
        edge[0] * relative[1] - edge[1] * relative[0]
    )

def _distance_to_segment(point, start, end):

    point = np.asarray(point, dtype=float)
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)

    segment = end - start 
    length_squared = float(np.dot(segment, segment))

    if length_squared < EPS:
        return float(np.linalg.norm(point - start))

    projection = float(
        np.dot(point - start, segment) / length_squared)

    projection = float(np.clip(projection, 0.0, 1.0))

    closest = start + projection * segment

    return float(np.linalg.norm(point - closest))

def _outward_side(start, end, coords):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)

    edge = end - start

    if np.linalg.norm(edge) < EPS:
        return 1

    midpoint = 0.5 * (start + end)
    outward = midpoint - _graph_centroid(coords)

    left_normal = np.array([
        -edge[1], edge[0]
    ])

    if np.dot(left_normal, outward) >= 0.0:
        return 1
    return -1

def _weighted_open_side(left_anchor, right_anchor, coords, decay_length):
    start = coords[left_anchor]
    end = coords[right_anchor]

    positive_occupancy = 0.0
    negative_occupancy = 0.0

    for vertex, point in coords.items():
        if vertex in (left_anchor, right_anchor):
            continue

        side = _side_of_line(point, start, end)

        if abs(side) < EPS:
            continue

        distance = _distance_to_segment(point, start, end)

        weight = float(np.exp(-distance/decay_length))

        if side > 0.0: 
            positive_occupancy += weight
        else:
            negative_occupancy += weight

    if positive_occupancy < negative_occupancy:
        return 1

    if negative_occupancy < positive_occupancy:
        return -1

    return _outward_side(start, end, coords)

def _new_segments(cycle, coords):
    existing_indices = [index for index, vertex in enumerate(cycle) if vertex in coords]
    segments = []

    for position, left_index in enumerate(existing_indices):

        right_index = existing_indices[
            (position + 1) % len(existing_indices)
        ]

        new_vertices = []
        index = (left_index + 1) % len(cycle)

        while index != right_index:
            new_vertices.append(cycle[index])

            index = (index + 1) % len(cycle)

        if new_vertices:
            segments.append((cycle[left_index], new_vertices, cycle[right_index]))

    return segments

def _has_one_shared_edge(cycle, coords):
    indices = [index for index, vertex in enumerate(cycle) if vertex in coords]

    if len(indices) != 2:
        return False

    first, second = indices
    cycle_length = len(cycle)

    return (
        (first + 1) % cycle_length == second or (second + 1) % cycle_length == first
    )

def _path_length(start, points, end):
    chain = [np.asarray(
        start, dtype=float
    )]

    chain.extend(np.asarray(point, dtype=float) for point in points)

    chain.append(np.asarray(end, dtype=float))

    return float(
        sum(
            np.linalg.norm(
                point_b - point_a
            )
            for point_a, point_b in zip(chain, chain[1:])
        )
    )

def _find_free_center(
    coords,
    rings,
    used_centers,
    ring_step,
    max_rings,
    build_points,
    min_clearance,
    target=None,
    outward=None,
    anchor=None
):
    if target is None:
        initial_ring_count = 1
    else:
        target = np.asarray(target, dtype=float)
        initial_ring_count = max(
            1,
            int(
                math.ceil(np.linalg.norm(target) / ring_step)
            ) + 1
        )
    if outward is not None:
        outward = _unit(outward)

        anchor = np.asarray(anchor, dtype=float)

    _ensure_rings(rings, initial_ring_count, ring_step)

    while True:
        candidates = []
        for ring_index, ring in enumerate(rings):
            for point_index, center in enumerate(ring):
                if center in used_centers:
                    continue
                center_array = np.asarray(center, dtype=float)

                if outward is not None:
                    displacement = (center_array - anchor)

                    if np.dot(displacement, outward) <= 0.0:
                        continue

                if not _points_clear(
                    [center_array], coords, min_clearance
                ):
                    continue

                proposed = build_points(center_array)

                if not _points_clear(proposed, coords, min_clearance):
                    continue

                if target is None:
                    score = (ring_index, point_index)

                else:
                    score = (float(np.linalg.norm(center_array - target)), ring_index, point_index)
                candidates.append(
                    (
                        score,
                        center
                    )
                )
        if candidates:
            _, selected_center = min(candidates, key=lambda item: item[0])
            used_centers.add(selected_center)

            return selected_center
        if len(rings) >= max_rings:
            raise RuntimeError("No free polygon center could be found")

        _ensure_rings(rings, len(rings) + 1, ring_step)

def _best_segment_group(count, start, end, preferred_side, coords, rings, ring_step, min_clearance, max_rings):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)

    degenerate_anchors = (np.linalg.norm(end - start) < EPS)

    current_extent = max(
        (
            np.linalg.norm(np.asarray(point, dtype=float)) for point in coords.values()
        ),
        default=0.0
    )

    initial_ring_count = max(1, int(math.ceil(current_extent / ring_step)) + 1)

    _ensure_rings(rings, initial_ring_count, ring_step)

    while True:
        best = None
        
        for ring_index, ring in enumerate(rings):
            if count > len(ring):
                continue

            for window_start in range(len(ring)):

                group = [ring[(window_start + offset) % len(ring)] for offset in range(count)]

                if not _points_clear(group, coords, min_clearance):
                    continue

                if (not degenerate_anchors and any(preferred_side * _side_of_line(point, start, end) <= EPS for point in group)):
                    continue

                reverse_group = list(reversed(group))

                forward_cost = _path_length(start, group, end)

                reverse_cost = _path_length(start, reverse_group, end)

                if reverse_cost < forward_cost:
                    ordered_group = reverse_group
                    cost = reverse_cost
                else:
                    ordered_group = group
                    cost = forward_cost

                candidate_key = (cost, ring_index, window_start)

                if (best is None or candidate_key < best[0]):
                    best = (candidate_key, ordered_group)

        if best is not None:       
            return best[1]
        
        if len(rings) >= max_rings:
            raise RuntimeError("No contigous candidate group could be found for an unplaced segment")

        _ensure_rings(rings, len(rings)+ 1, ring_step)

def place_points_method2(
        cycles,
        ring_step=2.0,
        polygon_radius=1.0,
        center_spacing=2.0,
        decay_length=2.0,
        gap_angle=np.pi / 2.0,
        min_clearance=0.25,
        max_rings=100
):
    if ring_step <= 0.0:
        raise ValueError("ring_step must be positive")


    if polygon_radius <= 0.0:
        raise ValueError(
            "polygon_radius must be positive"
        )

    if center_spacing <= 0.0:
        raise ValueError(
            "center_spacing must be positive"
        )

    if decay_length <= 0.0:
        raise ValueError(
            "decay_length must be positive"
        )

    if min_clearance < 0.0:
        raise ValueError(
            "min_clearance cannot be negative"
        )

    if max_rings < 1:
        raise ValueError(
            "max_rings must be at least 1"
        )

    coords = {}
    rings = []
    used_centers = set()

    for raw_cycle in cycles:
        cycle = list(raw_cycle)

        if not cycle:
            continue

        if len(set(cycle)) != len(cycle):
            raise ValueError("Each cycle must list each vertex once; closure is implied")

        existing = [vertex for vertex in cycle if vertex in coords]
        new_vertices = [vertex for vertex in cycle if vertex not in coords]

        # if doesn't contribute new verts
        if not new_vertices:
            continue

        if len(existing) == 0:
            if not coords:
                center = (0.0,0.0) # first cycle
            else:

                def build_polygon(candidate_center):
                    return _regular_polygon(len(cycle), candidate_center, polygon_radius)

                center = _find_free_center(
                    coords=coords,
                    rings=rings,
                    used_centers=used_centers,
                    ring_step=ring_step,
                    max_rings=max_rings,
                    build_points=build_polygon,
                    min_clearance=min_clearance)

            points = _regular_polygon(len(cycle), center, polygon_radius)

            coords.update(dict(zip(cycle, points)))

            continue

        # case 2 where exactly one previously placed vertex exists
        if len(existing) == 1:
            anchor = existing[0]
            anchor_index = cycle.index(anchor)

            ordered_new = (cycle[anchor_index + 1:] + cycle[:anchor_index])
            anchor_point = np.asarray(
                coords[anchor], dtype=float
            )

            graph_center = _graph_centroid(coords)

            outward = _unit(
                anchor_point - graph_center
            )

            target = (
                anchor_point
                + center_spacing * outward
            )

            def build_open_polygon(candidate_center):
                return _open_polygon(
                    len(ordered_new),
                    candidate_center,
                    anchor_point,
                    polygon_radius,
                    gap_angle
                )

            center = _find_free_center(
                coords=coords,
                rings=rings,
                used_centers=used_centers,
                ring_step=ring_step,
                max_rings=max_rings,
                build_points=build_open_polygon,
                min_clearance=min_clearance,
                target=target,
                outward=outward,
                anchor=anchor_point
            )

            points = build_open_polygon(
                center
            )

            coords.update(
                dict(
                    zip(
                        ordered_new,
                        points
                    )
                )
            )

            continue

        # Case 3 where exacly one shared edge exists. Use midpoint as ref and build facing outward
        if _has_one_shared_edge(cycle, coords):
            segments = _new_segments(cycle, coords)

            (
                left_anchor, segment, right_anchor
            ) = segments[0]

            start = np.asarray(coords[left_anchor], dtype=float)
            end = np.asarray(coords[right_anchor], dtype=float)
            reference = 0.5 * (start + end)
            graph_center = _graph_centroid(coords)
            outward = _unit(reference - graph_center)
            target = (reference + center_spacing * outward)

            def build_shared_edge_polygon(candidate_center):
                return _open_polygon(
                    len(segment),
                    candidate_center,
                    reference,
                    polygon_radius,
                    gap_angle
                )

            center = _find_free_center(
                coords=coords,
                rings=rings,
                used_centers=used_centers,
                ring_step=ring_step,
                max_rings=max_rings,
                build_points=build_shared_edge_polygon,
                min_clearance=min_clearance,
                target=target,
                outward=outward,
                anchor=reference
            )

            points = build_shared_edge_polygon(center)

            # The geometric point set is fixed, but the segment can
            # be assigned in either traversal direction.
            reverse_points = list(reversed(points))

            forward_cost = _path_length(start, points, end)

            reverse_cost = _path_length(start, reverse_points, end)

            if reverse_cost < forward_cost:
                points = reverse_points

            coords.update(dict(zip(segment, points)))

            continue

        # Case 4: Anything more complicated than the above 3 cases
        segments = _new_segments(cycle, coords)

        for (left_anchor, segment, right_anchor) in segments:
            start = coords[left_anchor]
            end = coords[right_anchor]

            preferred_side = _weighted_open_side(left_anchor, right_anchor, coords, decay_length)

            points = _best_segment_group(
                count=len(segment),
                start=start,
                end=end,
                preferred_side=preferred_side,
                coords=coords,
                rings=rings,
                ring_step=ring_step,
                min_clearance=min_clearance,
                max_rings=max_rings
            )

            coords.update(dict(zip(segment, points)))

    if not coords:
        return {}
    
    minimum = np.min(np.asarray(list(coords.values()), dtype=float), axis=0)

    return {
        vertex: tuple(np.asarray(point, dtype=float) - minimum)
        for vertex, point in coords.items()
    }