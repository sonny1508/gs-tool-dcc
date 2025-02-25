import unreal

# Path to the BP_PBRV asset
PBRV_ASSET_PATH = "/Script/Engine.Blueprint'/Game/assets/graphics/vehicles/bikes/bikeShared/PBR_TEST/BP_PBRV_Test.BP_PBRV_Test'"

def toggle_pbrv_object():
    # Get all actors in level using the non-deprecated method
    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = editor_actor_subsystem.get_all_level_actors()
    
    # Find BP_PBRV actors
    pbrv_actors = []
    for actor in all_actors:
        try:
            # First try with get_actor_label
            actor_name = actor.get_actor_label()
            if actor_name.startswith("BP_PBRV"):
                pbrv_actors.append(actor)
        except:
            # Fallback to get_name
            try:
                actor_name = actor.get_name()
                if actor_name.startswith("BP_PBRV"):
                    pbrv_actors.append(actor)
            except:
                pass
    
    # CASE 1: No BP_PBRV actors - create one
    if len(pbrv_actors) == 0:
        # Load the asset
        blueprint_asset = unreal.load_object(None, PBRV_ASSET_PATH)
        
        if not blueprint_asset:
            show_message("Error: Could not find BP_PBRV_Test asset!")
            return
        
        # Spawn the actor
        location = unreal.Vector(0, 0, 0)
        rotation = unreal.Rotator(0, 0, 0)
        new_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(blueprint_asset, location, rotation)
        
        if new_actor:
            show_message("BP_PBRV created")
        else:
            show_message("Error: Failed to create BP_PBRV actor")
    
    # CASE 2: Multiple BP_PBRV actors - keep one, delete others
    elif len(pbrv_actors) > 1:
        # Keep the first one
        keep_actor = pbrv_actors[0]
        
        # Delete the rest
        for actor in pbrv_actors[1:]:
            actor.destroy_actor()
        
        # Toggle visibility of the remaining actor
        toggle_actor_visibility(keep_actor)
    
    # CASE 3: Exactly one BP_PBRV actor - toggle visibility
    else:
        actor = pbrv_actors[0]
        toggle_actor_visibility(actor)

def toggle_actor_visibility(actor):
    # Check current visibility using the method that worked
    current_hidden = actor.is_temporarily_hidden_in_editor()
    
    # Toggle visibility using the method that worked
    new_hidden = not current_hidden
    actor.set_is_temporarily_hidden_in_editor(new_hidden)
    
    # Show notification
    status = "OFF" if new_hidden else "ON"
    show_message(f"BP_PBRV visibility turned {status}")

def show_message(message):
    # Use the method that worked in the logs
    unreal.SystemLibrary.print_string(None, message, print_to_screen=True, print_to_log=True)

# Run the script
toggle_pbrv_object()