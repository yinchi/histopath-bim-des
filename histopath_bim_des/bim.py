"""Runner-related model parameters."""

import re
from dataclasses import dataclass
from functools import reduce
from itertools import islice, product
from os import PathLike
from typing import Self

import ifcopenshell as ifc
import matplotlib.axes
import natsort
import networkx as ntx
import numpy as np
import pandas as pd
import shapely as shp
from ifcopenshell import geom as ifc_geom
from ifcopenshell.util import shape as ifc_shape
from shapely.plotting import plot_polygon

from .config.runners import RunnerConfig

settings = ifc_geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)  # Find global coordinates


@dataclass
class BimModel:
    """Representation of the histopathology lab's BIM data."""

    elevations: dict[str, float]
    """Elevation of each building storey, in metres."""

    doors: pd.DataFrame
    """Dataframe of door coordinate data."""

    walls: pd.DataFrame
    """Dataframe of wall coordinate data."""

    @staticmethod
    def from_ifc(path: PathLike, door_filter: str = r'd\d+$') -> Self:
        """Parse an Industry Foundation Model file
        representation of the histopathology lab."""
        ifc_file = ifc.open(path)

        # Get the list of elevations for each Storey in the IFC file.
        # Our IFC file is known to express elevation in mm, convert to m.
        elevations: dict[str, float] = reduce(
            lambda d1, d2: d1 | d2,
            map(
                lambda s: {s.Name: s.Elevation/1000.0},
                ifc_file.by_type("ifcBuildingStorey")
            )
        )

        # Get the name of an IFC object; works for walls and doors
        # in the current IFC file.
        def get_level_name(obj: ifc.entity_instance) -> str:
            return obj.ContainedInStructure[0].RelatingStructure.Name

        # Get the bounding box of an IFC object; for our IFC file,
        # all walls and doors are aligned to the xyz axes.
        def get_coords(obj: ifc.entity_instance) -> dict[str, float]:
            shape = ifc_geom.create_shape(settings, obj)
            grouped_verts = ifc_shape.get_vertices(shape.geometry)
            return {
                'x0': min(map(lambda xyz: xyz[0], grouped_verts)),
                'y0': min(map(lambda xyz: xyz[1], grouped_verts)),
                'z0': min(map(lambda xyz: xyz[2], grouped_verts)),
                'x1': max(map(lambda xyz: xyz[0], grouped_verts)),
                'y1': max(map(lambda xyz: xyz[1], grouped_verts)),
                # 'z1': max(map(lambda xyz: xyz[2], grouped_verts))
            }

        # Extract door data
        doors: list[ifc.entity_instance] = list(
            filter(
                lambda door: bool(re.match(door_filter, door.Name)),
                ifc_file.by_type("IfcDoor")
            )
        )
        doors_coords = [get_coords(door) for door in doors]
        doors_df = pd.DataFrame({
            'door_name': [door.Name for door in doors],
            'floor': [get_level_name(door) for door in doors],
            'x0': [box['x0'] for box in doors_coords],
            'x1': [box['x1'] for box in doors_coords],
            'y0': [box['y0'] for box in doors_coords],
            'y1': [box['y1'] for box in doors_coords],
            'z0': [box['z0'] for box in doors_coords],
            # 'z1': [box['z1'] for box in doors_coords]
        })\
            .sort_values(
            by='door_name',
            key=natsort.natsort_keygen()
        )\
            .reset_index(drop=True)

        # Extract wall data
        walls = ifc_file.by_type("IfcWall")
        wall_coords = [get_coords(wall) for wall in walls]
        walls_df = pd.DataFrame({
            'wall_name': [wall.Name for wall in walls],
            'floor': [get_level_name(wall) for wall in walls],
            'x0': [box['x0'] for box in wall_coords],
            'x1': [box['x1'] for box in wall_coords],
            'y0': [box['y0'] for box in wall_coords],
            'y1': [box['y1'] for box in wall_coords],
            'z0': [box['z0'] for box in wall_coords],
            # 'z1': [box['z1'] for box in wall_coords]
        })

        return BimModel(
            elevations=elevations,
            doors=doors_df,
            walls=walls_df
        )

    def to_shapely(self, level: int) -> 'ShapelyModel':
        """Returns a Shapely representation of a
        floor in the `BimModel`.

        Args:
            level: Level number of the floor.

        Returns:
            Shapely representation of the selected floor, where all doors and walls
            are represented as `shapely.Polygon` instances.
        """
        wall_shapes = [
            shp.box(wall.x0, wall.y0, wall.x1, wall.y1, ccw=False)
            for wall in self.walls.loc[
                self.walls.floor.str.contains(f'Level {level}')
            ].itertuples()
        ]

        door_shapes = {
            door.door_name: shp.box(
                door.x0, door.y0, door.x1, door.y1, ccw=False
            )
            for door in self.doors.loc[
                self.doors.floor.str.contains(f'Level {level}')
            ].itertuples()
        }

        for s in wall_shapes:
            shp.prepare(s)
        for s in door_shapes.values():
            shp.prepare(s)

        return ShapelyModel(wall_shapes, door_shapes)


