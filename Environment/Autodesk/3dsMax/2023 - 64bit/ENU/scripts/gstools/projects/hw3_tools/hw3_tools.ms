-- hw3_tools.ms — GSTools HW3 Modeling Tools for 3ds Max 2023
-- All modelling logic lives here. Called from hw3_tools.py.

-- ── Global roots ─────────────────────────────────────────────────────────────
-- Mirror the XXX_ROOT structure in hw3_tools_ui.py. All paths derive from the
-- %TEMP% environment variable so nothing is hard-coded to a specific drive.
--   HW3_ROOT  = %TEMP%\GSApplication\3dsmax\hw3_tools
--   IO_ROOT   = HW3_ROOT\io   (scratch FBX for building-scene / import-export)
global TEMP_DIR = (
    local t = systemTools.getEnvVariable "TEMP"
    if t == undefined or t == "" then (getDir #temp) else t
)
global HW3_ROOT = TEMP_DIR + "\\GSApplication\\3dsmax\\hw3_tools"
global IO_ROOT  = HW3_ROOT + "\\io"

-- Ensure IO_ROOT exists; return its path.
fn HW_EnsureIORoot = (
    if not (doesFileExist IO_ROOT) do makeDir IO_ROOT all:true
    IO_ROOT
)

-- Put the FBX exporter into a clean, fully-specified state.
-- FBXExporterSetParam settings are GLOBAL and STICKY: any param we don't set
-- keeps whatever value the last export (manual or another tool) left it at.
-- Resetting first and then setting the full block makes every scripted export
-- deterministic instead of inheriting whatever state the exporter was last in.
fn HW_ConfigureFbxExport = (
    try ( pluginManager.loadClass FBXEXP ) catch ()
    try ( FBXResetExport() ) catch ()

    FBXExporterSetParam "Animation" false
    FBXExporterSetParam "BakeAnimation" false
    FBXExporterSetParam "Skin" false
    FBXExporterSetParam "Shape" false              -- no morph/blendshape channels
    FBXExporterSetParam "SmoothingGroups" true
    FBXExporterSetParam "SmoothMeshExport" false   -- do NOT export as subdivision
    FBXExporterSetParam "GeomAsBone" false         -- geometry stays geometry, not bone
    FBXExporterSetParam "Triangulate" false
    FBXExporterSetParam "PreserveEdgeOrientation" true
    FBXExporterSetParam "Preserveinstances" true
    FBXExporterSetParam "Cameras" false
    FBXExporterSetParam "Lights" false
    FBXExporterSetParam "EmbedTextures" false
    FBXExporterSetParam "ASCII" false
    FBXExporterSetParam "FileVersion" "FBX202000"
)

-- Put the FBX importer into a clean, fully-specified state.
-- Like the exporter, FBXImporterSetParam settings are GLOBAL and STICKY. The
-- critical one is "Mode": if the importer was last left in #merge / #exmerge,
-- FBX matches incoming nodes to existing scene nodes BY NAME and updates them
-- in place instead of creating new nodes — so a fresh import produces ZERO new
-- nodes and our "newly imported objects" detection finds nothing. Forcing
-- #create guarantees the source mesh comes in as brand-new nodes every time.
fn HW_ConfigureFbxImport = (
    -- The FBX importer plugin must be loaded before its params exist. importFile
    -- with #noPrompt loads it lazily, so prime it via a reset first; guard
    -- everything so a missing function on an odd FBX build can't abort the import.
    try ( FBXResetImport() ) catch ()

    try ( FBXImporterSetParam "Mode" #create ) catch ()   -- add as NEW nodes, never merge by name
    try ( FBXImporterSetParam "Animation" false ) catch ()
    try ( FBXImporterSetParam "Skin" false ) catch ()
    try ( FBXImporterSetParam "Shape" false ) catch ()
    try ( FBXImporterSetParam "Cameras" false ) catch ()
    try ( FBXImporterSetParam "Lights" false ) catch ()
    try ( FBXImporterSetParam "SmoothingGroups" false ) catch ()
)

-- ── Helpers ──────────────────────────────────────────────────────────────────

fn HW_IsDigit ch = (
    findString "0123456789" ch != undefined
)

fn HW_TrimSep text = (
    local result = text
    while result.count > 0 do (
        local ch = result[result.count]
        if ch == "_" or ch == "-" or ch == "." or ch == " " then
            result = substring result 1 (result.count - 1)
        else
            exit
    )
    result
)

fn HW_ParseName nodeName = (
    local lastDigit = nodeName.count
    while lastDigit > 0 and HW_IsDigit nodeName[lastDigit] do
        lastDigit -= 1
    if lastDigit < nodeName.count then
        #(HW_TrimSep (substring nodeName 1 lastDigit),
          (substring nodeName (lastDigit + 1) (nodeName.count - lastDigit)) as integer)
    else
        #(nodeName, undefined)
)

fn HW_TwoDigit value = (
    if value < 10 then ("0" + (value as string)) else (value as string)
)

fn HW_JoinNames nodes = (
    local result = ""
    for i = 1 to nodes.count do (
        if i > 1 do result += ", "
        result += nodes[i].name
    )
    result
)

fn HW_Sanitize text = (
    local result = substituteString text " " "_"
    result = substituteString result "-" "_"
    result = substituteString result "." "_"
    result
)

fn HW_StripSuffix name sfx = (
    if name.count > sfx.count then (
        local tail = toLower (substring name (name.count - sfx.count + 1) sfx.count)
        if tail == (toLower sfx) then substring name 1 (name.count - sfx.count)
        else name
    ) else name
)

fn HW_GetLayerName node = (
    if node.layer != undefined then HW_Sanitize node.layer.name
    else "Layer"
)

fn HW_RenameByLayer nodes baseName = (
    local layerKeys   = #()
    local layerTotals = #()
    local layerIndexes = #()
    for node in nodes do (
        local lk = toLower (HW_GetLayerName node)
        local idx = findItem layerKeys lk
        if idx == 0 then (
            append layerKeys lk
            append layerTotals 1
        ) else (
            layerTotals[idx] += 1
        )
    )
    for i = 1 to layerTotals.count do append layerIndexes 0
    for node in nodes do (
        local ln  = HW_GetLayerName node
        local lk  = toLower ln
        local idx = findItem layerKeys lk
        local newName = baseName + "_" + ln
        if layerTotals[idx] > 1 then (
            layerIndexes[idx] += 1
            newName += "_" + (HW_TwoDigit layerIndexes[idx])
        )
        node.name = newName
    )
)

fn HW_CollectRelated sourceNode = (
    local related = #()
    local instanceNodes = #()
    InstanceMgr.GetInstances sourceNode &instanceNodes
    for node in instanceNodes do (
        if node != sourceNode and (findItem related node) == 0 do
            append related node
    )
    local dependentNodes = refs.dependentNodes sourceNode.baseObject firstOnly:false baseObjectOnly:true
    for node in dependentNodes do (
        if node != sourceNode and (findItem related node) == 0 do
            append related node
    )
    related
)

fn HW_SortBySuffix a b = (
    local aInfo = HW_ParseName a.name
    local bInfo = HW_ParseName b.name
    local aN = if aInfo[2] == undefined then -1 else aInfo[2]
    local bN = if bInfo[2] == undefined then -1 else bInfo[2]
    if aN == bN then stricmp a.name b.name
    else if aN < bN then -1
    else 1
)

-- ── Operations ────────────────────────────────────────────────────────────────

fn HW_RenameSort = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one object." title:"HW model tool"
        return false
    )
    undo "HW Rename/Sort" on (
        -- Phase 1: Sort selected nodes by their common base name group and renumber.
        local groupKeys  = #()
        local groupBases = #()
        local groupNodes = #()
        for node in nodes do (
            local info    = HW_ParseName node.name
            local baseName = info[1]
            local key     = toLower baseName
            local index   = findItem groupKeys key
            if index == 0 then (
                append groupKeys  key
                append groupBases baseName
                append groupNodes #(node)
            ) else (
                local arr = groupNodes[index]
                append arr node
                groupNodes[index] = arr
            )
        )
        local tmpStamp = (timeStamp() as string)
        for i = 1 to nodes.count do
            nodes[i].name = ("__hw_tmp_" + tmpStamp + "_" + (i as string))
        for gi = 1 to groupNodes.count do (
            local sortedNodes = groupNodes[gi]
            qsort sortedNodes HW_SortBySuffix
            for i = 1 to sortedNodes.count do
                sortedNodes[i].name = (groupBases[gi] + "_" + HW_TwoDigit i)
        )

        -- Phase 2: For each selected source that has references/instances,
        -- rename those references by layer using the now-finalised source names.
        -- Exclude selected nodes from related (they were numbered in Phase 1).
        -- Track processed refs so nodes shared by multiple selected sources are
        -- only renamed once (first matching source wins).
        local processedRefs = #()
        for srcNode in nodes do (
            local related = HW_CollectRelated srcNode
            local filteredRelated = #()
            for r in related do (
                if (findItem nodes r) == 0 and (findItem processedRefs r) == 0 do
                    append filteredRelated r
            )
            if filteredRelated.count > 0 do (
                HW_RenameByLayer filteredRelated (HW_Sanitize srcNode.name)
                for r in filteredRelated do append processedRefs r
            )
        )
    )
    true
)

