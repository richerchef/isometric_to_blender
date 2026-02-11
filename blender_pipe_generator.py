import bpy
import csv
import mathutils

# CONFIGURATION
FILE_PATH = r"C:\Users\riche\OneDrive\Desktop\work sandpits\Pipe generator viewer\coordinates\pipe_export.csv"
SCALE = 0.001  
ELBOW_FACTOR = 1.5 

def create_straight_pipe(name, start, end, radius):
    vec = end - start
    dist = vec.length
    if dist < 0.0001: return # Ignore zero-length segments
    
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
    
    # Start Point
    p0 = polyline.bezier_points[0]
    p0.co = p_start
    p0.handle_right = center 
    p0.handle_left_type = 'FREE'
    
    # End Point
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
            nodes[name] = {
                'pos': mathutils.Vector((float(row['X']), float(row['Y']), float(row['Z']))) * SCALE,
                'prev': row['PreviousNode'].strip(),
                'radius': (float(row['Dimension']) / 2) * SCALE,
                'next': []
            }

    for name, data in nodes.items():
        if data['prev'] in nodes:
            nodes[data['prev']]['next'].append(name)

    for name, data in nodes.items():
        if not data['prev'] or data['prev'] not in nodes: continue
        
        node_curr = data
        node_prev = nodes[data['prev']]
        vec_to_curr = (node_curr['pos'] - node_prev['pos']).normalized()
        
        # --- BEND DETECTION ---
        has_bend_at_start = False
        if node_prev['prev'] in nodes:
            node_gp = nodes[node_prev['prev']]
            vec_in = (node_prev['pos'] - node_gp['pos']).normalized()
            # If the angle is significant (> 1 degree), create a bend
            if vec_in.dot(vec_to_curr) < 0.999:
                has_bend_at_start = True
                create_elbow_curve(name, node_prev['pos'], vec_in, vec_to_curr, node_curr['radius'])

        has_bend_at_end = False
        if node_curr['next']:
            # For simplicity, we check the first child to see if the pipe turns
            next_node = nodes[node_curr['next'][0]]
            vec_out = (next_node['pos'] - node_curr['pos']).normalized()
            if vec_to_curr.dot(vec_out) < 0.999:
                has_bend_at_end = True

        # --- RUN CALCULATION ---
        take_off = node_curr['radius'] * ELBOW_FACTOR
        
        # Only shorten the start if there was a bend at the previous node
        run_start = node_prev['pos'] + (vec_to_curr * take_off) if has_bend_at_start else node_prev['pos']
        
        # Only shorten the end if there is a bend at the current node
        run_end = node_curr['pos'] - (vec_to_curr * take_off) if has_bend_at_end else node_curr['pos']
        
        create_straight_pipe(name, run_start, run_end, node_curr['radius'])

run_pipe_generator()