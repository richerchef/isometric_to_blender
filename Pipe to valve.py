import bpy
import bmesh
from mathutils import Vector

# ---------------------------------------------------
# SETTINGS
# ---------------------------------------------------

TARGET_KEYWORDS = ["pipe", "run", "cyl"]
TARGET_COLLECTION_NAME = "Valves"

# ---------------------------------------------------
# CREATE COLLECTION
# ---------------------------------------------------

if TARGET_COLLECTION_NAME not in bpy.data.collections:
    new_col = bpy.data.collections.new(TARGET_COLLECTION_NAME)
    bpy.context.scene.collection.children.link(new_col)

target_collection = bpy.data.collections[TARGET_COLLECTION_NAME]

# ---------------------------------------------------
# VALVE GENERATOR
# ---------------------------------------------------

def create_procedural_valve(length=2.0, radius=0.5):

    # Main valve body (two cones tip to tip)
    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=radius,
        radius2=0,
        depth=length/2,
        location=(0, 0, length/4)
    )
    cone1 = bpy.context.active_object

    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=radius,
        radius2=0,
        depth=length/2,
        location=(0, 0, -length/4),
        rotation=(3.14159, 0, 0)
    )
    cone2 = bpy.context.active_object

    # Stem
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=radius * 0.2,
        depth=radius * 3,
        location=(0, 0, 0)
    )
    stem = bpy.context.active_object

    # Handle
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=radius * 0.1,
        depth=radius * 4,
        location=(0, 0, radius * 1.5),
        rotation=(0, 1.5708, 0)
    )
    handle = bpy.context.active_object

    # Join all parts
    bpy.ops.object.select_all(action='DESELECT')
    cone1.select_set(True)
    cone2.select_set(True)
    stem.select_set(True)
    handle.select_set(True)
    bpy.context.view_layer.objects.active = cone1
    bpy.ops.object.join()

    valve = bpy.context.active_object
    valve.name = "ProceduralValve"

    return valve


# ---------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------

for obj in list(bpy.context.scene.objects):

    if obj.type != 'MESH':
        continue

    if not any(k.lower() in obj.name.lower() for k in TARGET_KEYWORDS):
        continue

    print(f"Replacing: {obj.name}")

    location = obj.location.copy()
    rotation = obj.rotation_euler.copy()
    dimensions = obj.dimensions.copy()

    pipe_length = dimensions.z
    pipe_radius = dimensions.x / 2

    # Create valve
    valve = create_procedural_valve(length=pipe_length, radius=pipe_radius)

    # Link to collection
    target_collection.objects.link(valve)
    bpy.context.scene.collection.objects.unlink(valve)

    # Match transform
    valve.location = location
    valve.rotation_euler = rotation

    # Delete original pipe
    bpy.data.objects.remove(obj, do_unlink=True)

print("All pipes replaced with procedural valves.")