fn HW_ExportSourceModules meshRoot = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one object to export." title:"HW Export"
        return false
    )
    if not (doesFileExist meshRoot) do makedir meshRoot
    local exported = 0
    disableSceneRedraw()
    undo off (
        for srcNode in nodes do (
            if (superClassOf srcNode) != GeometryClass do continue
            local fbxPath = meshRoot + "\\" + srcNode.name + ".fbx"
            -- Temporarily select only this node for export
            select srcNode
            local ok = false
            try ( ok = exportFile fbxPath #noPrompt selectedOnly:true ) catch ()
            if ok do exported += 1
        )
        -- Restore original selection
        select nodes
    )
    enableSceneRedraw()
    exported
)

fn HW_CollapseModifier = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one object." title:"HW model tool"
        return false
    )
    local invalid = #()
    for node in nodes do (
        if (superClassOf node) != GeometryClass do append invalid node
    )
    if invalid.count > 0 then (
        messageBox ("Selected object is not a mesh/geometry:\n" + (HW_JoinNames invalid)) title:"HW model tool"
        return false
    )
    undo "HW Collapse Modifier" on (
        for node in nodes do (
            if node.modifiers.count > 0 do
                maxOps.CollapseNodeTo node 1 true
        )
    )
    true
)

fn HW_Attach = (
    local nodes = selection as array
    if nodes.count < 2 then (
        messageBox "Please select at least 2 geometry objects." title:"HW model tool"
        return false
    )
    local invalid = #()
    for node in nodes do (
        if (superClassOf node) != GeometryClass do append invalid node
    )
    if invalid.count > 0 then (
        messageBox ("Selected object is not a mesh/geometry:\n" + (HW_JoinNames invalid)) title:"HW model tool"
        return false
    )
    undo "HW Attach" on (
        local target     = nodes[1]
        local targetName = target.name
        convertToPoly target
        for i = 2 to nodes.count do
            polyop.attach target nodes[i]
        target.name = targetName
        select target
    )
    true
)