@dataclass
class ShapelyModel:
    """Shapely representation of a floor in the histopathology lab.
    All doors and walls are represented as `shapely.Polygon` instances.
    """
    wall_shapes: list[shp.Polygon]
    door_shapes: dict[str, shp.Polygon]

    def is_valid_box(
        self,
        box: shp.Polygon,
        ok_doors: list[str]
    ):
        """Determines if box intersects with a wall or door
        except for `ok_doors`. `ok_doors` will typically be the
        source and destination doors of a shortest-path algorithm.

        Args:
            box: The box to check against the current model.
            ok_doors: A list of doors to ignore when checking for intersections.
        """

        # Since all doors are within walls, we only need to check the
        # ok_doors as special cases

        ok_door_shapes = [self.door_shapes[x] for x in ok_doors]
        shp.prepare(box)
        if any(box.intersects(ok_door_shapes)):
            # Intersects with door in ok_doors
            return True, 'ok_door'
        if any(box.intersects(self.wall_shapes)):
            # Intersects with wall
            return False, 'wall'
        return True, 'empty'

    def shortest_path(
        self,
        from_door: str,
        to_door: str,
        grid_size: float = 0.5,
        bottom_left: tuple[float, float] = (30, 45),
        top_right: tuple[float, float] = (90, 70)
    ) -> ntx.Graph:
        """Find the shortest path between two doors in the model.
        A reasonable search box has been provided for the current study
        (the histopathology lab at Addenbrooke's Hospital, Cambridge, UK).

        Args:
            from_door: Starting door on the path.
            to_door: Destination door on the path.
            grid_size: Grid size for pathfinding algorithm, in metres. Defaults to 0.5.
            bottom_left:
                Bottom-left coordinate for pathfinding algorithm, in metres. Defaults to (30, 45).
            top_right:
                Top-right coordinate for pathfinding algorithm, in metres. Defaults to (90,70).

        Raises:
            networkx.NetworkXNoPath:
                If no path exists between `from_door` and `to_door` without
                passing through a wall or another door.
        """
        # Get grid dimensions (nX, nY)
        x_min, y_min = bottom_left
        x_max, y_max = top_right
        n_x = len(np.arange(x_min, x_max, grid_size))
        n_y = len(np.arange(y_min, y_max, grid_size))

        # Create base grid, assigning 'box' and 'pos' attributes
        # to each node
        grid = ntx.grid_2d_graph(n_x, n_y)
        for i, j in grid.nodes:
            x0 = x_min + i*grid_size
            y0 = y_min + j*grid_size
            grid.nodes[(i, j)]['box'] = shp.box(
                x0, y0, x0+grid_size, y0+grid_size, ccw=False
            )
            shp.prepare(grid.nodes[(i, j)]['box'])
            centroid = grid.nodes[(i, j)]['box'].centroid
            grid.nodes[(i, j)]['pos'] = (centroid.x, centroid.y)

        # Select valid nodes for subgraph
        selected_nodes = [
            n for n, v in grid.nodes(data=True)
            if self.is_valid_box(
                v['box'],
                ok_doors=[from_door, to_door]
            )[0]
        ]
        grid2 = ntx.Graph(grid.subgraph(selected_nodes))

        # Add diagonals to grid2 within each complete "box" of 4 edges
        for _, _, v in grid2.edges(data=True):
            v['weight'] = 1.0

        for x, y in grid2.nodes:
            # northeast direction
            if (
                (x+1, y) in grid2.nodes
                and (x, y+1) in grid2.nodes
                and (x+1, y+1) in grid2.nodes
            ):
                grid2.add_edge((x, y), (x+1, y+1), weight=2**0.5)

            # southeast direction
            if (
                (x+1, y) in grid2.nodes
                and (x, y-1) in grid2.nodes
                and (x+1, y-1) in grid2.nodes
            ):
                grid2.add_edge((x, y), (x+1, y-1), weight=2**0.5)

        # Get node indexes for from_door and to_door
        from_node = [
            n for n, v in grid.nodes(data=True)
            if v['box'].intersects(self.door_shapes[from_door].centroid)
        ][0]
        to_node = [
            n for n, v in grid.nodes(data=True)
            if v['box'].intersects(self.door_shapes[to_door].centroid)
        ][0]

        path_nodes = ntx.shortest_path(
            grid2, from_node, to_node, weight='weight'
        )
        path_edges = list(zip(path_nodes[:-1], path_nodes[1:]))
        path_graph = ntx.Graph()
        for i, n in enumerate(path_nodes):
            path_graph.add_node(i, pos=grid2.nodes(data=True)[n]['pos'])
        for i, e in enumerate(path_edges):
            path_graph.add_edge(i, i+1, weight=grid2.edges[e]['weight'])

        path_length = ntx.shortest_path_length(
            grid2, from_node, to_node, weight='weight'
        ) * grid_size

        return path_length, path_graph

    def plot_floor(
        self,
        ax: matplotlib.axes.Axes,
        title: str,
        bottom_left: tuple[float, float] = (30, 45),
        top_right: tuple[float, float] = (100, 80)
    ):
        """Plots the floor model using Matplotlib. Reasonable axis limits
        have been provided for the current study (the histopathology lab at
        Addenbrooke's Hospital, Cambridge, UK).

        Args:
            ax: The Axes object to plot to.
            title: The plot title.
            bottom_left:
                Bottom left corner of plot. Defaults to (30, 45), corresponding
                to metres in the floor plan.
            top_right:
                Top right corner of plot. Defaults to (100, 80), corresponding
                to metres in the floor plan.
        """
        for p in self.wall_shapes:
            plot_polygon(
                p, ax, facecolor='gray',
                add_points=False, linewidth=0
            )
        for n, p in self.door_shapes.items():
            plot_polygon(
                p, ax, facecolor='red',
                add_points=False, linewidth=0
            )
            ax.text(p.centroid.x, p.centroid.y, n, color='red')
        ax.axis('square')
        x0, y0 = bottom_left
        x1, y1 = top_right
        ax.set_xlim((x0, x1))
        ax.set_ylim((y0, y1))
        ax.set_title(title)


