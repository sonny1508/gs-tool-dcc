import maya.cmds as mc


def GS_Spread():
    # Store original selection
    original_selection = mc.ls(sl=True)
    selected_edges = mc.ls(fl=True, sl=True)
    
    if not selected_edges:
        print("No edges selected!")
        return
    
    print(f"Processing {len(selected_edges)} selected edges...")
    
    # Find all unique edge loops from selected edges
    processed_edges = set()
    edge_loops = []
    
    for edge in selected_edges:
        if edge not in processed_edges:
            # Get complete loop for this edge
            mc.select(edge, r=True)
            complete_loop = mc.ls(mc.polySelectSp(q=True, loop=True), fl=True)
            
            # Find which edges from complete loop are in our selection
            loop_selected_edges = [e for e in complete_loop if e in selected_edges]
            
            if loop_selected_edges:
                edge_loops.append({
                    'selected_edges': loop_selected_edges,
                    'complete_loop': complete_loop
                })
                processed_edges.update(loop_selected_edges)
    
    print(f"Found {len(edge_loops)} edge loops to process")
    
    # Run the algorithm multiple times to converge
    for iteration in range(1):
        print(f"Iteration {iteration + 1}")
        
        # Dictionary to store target positions for all vertices
        vertex_target_positions = {}
        
        # Process each edge loop
        for loop_index, loop_data in enumerate(edge_loops):
            selected_edges_in_loop = loop_data['selected_edges']
            complete_loop = loop_data['complete_loop']
            
            # Get vertices from selected edges in this loop
            loop_vertices = mc.ls(mc.polyListComponentConversion(selected_edges_in_loop, tv=True), fl=True)
            
            # Process each vertex
            for vertex in loop_vertices:
                # Get all edges connected to this vertex that are part of the loop
                vertex_loop_edges = [e for e in mc.ls(mc.polyListComponentConversion(vertex, te=True), fl=True) 
                                   if e in complete_loop]
                
                # Get adjacent vertices on the edge loop
                adjacent_loop_vertices = mc.ls(mc.polyListComponentConversion(vertex_loop_edges, tv=True), fl=True)
                adjacent_loop_vertices = [v for v in adjacent_loop_vertices if v != vertex]
                
                # Get all edges connected to this vertex
                all_vertex_edges = mc.ls(mc.polyListComponentConversion(vertex, te=True), fl=True)
                
                # Find edges that go ACROSS the loop (not along the loop)
                across_edges = [e for e in all_vertex_edges if e not in complete_loop]
                
                if across_edges:
                    # Get all vertices from across edges
                    across_vertices = mc.ls(mc.polyListComponentConversion(across_edges, tv=True), fl=True)
                    # Remove the current vertex from the list
                    across_vertices = [v for v in across_vertices if v != vertex]
                    
                    # If more than 2 neighbors, find the correct ones
                    if len(across_vertices) > 2:
                        qualified_neighbors = []
                        
                        # For each potential neighbor
                        for neighbor in across_vertices:
                            # Get faces connected to both current vertex and this neighbor
                            vertex_faces = mc.ls(mc.polyListComponentConversion(vertex, tf=True), fl=True)
                            neighbor_faces = mc.ls(mc.polyListComponentConversion(neighbor, tf=True), fl=True)
                            shared_faces = set(vertex_faces).intersection(set(neighbor_faces))
                            
                            # Check if any of these shared faces also include an adjacent loop vertex
                            for adj_loop_vertex in adjacent_loop_vertices:
                                adj_faces = mc.ls(mc.polyListComponentConversion(adj_loop_vertex, tf=True), fl=True)
                                
                                # If we find a face shared by all three vertices
                                if any(face in adj_faces for face in shared_faces):
                                    qualified_neighbors.append(neighbor)
                                    break
                        
                        # Use qualified neighbors if we found exactly 2
                        if len(qualified_neighbors) == 2:
                            across_vertices = qualified_neighbors
                        else:
                            print(f"  Vertex {vertex} has {len(qualified_neighbors)} qualified neighbors (need exactly 2)")
                            continue
                    
                    # Only move if exactly 2 across neighbors
                    if len(across_vertices) == 2:
                        # Get current vertex position
                        current_pos = mc.xform(vertex, q=True, t=True, ws=True)
                        
                        # Get neighbor positions
                        pos1 = mc.xform(across_vertices[0], q=True, t=True, ws=True)
                        pos2 = mc.xform(across_vertices[1], q=True, t=True, ws=True)
                        
                        # Calculate distances to each neighbor
                        dist1 = ((current_pos[0] - pos1[0])**2 + 
                                (current_pos[1] - pos1[1])**2 + 
                                (current_pos[2] - pos1[2])**2)**0.5
                        dist2 = ((current_pos[0] - pos2[0])**2 + 
                                (current_pos[1] - pos2[1])**2 + 
                                (current_pos[2] - pos2[2])**2)**0.5
                        
                        # Calculate average distance for equal spacing
                        avg_distance = (dist1 + dist2) / 2.0
                        
                        # Determine which neighbor to move toward
                        if dist1 > avg_distance:
                            # Too far from neighbor 1, move toward it
                            direction = [
                                pos1[0] - current_pos[0],
                                pos1[1] - current_pos[1],
                                pos1[2] - current_pos[2]
                            ]
                            move_distance = dist1 - avg_distance
                        else:
                            # Too far from neighbor 2, move toward it
                            direction = [
                                pos2[0] - current_pos[0],
                                pos2[1] - current_pos[1],
                                pos2[2] - current_pos[2]
                            ]
                            move_distance = dist2 - avg_distance
                        
                        # Normalize direction
                        dir_length = (direction[0]**2 + direction[1]**2 + direction[2]**2)**0.5
                        if dir_length > 0:
                            direction = [d / dir_length for d in direction]
                            
                            # Calculate new position
                            new_pos = [
                                current_pos[0] + direction[0] * move_distance,
                                current_pos[1] + direction[1] * move_distance,
                                current_pos[2] + direction[2] * move_distance
                            ]
                            
                            vertex_target_positions[vertex] = new_pos
                    
                    elif len(across_vertices) != 2:
                        print(f"  Skipping vertex {vertex} - has {len(across_vertices)} across neighbors (need exactly 2)")
        
        # Move all vertices to their calculated target positions
        for vertex, target_pos in vertex_target_positions.items():
            mc.move(target_pos[0], target_pos[1], target_pos[2], vertex, absolute=True, worldSpace=True)
    
    # Restore original selection
    if original_selection:
        mc.select(original_selection, r=True)