fn HW_Detach asClone = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one geometry object." title:"HW model tool"
        return false
    )
    if nodes.count != 1 then (
        messageBox "Please select only one object for Detach." title:"HW model tool"
        return false
    )
    local target = nodes[1]
    if (superClassOf target) != GeometryClass then (
        messageBox ("Selected object is not a mesh/geometry:\n" + target.name) title:"HW model tool"
        return false
    )
    convertToPoly target
    local faceSel = polyop.getFaceSelection target
    if faceSel.numberSet == 0 then (
        messageBox "Please select at least one polygon/face to detach." title:"HW model tool"
        return false
    )
    local newName = uniqueName (target.name + "_detach")
    undo "HW Detach" on (
        polyop.detachFaces target faceSel delete:(not asClone) asNode:true name:newName node:target
    )
    true
)

fn HW_RenameSourceRef = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one source object." title:"HW model tool"
        return false
    )
    local count = 0
    undo "HW Rename Source/Reference" on (
        for srcNode in nodes do (
            local srcName = HW_Sanitize srcNode.name
            local related = HW_CollectRelated srcNode
            if related.count > 0 then (
                HW_RenameByLayer related srcName
                count += related.count
            )
        )
    )
    if count == 0 then (
        messageBox "No reference/instance objects found for the selected source objects." title:"HW model tool"
        return false
    )
    true
)

fn HW_SelectRefInst = (
    local nodes = selection as array
    if nodes.count != 1 then (
        messageBox "Please select exactly one source object." title:"HW model tool"
        return false
    )
    local related  = HW_CollectRelated nodes[1]
    local geoNodes = #()
    for node in related do (
        if (superClassOf node) == GeometryClass and (findItem geoNodes node) == 0 do
            append geoNodes node
    )
    if geoNodes.count == 0 then (
        messageBox "No reference/instance geometry objects found." title:"HW model tool"
        return false
    )
    select geoNodes
    true
)

-- From the current selection, keep only "non-reference" objects: those that are
-- neither referenced by nor an instance/reference of any other node. An object
-- with zero related nodes (HW_CollectRelated returns empty) stands completely
-- alone and qualifies. Updates the selection to just those objects.
fn HW_CheckNonReference = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one object." title:"HW model tool"
        return false
    )
    local standalone = #()
    for node in nodes do (
        local related = HW_CollectRelated node
        if related.count == 0 do append standalone node
    )
    if standalone.count == 0 then (
        messageBox "No non-reference objects found in the selection." title:"HW model tool"
        return false
    )
    select standalone
    true
)

fn HW_CreateWindowsGlass = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select at least one source object." title:"HW model tool"
        return false
    )
    for n in nodes do (
        if (superClassOf n) != GeometryClass then (
            messageBox ("Selected object is not a mesh/geometry:\n" + n.name) title:"HW model tool"
            return false
        )
        if n.modifiers.count > 0 then (
            messageBox ("Object has modifier. Please collapse/remove modifiers first:\n" + n.name) title:"HW model tool"
            return false
        )
        if (classOf n.baseObject) != Editable_Poly then (
            messageBox ("Object must be Editable Poly before creating glass:\n" + n.name) title:"HW model tool"
            return false
        )
    )
    local createdCount = 0
    undo "HW Create Windows Glass" on (
        for srcNode in nodes do (
            local matIDFaces = #{}
            local faceCount  = polyop.getNumFaces srcNode
            for f = 1 to faceCount do (
                if (polyop.getFaceMatID srcNode f) == 1 do matIDFaces[f] = true
            )
            if matIDFaces.numberSet == 0 do continue
            local glassName = srcNode.name + "_glass"
            polyop.detachFaces srcNode matIDFaces delete:true asNode:true name:glassName node:srcNode
            local glassSrc = getNodeByName glassName
            if glassSrc == undefined do continue
            createdCount += 1
            local related   = HW_CollectRelated srcNode
            local glassRefs = #()
            for relNode in related do (
                if (superClassOf relNode) != GeometryClass do continue
                local newNodes = #()
                maxOps.CloneNodes glassSrc cloneType:#reference newNodes:&newNodes
                if newNodes.count == 0 do continue
                local glassRef = newNodes[1]
                glassRef.transform = relNode.transform
                if relNode.layer != undefined do relNode.layer.addNode glassRef
                for mi = relNode.modifiers.count to 1 by -1 do
                    addModifier glassRef (copy relNode.modifiers[mi])
                append glassRefs glassRef
                createdCount += 1
            )
            if glassRefs.count > 0 do HW_RenameByLayer glassRefs glassSrc.name
        )
    )
    if createdCount == 0 then (
        messageBox "No Material ID 1 faces found on selected objects." title:"HW model tool"
        return false
    )
    true
)

