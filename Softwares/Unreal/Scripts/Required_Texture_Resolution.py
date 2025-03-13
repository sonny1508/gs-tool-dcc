import unreal

def disable_nanite_for_all_actors():
    try:
        # Get actors using EditorLevelLibrary
        editor_level_lib = unreal.EditorLevelLibrary()
        all_actors = editor_level_lib.get_all_level_actors()
        selected_actors = editor_level_lib.get_selected_level_actors()
        
        actors_to_process = selected_actors if selected_actors else all_actors
        
        if len(actors_to_process) == 0:
            unreal.log_warning("No actors to process.")
            return
            
        unreal.log(f"Processing {len(actors_to_process)} actors.")
        
        count = 0
        for actor in actors_to_process:
            try:
                # Check if this is a StaticMeshActor
                actor_class_name = actor.get_class().get_name()
                
                if 'StaticMesh' in actor_class_name:
                    # Get components
                    components = actor.get_components_by_class(unreal.StaticMeshComponent)
                    
                    for component in components:
                        try:
                            # Based on the component properties we found, let's try:
                            # 1. disallow_nanite property
                            if hasattr(component, 'disallow_nanite'):
                                unreal.log(f"Setting disallow_nanite to True for {actor.get_actor_label()}")
                                component.set_editor_property('disallow_nanite', True)
                                count += 1
                                continue
                                
                            # 2. force_nanite_for_masked property (set to false)
                            if hasattr(component, 'force_nanite_for_masked'):
                                unreal.log(f"Setting force_nanite_for_masked to False for {actor.get_actor_label()}")
                                component.set_editor_property('force_nanite_for_masked', False)
                                count += 1
                                
                            # Get static mesh if available
                            static_mesh = None
                            if hasattr(component, 'static_mesh'):
                                static_mesh = component.static_mesh
                            
                            if static_mesh:
                                # Try different nanite property names
                                if hasattr(static_mesh, 'nanite_enabled'):
                                    if static_mesh.get_editor_property('nanite_enabled'):
                                        unreal.log(f"Setting nanite_enabled to False for {actor.get_actor_label()}")
                                        static_mesh.set_editor_property('nanite_enabled', False)
                                        static_mesh.modify()
                                        count += 1
                        except Exception as e:
                            unreal.log_warning(f"Error updating component: {str(e)}")
            except Exception as e:
                unreal.log_warning(f"Error processing actor: {str(e)}")
        
        if count > 0:
            unreal.log(f"Successfully processed {count} components to disable Nanite.")
        else:
            unreal.log_warning("No components were modified to disable Nanite.")
    
    except Exception as e:
        unreal.log_error(f"An error occurred: {str(e)}")

# Execute the function
disable_nanite_for_all_actors()