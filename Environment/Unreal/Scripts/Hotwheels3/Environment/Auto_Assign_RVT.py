import unreal

# Access the Editor Actor Subsystem
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Retrieve selected actors in the level editor
selected_actors = actor_subsystem.get_selected_level_actors()

# Load your Runtime Virtual Texture asset
rvt_asset = unreal.load_asset("/Game/assets/graphics/Env/EnvShared/RVT/RVT_World")

# Iterate over selected actors and assign the RVT
for actor in selected_actors:
    # Get the Static Mesh Component (if present)
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp:
        # Assign the RVT to the mesh component
        mesh_comp.set_editor_property("runtime_virtual_textures", [rvt_asset])