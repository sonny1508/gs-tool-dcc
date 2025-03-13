import unreal

def enable_nanite_for_all_actors():
    # Get actors using EditorLevelLibrary
    editor_level_lib = unreal.EditorLevelLibrary()
    all_actors = editor_level_lib.get_all_level_actors()
    selected_actors = editor_level_lib.get_selected_level_actors()
    
    actors_to_process = selected_actors if selected_actors else all_actors
    
    if len(actors_to_process) == 0:
        unreal.log_warning("No actors to process.")
        return
        
    unreal.log(f"Processing {len(actors_to_process)} actors.")
    
    # Keep track of actions
    enabled_count = 0
    already_enabled_count = 0
    
    for actor in actors_to_process:
        # Check if this is a StaticMeshActor
        actor_class_name = actor.get_class().get_name()
        
        if 'StaticMesh' in actor_class_name:
            # Get components
            components = actor.get_components_by_class(unreal.StaticMeshComponent)
            
            for component in components:

                # Check if disallow_nanite property exists
                if hasattr(component, 'disallow_nanite'):
                    # Get current value
                    current_value = component.get_editor_property('disallow_nanite')
                    
                    # Only change if it's currently True (Nanite is disallowed)
                    if current_value:
                        # Set to False to allow Nanite
                        component.set_editor_property('disallow_nanite', False)
                        unreal.log(f"Enabled Nanite for: {actor.get_actor_label()}")
                        enabled_count += 1
                    else:
                        already_enabled_count += 1

# Execute the function
enable_nanite_for_all_actors()