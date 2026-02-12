import bpy
import csv
import mathutils
import re

# CONFIGURATION
FILE_PATH = r"C:\Users\riche\OneDrive\Desktop\work sandpits\Pipe generator viewer\coordinates\pipework_nodes.csv"
SCALE = 0.001  
ELBOW_FACTOR = 1.5 

def parse_anchor(s):
    """Checks if 'PreviousNode' is a coordinate anchor like (500, 500, 0)"""
    if not s or not s.startswith('('): return None
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", s)
    return mathutils.Vector((float(nums[0]), float(nums[1]), float(nums[2]))) if len(nums) == 3 else None

def create_straight_pipe(name, start, end, radius):
    vec = end - start
    dist = vec.length
    if dist < 0.0001: return 
    
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=dist, vertices=32)
    pipe = bpy.context.object
    pipe.name = f"Run_{name}"
    pipe.location = (start + end) / 2
    pipe.rotation_mode = 'QUATERNION'
    pipe.rotation_quaternion = vec.to_track_quat('Z', 'Y')

def create_elbow_curve(name, center, vec_in, vec_out, radius):
    take_off = radius * ELBOW_FACTOR
    p_start = center - (vec_in * take_off)
    p_end = center + (vec_out * take_off)
    
    curve_data = bpy.data.curves.new(name=f"ElbowCurve_{name}", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.fill_mode = 'FULL'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 6
    
    polyline = curve_data.splines.new('BEZIER')
    polyline.bezier_points.add(1)
    
    p0 = polyline.bezier_points[0]
    p0.co = p_start
    p0.handle_right = center 
    p0.handle_left_type = 'FREE'
    
    p1 = polyline.bezier_points[1]
    p1.co = p_end
    p1.handle_left = center
    p1.handle_right_type = 'FREE'
    
    obj = bpy.data.objects.new(f"Elbow_{name}", curve_data)
    bpy.context.collection.objects.link(obj)

def run_pipe_generator():
    if bpy.context.object and bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    nodes = {}
    
    with open(FILE_PATH, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['NodeName'].strip()
            prev_str = row['PreviousNode'].strip()
            
            # Get Vector Deltas
            dv = mathutils.Vector((float(row['X']), float(row['Y']), float(row['Z']))) * SCALE
            radius = (float(row['Dimension']) / 2) * SCALE
            
            # COORDINATE CALCULATION
            anchor = parse_anchor(prev_str)
            
            if anchor:
                # Start new run at anchor location
                abs_pos = (anchor * SCALE) + dv
            elif prev_str in nodes:
                # Continue from previous node's absolute position
                abs_pos = nodes[prev_str]['pos'] + dv
            else:
                # Fallback for first node of file with no anchor
                abs_pos = dv

            nodes[name] = {
                'pos': abs_pos,
                'prev': prev_str,
                'radius': radius,
                'next': []
            }

    # Rest of your elbow/pipe logic remains exactly the same
    for name, data in nodes.items():
        if data['prev'] in nodes:
            nodes[data['prev']]['next'].append(name)

    for name, data in nodes.items():
        if not data['prev'] or data['prev'] not in nodes: continue
        
        node_curr = data
        node_prev = nodes[data['prev']]
        vec_to_curr = (node_curr['pos'] - node_prev['pos']).normalized()
        
        has_bend_at_start = False
        if node_prev['prev'] in nodes:
            node_gp = nodes[node_prev['prev']]
            vec_in = (node_prev['pos'] - node_gp['pos']).normalized()
            if vec_in.dot(vec_to_curr) < 0.999:
                has_bend_at_start = True
                create_elbow_curve(name, node_prev['pos'], vec_in, vec_to_curr, node_curr['radius'])

        has_bend_at_end = False
        if node_curr['next']:
            next_node = nodes[node_curr['next'][0]]
            vec_out = (next_node['pos'] - node_curr['pos']).normalized()
            if vec_to_curr.dot(vec_out) < 0.999:
                has_bend_at_end = True

        take_off = node_curr['radius'] * ELBOW_FACTOR
        run_start = node_prev['pos'] + (vec_to_curr * take_off) if has_bend_at_start else node_prev['pos']
        run_end = node_curr['pos'] - (vec_to_curr * take_off) if has_bend_at_end else node_curr['pos']
        
        create_straight_pipe(name, run_start, run_end, node_curr['radius'])

run_pipe_generator()