HOTKEY_SET = "GSTools"
_RTC = "GS_Spread"
_NAME_CMD = "GS_SpreadNameCommand"


def _ensure_editable_hotkey_set():
    """Maya's factory 'Maya_Default' hotkey set is LOCKED - you cannot add hotkeys
    to it. That is why Alt+S always came up blank: the assignment silently failed.
    If the current set is the locked default, clone it into an editable 'GSTools'
    set and make that current; otherwise keep the user's current (editable) set."""
    current = mc.hotkeySet(q=True, current=True)
    if current and current != "Maya_Default":
        return current
    if not mc.hotkeySet(HOTKEY_SET, exists=True):
        mc.hotkeySet(HOTKEY_SET, source=current or "Maya_Default", current=True)
    else:
        mc.hotkeySet(e=True, current=HOTKEY_SET)
    return HOTKEY_SET


def register():
    """Register the GS_Spread runtime command and bind it to Alt+S.

    The original setup left the hotkey blank for two reasons, both fixed here:
      1. it bound the hotkey straight to a runTimeCommand - Maya's `hotkey -name`
         must reference a *nameCommand* that wraps the runTimeCommand;
      2. it wrote into the locked factory hotkey set (see _ensure_editable_hotkey_set).
    """
    # (Re)create the runtime command. It self-imports so it never depends on
    # GS_Spread already being present in the __main__ namespace.
    if mc.runTimeCommand(_RTC, q=True, exists=True):
        mc.runTimeCommand(_RTC, e=True, delete=True)
    mc.runTimeCommand(
        _RTC,
        command="import GS_Spread\nGS_Spread.GS_Spread()",
        commandLanguage="python",
        category="GSTools",
        annotation="GS Spread - equalize edge spacing",
        default=True,
    )
    # Wrap it in a nameCommand - this is what `hotkey -name` actually binds to.
    mc.nameCommand(_NAME_CMD, annotation="GS Spread", command=_RTC, sourceType="mel")
    # Bind Alt+S on an editable hotkey set.
    _ensure_editable_hotkey_set()
    mc.hotkey(keyShortcut="s", altModifier=True, name=_NAME_CMD)
    print("GSTools: GS_Spread bound to Alt+S (hotkey set '%s')." %
          mc.hotkeySet(q=True, current=True))