def logical_graph(
    model: ShapelyModel,
    speed: float | None = 1.2
) -> ntx.Graph:
    """Construct a logical graph representation of the floor model,
    with nodes representing doors and edge weights representing travel
    times in seconds.

    Args:
        speed: Runner speed in m/s. Defaults to 1.2.

    Returns:
        The logical graph for the given floor model.
    """
    graph = ntx.Graph()
    keys = list(model.door_shapes.keys())
    graph.add_nodes_from(keys)
    for i, k1 in enumerate(keys):
        for _, k2 in islice(enumerate(keys), i+1, None):
            try:
                path_len, _ = model.shortest_path(k1, k2)
                graph.add_edge(k1, k2, weight=path_len/speed)  # weight = runner_time
            except ntx.NetworkXNoPath:
                continue
    return graph


def runner_times(
    model: BimModel,
    cfg: RunnerConfig
) -> dict[tuple[str, str], float]:
    """Compute runner times between process stages in the
    histopathology model.

    Args:
        model: BIM model representation of the histopathology lab.
        config: Dataclass containing runner parameters.

    Returns:
        Maps pairs of process stages to the time (in seconds) required to travel between them.
    """

    # Find all the levels containing doors of interest
    target_levels = [re.match(r'Level (\d+)', s).group(1) for s in model.doors.floor.unique()]

    # Build the logical graph for each target level and compose them
    logical_graphs = {
        level: logical_graph(model.to_shapely(level=level), speed=cfg.runner_speed)
        for level in target_levels
    }
    full_logical_graph = ntx.compose_all(logical_graphs.values())

    # Add extra paths between levels
    for path in cfg.extra_paths:
        full_logical_graph.add_edge(
            *path.path,
            weight=path.duration_seconds
        )

    d = cfg.door_map.model_dump()
    k = list(d.keys())
    pairs = list(zip(k, k[1:]))

    ret = {}
    for u, v in pairs:
        if 'cutup' in (u, v):
            # encapsulate single strings in a list as necessary
            du = d[u] if u == 'cutup' else [d[u]]
            dv = d[v] if v == 'cutup' else [d[v]]

            # compute the average runner time for all cutup rooms
            ret[(u, v)] = np.average(
                [
                    ntx.shortest_path_length(
                        full_logical_graph, d1, d2, weight='weight'
                    ) for d1, d2 in product(du, dv)
                ],
                weights=cfg.cutup_dist
            )
        else:
            ret[(u, v)] = ntx.shortest_path_length(
                full_logical_graph, d[u], d[v], weight='weight'
            )
    return ret
