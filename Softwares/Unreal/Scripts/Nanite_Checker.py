import unreal

def enable_nanite_for_all_meshes():
    # Get all actors using EditorLevelLibrary
    editor_level_lib = unreal.EditorLevelLibrary()
    all_actors = editor_level_lib.get_all_level_actors()
    
    if len(all_actors) == 0:
        unreal.log_warning("No actors in the level.")
        return
        
    unreal.log(f"Processing all meshes in {len(all_actors)} actors.")
    
    # Keep track of actions
    enabled_count = 0
    already_enabled_count = 0
    
    for actor in all_actors:
        # Process static mesh components
        static_components = actor.get_components_by_class(unreal.StaticMeshComponent)
        for component in static_components:
            if hasattr(component, 'disallow_nanite'):
                current_value = component.get_editor_property('disallow_nanite')
                if current_value:
                    component.set_editor_property('disallow_nanite', False)
                    unreal.log(f"Enabled Nanite for StaticMesh: {actor.get_actor_label()}")
                    enabled_count += 1
                else:
                    already_enabled_count += 1
        
        # Process skeletal mesh components
        skeletal_components = actor.get_components_by_class(unreal.SkeletalMeshComponent)
        for component in skeletal_components:
            if hasattr(component, 'disallow_nanite'):
                current_value = component.get_editor_property('disallow_nanite')
                if current_value:
                    component.set_editor_property('disallow_nanite', False)
                    unreal.log(f"Enabled Nanite for SkeletalMesh: {actor.get_actor_label()}")
                    enabled_count += 1
                else:
                    already_enabled_count += 1
    
    unreal.log(f"Nanite enabled for {enabled_count} components. {already_enabled_count} components already had Nanite enabled.")

# Execute the function
enable_nanite_for_all_meshes()