-- ── Source Replace helpers ───────────────────────────────────────────────────

-- Remap face Material IDs on targetObj so they match masterMat's slot layout.
-- Mirrors Material_ID_Remapper.mcr: matches sub-material names from srcMat to
-- masterMat slots, builds oldID->newID table, iterates all faces.
-- Returns true if any remapping was performed.
fn HW_RemapMaterialIDs targetObj masterMat =
(
    if masterMat == undefined then return false
    if targetObj.material == undefined then return false
    if (classOf masterMat) != Multimaterial then return false

    -- Build master name -> slot ID lookup
    local masterNameToID = #()
    for i = 1 to masterMat.numsubs do (
        local sub = masterMat.materialList[i]
        if sub != undefined do
            append masterNameToID #(toLower sub.name, masterMat.materialIDList[i])
    )
    if masterNameToID.count == 0 then return false

    -- Build oldID -> newID remapping from targetObj's current material
    local idMappings = #()
    local srcMat = targetObj.material

    if (classOf srcMat) == Multimaterial then (
        for i = 1 to srcMat.numsubs do (
            local sub = srcMat.materialList[i]
            if sub == undefined do continue
            local oldID = srcMat.materialIDList[i]
            for pair in masterNameToID where pair[1] == (toLower sub.name) do (
                if pair[2] != oldID do append idMappings #(oldID, pair[2])
                exit
            )
        )
    ) else (
        -- Single material: treated as face ID 1
        for pair in masterNameToID where pair[1] == (toLower srcMat.name) do (
            if pair[2] != 1 do append idMappings #(1, pair[2])
            exit
        )
    )

    if idMappings.count == 0 then return true  -- names matched but IDs already correct

    -- Remap face IDs — supports Editable Poly and Editable Mesh (same as Material_ID_Remapper.mcr)
    if (classOf targetObj.baseObject) == Editable_Poly or (classOf targetObj.baseObject) == PolyMeshObject then (
        local n = polyop.getNumFaces targetObj
        for f = 1 to n do (
            local fID = polyop.getFaceMatID targetObj f
            for m in idMappings where m[1] == fID do (
                polyop.setFaceMatID targetObj f m[2]
                exit
            )
        )
    ) else if (classOf targetObj.baseObject) == Editable_Mesh then (
        local n = targetObj.numfaces
        for f = 1 to n do (
            local fID = getFaceMatID targetObj f
            for m in idMappings where m[1] == fID do (
                setFaceMatID targetObj f m[2]
                exit
            )
        )
    )
    true
)

-- Check if any sub-material (or top-level material) names in srcMat overlap with masterMat
fn HW_MaterialNamesMatch srcMat masterMat =
(
    if srcMat == undefined or masterMat == undefined then return false

    local masterNames = #()
    if (classOf masterMat) == Multimaterial then (
        for i = 1 to masterMat.numsubs do (
            local sub = masterMat.materialList[i]
            if sub != undefined do append masterNames (toLower sub.name)
        )
    ) else (
        append masterNames (toLower masterMat.name)
    )
    if masterNames.count == 0 then return false

    if (classOf srcMat) == Multimaterial then (
        for i = 1 to srcMat.numsubs do (
            local sub = srcMat.materialList[i]
            if sub != undefined and (findItem masterNames (toLower sub.name)) > 0 do return true
        )
    ) else (
        if (findItem masterNames (toLower srcMat.name)) > 0 do return true
    )
    false
)

-- ── Source Replace ────────────────────────────────────────────────────────────

global HW_ReplacerNode = undefined

fn HW_SetReplacer = (
    local nodes = selection as array
    if nodes.count == 0 then (
        messageBox "Please select an object in the viewport first." title:"Source Replace"
        return undefined
    )
    if nodes.count > 1 then (
        messageBox "Please select exactly one object." title:"Source Replace"
        return undefined
    )
    HW_ReplacerNode = nodes[1]
    HW_ReplacerNode.name
)

fn HW_ClearReplacer = (
    HW_ReplacerNode = undefined
    ""
)

fn HW_GetReplacerName = (
    if HW_ReplacerNode == undefined then return ""
    if isdeleted HW_ReplacerNode then ( HW_ReplacerNode = undefined; return "" )
    HW_ReplacerNode.name
)

fn HW_SourceReplace fbxPath = (
    if HW_ReplacerNode == undefined then (
        messageBox "Please pick a replacer object first." title:"Source Replace"
        return false
    )
    if isdeleted HW_ReplacerNode then (
        messageBox "Replacer object no longer exists. Please pick a new one." title:"Source Replace"
        HW_ReplacerNode = undefined
        return false
    )
    if not (doesFileExist fbxPath) then (
        messageBox ("FBX file not found:\n" + fbxPath) title:"Source Replace"
        return false
    )

    local replacer = HW_ReplacerNode

    -- Collect all geometry nodes that share replacer's baseObject (instances + references).
    local allRelated = #(replacer)
    local related = HW_CollectRelated replacer
    for obj in related do (
        if (superClassOf obj) == GeometryClass and (findItem allRelated obj) == 0 do
            append allRelated obj
    )

    -- Snapshot layer hidden states — FBX import can alter them as a side effect
    local snapLayerNames  = #()
    local snapLayerHidden = #()
    for i = 0 to layerManager.count - 1 do (
        local lyr = layerManager.getLayer i
        if lyr != undefined do (
            append snapLayerNames  lyr.name
            append snapLayerHidden lyr.isHidden
        )
    )

    -- Temp-rename only the replacer to avoid FBX import name collision
    local origName = replacer.name
    local stamp = timeStamp() as string
    replacer.name = ("__hw_src_" + stamp)

    -- Record existing handles before import
    local beforeHandles = #()
    for obj in objects do append beforeHandles obj.handle

    -- Import FBX silently. Force importer into create-new mode first, otherwise a
    -- sticky #merge mode would update existing nodes by name and import nothing new.
    HW_ConfigureFbxImport()
    disableSceneRedraw()
    local importOK = false
    try ( importOK = importFile fbxPath #noPrompt ) catch ()
    enableSceneRedraw()

    if not importOK then (
        replacer.name = origName
        messageBox "Failed to import FBX file." title:"Source Replace"
        return false
    )

    -- Collect newly imported objects
    local importedAll = #()
    for obj in objects do (
        if (findItem beforeHandles obj.handle) == 0 do append importedAll obj
    )
    if importedAll.count == 0 then (
        replacer.name = origName
        messageBox "No objects were imported from the FBX file." title:"Source Replace"
        return false
    )

    -- Find root of imported hierarchy
    local importedRoots = #()
    for obj in importedAll do (
        local hasImportedParent = false
        for other in importedAll do (
            if obj != other and obj.parent == other then ( hasImportedParent = true; exit )
        )
        if not hasImportedParent do append importedRoots obj
    )
    local srcObj = importedRoots[1]

    -- Remap face material IDs on srcObj to match replacer's material layout before swap.
    local matMatched = HW_MaterialNamesMatch srcObj.material replacer.material
    if matMatched do HW_RemapMaterialIDs srcObj replacer.material

    undo "HW Source Replace" on (
        -- Swap geometry and objectOffset: assign new baseObject and copy the geometric offset
        -- from srcObj so the pivot-to-geometry relationship matches the imported mesh.
        local newBase       = srcObj.baseObject
        local newOffsetPos   = srcObj.objectOffsetPos
        local newOffsetRot   = srcObj.objectOffsetRot
        local newOffsetScale = srcObj.objectOffsetScale
        for node in allRelated do (
            try (
                node.baseObject      = newBase
                node.objectOffsetPos   = newOffsetPos
                node.objectOffsetRot   = newOffsetRot
                node.objectOffsetScale = newOffsetScale
            ) catch ()
        )

        -- Restore replacer's original name
        replacer.name = origName

        -- Delete all imported FBX wrapper nodes.
        -- Geometry survives because allRelated nodes now hold references to newBase.
        for obj in importedAll do (
            if not isdeleted obj do try ( delete obj ) catch ()
        )

        HW_ReplacerNode = undefined
        redrawViews()
    )

    -- Restore layer hidden states changed by the FBX import (outside undo block so it
    -- persists correctly across multiple sequential Source Replace calls).
    for i = 1 to snapLayerNames.count do (
        local lyr = layerManager.getLayerFromName snapLayerNames[i]
        if lyr != undefined do try ( lyr.isHidden = snapLayerHidden[i] ) catch ()
    )

    true
)

-- ── File I/O ──────────────────────────────────────────────────────────────────

-- Helper: return the parent ILayer of a given ILayer, or undefined.
fn HW_GetParentLayer lyr = (
    local parent = undefined
    try ( parent = lyr.getParent() ) catch ()
    parent
)

-- Helper: return true if lyr's immediate parent is named parentLayerName.
fn HW_LayerDirectChildOf lyr parentLayerName = (
    local p = HW_GetParentLayer lyr
    if p == undefined then return false
    p.name == parentLayerName
)

-- Helper: get or create a layer nested under parentLayerName.
fn HW_GetOrCreateChildLayer parentLayerName childLayerName = (
    local childLyr = layerManager.getLayerFromName childLayerName
    if childLyr == undefined then (
        childLyr = layerManager.newLayerFromName childLayerName
        local parentLyr = layerManager.getLayerFromName parentLayerName
        if parentLyr != undefined do (
            try ( childLyr.setParent parentLyr ) catch ()
        )
    )
    childLyr
)

-- Returns the ancestor chain of lyr from the direct child of stopAtName down to lyr,
-- ordered root-first. E.g., Brick under Wall under _Part_Divisions → ["Wall","Brick"].
-- Uses getParent() with try/catch; falls back to just [lyr.name] if unavailable.
fn HW_GetLayerChain lyr stopAtName = (
    local chain = #()
    local cur = lyr
    while cur != undefined do (
        if cur.name == stopAtName do exit
        local newChain = #(cur.name)
        for n in chain do append newChain n
        chain = newChain
        local parent = undefined
        try ( parent = cur.getParent() ) catch ()
        cur = parent
    )
    if chain.count == 0 and lyr != undefined do chain = #(lyr.name)
    chain
)

fn HW_ExportBuildingScene = (
    local SRC_LAYER  = "Source_Modules"
    local DIV_LAYER  = "_Part_Divisions"
    local EXP_SUFFIX = "_export"
    local EXP_PARENT = "Source_Modules_Instance"

    local srcLayer = layerManager.getLayerFromName SRC_LAYER
    if srcLayer == undefined then (
        messageBox ("Layer '" + SRC_LAYER + "' not found.") title:"Export Building Scene"
        return false
    )
    if (layerManager.getLayerFromName DIV_LAYER) == undefined then (
        messageBox ("Layer '" + DIV_LAYER + "' not found.") title:"Export Building Scene"
        return false
    )

    local srcNodes = #()
    srcLayer.nodes &srcNodes
    local geoSrcNodes = #()
    for n in srcNodes where (superClassOf n) == GeometryClass do append geoSrcNodes n
    if geoSrcNodes.count == 0 then (
        messageBox ("No geometry objects in '" + SRC_LAYER + "'.") title:"Export Building Scene"
        return false
    )

    local totalCreated = 0

    max modify mode

    undo "HW Export Building Scene" on (
        disableSceneRedraw()

        -- ── Re-run cleanup: remove the previous bake ─────────────────────────────
        -- Delete every object tagged HW_Baked from a prior run so we regenerate
        -- fresh instead of stacking duplicate output. The original Array-reference
        -- objects are preserved (hidden + tagged HW_BakeRef) and re-baked below.
        local prevBaked = #()
        for obj in objects do (
            if (getUserProp obj "HW_Baked") == "1" do append prevBaked obj
        )
        for obj in prevBaked where (isValidNode obj) do try ( delete obj ) catch ()

        -- Ensure _Part_Divisions_export parent layer exists
        local expParentLyr = layerManager.getLayerFromName EXP_PARENT
        if expParentLyr == undefined do expParentLyr = layerManager.newLayerFromName EXP_PARENT

        -- ── Phase 1: For each source object, process all its references ───────────
        -- Flow per reference:
        --   find ref → copy Array modifier to source → Create Objects →
        --   delete ref immediately → relink instances → move to _export layer
        for srcNode in geoSrcNodes do (
            local related = HW_CollectRelated srcNode

            for refNode in related do (
                if (superClassOf refNode) != GeometryClass do continue
                local refLyr = refNode.layer
                if refLyr == undefined do continue
                if refLyr.name == SRC_LAYER do continue

                -- Find Array modifier
                local arrayMod = undefined
                for m in refNode.modifiers do (
                    if (findString (toLower ((classOf m) as string)) "array") != undefined then (
                        arrayMod = m; exit
                    )
                )

                -- Build the nested _export layer hierarchy mirroring _Part_Divisions depth.
                -- e.g. _Part_Divisions > Wall > Brick → _Part_Divisions_export > Wall_export > Brick_export
                local layerChain = HW_GetLayerChain refLyr DIV_LAYER
                local curExpParent = expParentLyr
                local expChildLyr  = expParentLyr
                for chainName in layerChain do (
                    local expName  = chainName + EXP_SUFFIX
                    local chainLyr = layerManager.getLayerFromName expName
                    if chainLyr == undefined then (
                        try ( chainLyr = layerManager.newLayerFromName expName parent:curExpParent ) catch ()
                        if chainLyr == undefined do (
                            chainLyr = layerManager.newLayerFromName expName
                            if chainLyr != undefined do try ( chainLyr.setParent curExpParent ) catch ()
                        )
                    )
                    if chainLyr != undefined do (
                        curExpParent = chainLyr
                        expChildLyr  = chainLyr
                    )
                )

                if arrayMod != undefined then (
                    -- Copy modifier to source object
                    local newMod = copy arrayMod
                    addModifier srcNode newMod

                    -- Snapshot max handle and existing layer names before Create Objects
                    local maxHandleBefore = 0
                    for obj in objects do (
                        if obj.handle > maxHandleBefore do maxHandleBefore = obj.handle
                    )
                    local preCreateLayers = #()
                    for i = 0 to layerManager.count - 1 do (
                        local l = layerManager.getLayer i
                        if l != undefined do append preCreateLayers l.name
                    )

                    -- Execute Create Objects with Use Instance
                    local prevSel = selection as array
                    select srcNode
                    try ( newMod.useInstance = true ) catch ()
                    try ( newMod.createObjects() ) catch ()
                    if prevSel.count > 0 then select prevSel else clearSelection()

                    -- Collect newly created objects (handle > maxHandleBefore)
                    local newObjs = #()
                    for obj in objects do (
                        if obj.handle > maxHandleBefore do append newObjs obj
                    )

                    -- Remove temp modifier from source
                    deleteModifier srcNode newMod

                    -- Preserve the Array-reference object instead of deleting it,
                    -- so this tool is re-runnable: hide it and tag it. It keeps its
                    -- Array modifier, so HW_CollectRelated + the "has Array modifier"
                    -- filter re-find it on the next run. (Old behaviour: delete refNode.)
                    setUserProp refNode "HW_BakeRef" "1"
                    refNode.isHidden = true

                    -- Relink: assign baseObject so clones are true instances of srcNode.
                    -- Save transform first — carries the array positions.
                    for newObj in newObjs do (
                        try (
                            local tm = newObj.transform
                            newObj.baseObject = srcNode.baseObject
                            newObj.transform = tm
                        ) catch ()
                    )

                    -- Align pivot: same pivot-to-mesh relationship as srcNode.
                    -- localPivotPos = pivot in srcNode's local mesh space.
                    -- Each instance gets: pivot = localPivotPos * its own objecttransform.
                    local localPivotPos = srcNode.pivot * inverse(srcNode.objecttransform)
                    for newObj in newObjs do (
                        try ( newObj.pivot = localPivotPos * newObj.objecttransform ) catch ()
                    )

                    -- Move new objects into the deepest _export layer.
                    -- Tag them as baked output so a later run can remove this bake
                    -- before regenerating (keeps the tool re-runnable).
                    for newObj in newObjs do (
                        try ( setUserProp newObj "HW_Baked" "1" ) catch ()
                        try ( expChildLyr.addNode newObj ) catch ()
                        totalCreated += 1
                    )

                    -- Delete _Clones layers created by createObjects() (now empty)
                    for i = layerManager.count - 1 to 0 by -1 do (
                        local l = layerManager.getLayer i
                        if l == undefined do continue
                        -- Skip layers that existed before createObjects
                        local alreadyExisted = false
                        for pn in preCreateLayers where pn == l.name do ( alreadyExisted = true; exit )
                        if alreadyExisted do continue
                        if (findString (toLower l.name) "_clones") != undefined do
                            try ( layerManager.deleteLayerByName l.name ) catch ()
                    )
                ) else (
                    -- No Array modifier. This can be a leftover baked instance from a
                    -- previous run (shares srcNode.baseObject, so HW_CollectRelated
                    -- returns it). Those are removed by the start-of-run cleanup, so
                    -- skip anything tagged; only drop genuine non-array references.
                    local isBaked = (getUserProp refNode "HW_Baked") == "1"
                    local isRef   = (getUserProp refNode "HW_BakeRef") == "1"
                    if not isBaked and not isRef do delete refNode
                )
            )
        )

        -- ── Final step: move objects from Source_Modules_Instance → _Part_Divisions ──
        -- Strip _export suffix from each layer name in the relative path.
        -- Objects on Source_Modules_Instance directly → go to _Part_Divisions.
        -- Objects in wall_01_export → go to wall_01 under _Part_Divisions, etc.
        local instLyr   = layerManager.getLayerFromName EXP_PARENT
        local divTopLyr = layerManager.getLayerFromName DIV_LAYER
        if instLyr != undefined and divTopLyr != undefined do (
            local allSceneObjs = objects as array
            for obj in allSceneObjs do (
                local objLyr = obj.layer
                if objLyr == undefined do continue
                local relPath = #()
                local cur     = objLyr
                local inInst  = false
                while cur != undefined do (
                    if cur.name == EXP_PARENT do ( inInst = true; exit )
                    local parent = undefined
                    try ( parent = cur.getParent() ) catch ()
                    local stripped = HW_StripSuffix cur.name EXP_SUFFIX
                    local newPath = #(stripped)
                    for n in relPath do append newPath n
                    relPath = newPath
                    cur = parent
                )
                if not inInst do continue
                local curParent = divTopLyr
                local targetLyr = divTopLyr
                for layerName in relPath do (
                    local lyr = layerManager.getLayerFromName layerName
                    if lyr == undefined then (
                        lyr = layerManager.newLayerFromName layerName
                        if lyr != undefined do try ( lyr.setParent curParent ) catch ()
                    )
                    if lyr != undefined do (
                        curParent = lyr
                        targetLyr = lyr
                    )
                )
                try ( targetLyr.addNode obj ) catch ()
            )
        )

        -- Delete Source_Modules_Instance and its children if no objects remain inside
        if instLyr != undefined do (
            local hasObjs = false
            for obj in objects while not hasObjs do (
                local cur = obj.layer
                while cur != undefined do (
                    if cur.name == EXP_PARENT do ( hasObjs = true; exit )
                    local p = undefined
                    try ( p = cur.getParent() ) catch ()
                    cur = p
                )
            )
            if not hasObjs do (
                -- Collect all layer names in the subtree
                local instLayerNames = #()
                for i = 0 to layerManager.count - 1 do (
                    local lyr = layerManager.getLayer i
                    if lyr == undefined do continue
                    local cur = lyr
                    local inSubtree = false
                    while cur != undefined do (
                        if cur.name == EXP_PARENT do ( inSubtree = true; exit )
                        local p = undefined
                        try ( p = cur.getParent() ) catch ()
                        cur = p
                    )
                    if inSubtree do append instLayerNames lyr.name
                )
                -- Delete bottom-up: retry passes until all removed
                local maxPasses = instLayerNames.count + 1
                local pass = 0
                while instLayerNames.count > 0 and pass < maxPasses do (
                    pass += 1
                    local remaining = #()
                    for lyrName in instLayerNames do (
                        local ok = false
                        try ( ok = layerManager.deleteLayerByName lyrName ) catch ()
                        if not ok do append remaining lyrName
                    )
                    instLayerNames = remaining
                )
            )
        )

        -- Unhide all objects in Source_Modules
        local srcModNodes = #()
        srcLayer.nodes &srcModNodes
        for obj in srcModNodes do try ( obj.isHidden = false ) catch ()

        -- Unhide all objects in _Part_Divisions and its children
        if divTopLyr != undefined do (
            for obj in objects do (
                local cur = obj.layer
                local inDiv = false
                while cur != undefined do (
                    if cur.name == DIV_LAYER do ( inDiv = true; exit )
                    local p = undefined
                    try ( p = cur.getParent() ) catch ()
                    cur = p
                )
                -- Keep preserved Array-reference objects hidden: they must not appear
                -- in the viewport or be picked up by the visibility-based export.
                if inDiv and (getUserProp obj "HW_BakeRef") != "1" do
                    try ( obj.isHidden = false ) catch ()
            )
        )

        enableSceneRedraw()
        redrawViews()
    )

    if totalCreated == 0 then (
        messageBox "No objects created.\nCheck refs have an Array modifier." title:"Export Building Scene"
        return false
    )

    messageBox (totalCreated as string + " object(s) exported.") title:"Export Building Scene"

    -- Export all visible objects to <IO_ROOT>\temp_building_scene.fbx
    local fbxPath = (HW_EnsureIORoot()) + "\\temp_building_scene.fbx"
    local prevSel = selection as array
    local visibleObjs = #()
    for obj in objects do (
        if obj.isHidden do continue
        -- Never export preserved Array-reference source objects.
        if (getUserProp obj "HW_BakeRef") == "1" do continue
        append visibleObjs obj
    )
    if visibleObjs.count > 0 do (
        select visibleObjs
        HW_ConfigureFbxExport()
        exportFile fbxPath #noPrompt selectedOnly:true
    )
    if prevSel.count > 0 then select prevSel else clearSelection()

    true
)

fn HW_ImportTemp = (
    local importPath = (HW_EnsureIORoot()) + "\\temp.fbx"
    if not (doesFileExist importPath) do (
        messageBox ("File not found:\n" + importPath) title:"Import"
        return false
    )

    -- Snapshot scene materials before import so we only match against pre-existing ones
    local preMats = #()
    for mat in sceneMaterials do append preMats mat

    local beforeHandles = #()
    for obj in objects do append beforeHandles obj.handle

    HW_ConfigureFbxImport()
    disableSceneRedraw()
    local importOK = false
    try ( importOK = importFile importPath #noPrompt ) catch ()
    enableSceneRedraw()

    if not importOK do (
        messageBox "Failed to import FBX file." title:"Import"
        return false
    )

    -- Collect newly imported geometry objects
    local importedObjs = #()
    for obj in objects do (
        if (findItem beforeHandles obj.handle) == 0 and
           (superClassOf obj) == GeometryClass do append importedObjs obj
    )

    -- Material remap: for each imported object, search pre-existing scene materials
    -- by name. If any sub-material name (or the material name itself) matches,
    -- remap face IDs to the scene material's slot layout and assign it.
    for impObj in importedObjs do (
        if impObj.material == undefined do continue
        local bestMatch = undefined
        for sceneMat in preMats do (
            if HW_MaterialNamesMatch impObj.material sceneMat do (
                bestMatch = sceneMat; exit
            )
        )
        if bestMatch != undefined do (
            HW_RemapMaterialIDs impObj bestMatch
            try ( impObj.material = bestMatch ) catch ()
        )
    )

    redrawViews()
    importedObjs.count
)

fn HW_ExportSelected = (
    local nodes = selection as array
    if nodes.count == 0 do (
        messageBox "Please select at least one object." title:"Export Selected"
        return false
    )
    local exportPath = (HW_EnsureIORoot()) + "\\temp.fbx"
    HW_ConfigureFbxExport()
    local ok = false
    try ( ok = exportFile exportPath #noPrompt selectedOnly:true ) catch ()
    if not ok do (
        messageBox "Failed to export FBX file." title:"Export Selected"
        return false
    )
    true
)

format "[GSTools] hw3_tools.ms loaded\n"
