import unreal
import xml.etree.ElementTree as ET
import os
from pathlib import Path

def get_valid_bake_types():
    return ['VAT', 'BAT', 'OAT', 'DATA']

def is_bake_type_valid(type):
    if type:
        if isinstance(type, str):
            return type in get_valid_bake_types()
    
    return False

def get_converted_scale(system, unit, length, scale):
    """
    """
    length_unit = 1.0
    if system == "METRIC" or system == "NONE":
        if unit == "MICROMETERS":
            length_unit = 1/(100 * 100)
        elif unit == "MILLIMETERS":
            length_unit = 1/(100)
        elif unit == "CENTIMETERS":
            length_unit = 1
        elif unit == "METERS":
            length_unit = 100
        elif unit == "KILOMETERS":
            length_unit = 100 * 100
        elif unit == "ADAPTIVE":
            length_unit = 1 # @NOTE what to do with adaptive?
    elif system == "IMPERIAL":
        if unit == "THOU":
            length_unit = 0.00254
        elif unit == "INCHES":
            length_unit = 2.54
        elif unit == "FEET":
            length_unit = 30.48
        elif unit == "MILES":
            length_unit = 160934
        elif unit == "ADAPTIVE":
            length_unit = 1 # @NOTE what to do with adaptive?

    length = scale / length_unit
    return length

def import_baked_data(file_path, destination, import_mesh, import_mesh_subfolder, import_textures, import_textures_subfolder, create_material, create_material_subfolder, create_material_name, obj_name = ""):
    """ """
    if destination == "":
        return (False, "Invalid destination")

    if not os.path.exists(file_path):
        return (False, "File does not exist")

    if Path(file_path).suffix != ".xml":
        return (False, "File doesn't seem to be an xml file")

    tree = ET.parse(file_path)
    root = tree.getroot()

    baked_data_version = root.get("version")
    baked_data_type = root.get("type")

    if is_bake_type_valid(baked_data_type):
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        if baked_data_type == 'VAT':
            success, msg = import_baked_data_vat(root, baked_data_version, asset_tools, destination, import_mesh, import_mesh_subfolder, import_textures, import_textures_subfolder, create_material, create_material_subfolder, create_material_name, obj_name)
            return(success, msg)
        else:
            return (False, "Unsupported importer for now: " + baked_data_type)
    else:
        return (False, "Couldn't deduce data type")
        
    return (True, "")

def import_baked_data_vat(root, version, asset_tools, destination, import_mesh, import_mesh_subfolder, import_textures, import_textures_subfolder, create_material, create_material_subfolder, create_material_name, obj_name = ""):
    """ """

    import_tasks = []

    baked_data_ID = root.get("ID")

    if destination[-1] != "/":
        destination += "/"

    ###############
    # IMPORT MESH #
    
    mesh = root.find("Mesh")
    if mesh is not None and import_mesh:
        mesh_path = mesh.get("path")
        if mesh_path and os.path.exists(mesh_path):
            asset_import_task = unreal.AssetImportTask()
            asset_import_task.destination_path = destination + import_mesh_subfolder
            asset_import_task.filename = mesh_path # @TODO
            asset_import_task.replace_existing = True
            asset_import_task.automated = True
            asset_import_task.save = False

            asset_import_task.options = unreal.FbxImportUI()

            asset_import_task.options.import_as_skeletal = False
            asset_import_task.options.import_animations = False
            asset_import_task.options.import_mesh = True
            asset_import_task.options.import_rigid_mesh = True
            asset_import_task.options.import_materials = False
            asset_import_task.options.import_textures = False
            asset_import_task.options.create_physics_asset = False

            asset_import_task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            
            asset_import_task.options.static_mesh_import_data.combine_meshes = True
            asset_import_task.options.static_mesh_import_data.auto_generate_collision = False
            asset_import_task.options.static_mesh_import_data.build_nanite = False
            asset_import_task.options.static_mesh_import_data.generate_lightmap_u_vs = False
            asset_import_task.options.static_mesh_import_data.distance_field_resolution_scale = 0.0

            import_tasks.append(asset_import_task)

    ###################
    # IMPORT TEXTURES #

    textures = root.find("Textures")
    if textures is not None and import_textures:
        for texture in textures.findall("Texture"):
            texture_path = texture.get("path")
            if texture_path is not None and os.path.exists(texture_path):
                asset_import_task = unreal.AssetImportTask()
                asset_import_task.destination_path = destination + import_textures_subfolder
                asset_import_task.filename = texture_path # @TODO
                asset_import_task.replace_existing = True
                asset_import_task.automated = True
                asset_import_task.save = False

                import_tasks.append(asset_import_task)
    
    ##########
    # IMPORT #
    
    asset_tools.import_asset_tasks(import_tasks)

    #######
    # XML #

    frames = root.find("Frames")
    if frames is not None:
        frames_sampling = frames.get("sampling") # @TODO do things differently depending on this
        frames_count = frames.get("count")
        frames_padded = frames.get("padded")
        frames_padding = frames.get("padding")
        frames_width = frames.get("width")
        frames_height = frames.get("height")

    uv = root.find("UV")
    if uv is not None:
        uv_index = uv.get("index")
        uv_index_v = uv.get("invert_v") # @TODO update material with this

    mesh = root.find("Mesh")
    if mesh is not None:
        mesh_bounds_offset_min_x = mesh.get("bounds_offset_min_x")
        mesh_bounds_offset_min_y = mesh.get("bounds_offset_min_y")
        mesh_bounds_offset_min_z = mesh.get("bounds_offset_min_z")
        mesh_bounds_offset_max_x = mesh.get("bounds_offset_max_x")
        mesh_bounds_offset_max_y = mesh.get("bounds_offset_max_y")
        mesh_bounds_offset_max_z = mesh.get("bounds_offset_max_z")

    StateMachine = []
    animations = root.find("Animations")
    if animations:
        for animation in animations.findall("Animation"):
            animation_name = animation.get("name")
            animation_start_frame = animation.get("start_frame")
            animation_end_frame = animation.get("end_frame")
            animation_frames = animation.get("frames")

            StateMachine.append((animation_name, animation_start_frame, animation_end_frame, animation_frames))

    ###################
    # IMPORTED ASSETS #

    static_mesh_editor_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

    for import_task in import_tasks:
        unreal.log("Import Task for: {}".format(import_task.filename))
        for object_path in import_task.imported_object_paths:
            unreal.log("Imported object: {}".format(object_path))

            asset = unreal.EditorAssetLibrary.load_asset(object_path)
            if isinstance(asset, unreal.StaticMesh):
                #unreal.EditorAssetLibrary.sync_browser_to_objects([object_path])

                # @TODO disable collision
                asset.set_editor_property("negative_bounds_extension", unreal.Vector(x=float(mesh_bounds_offset_min_x), y=float(mesh_bounds_offset_min_y), z=float(mesh_bounds_offset_min_z))) # @TODO check
                asset.set_editor_property("positive_bounds_extension", unreal.Vector(x=float(mesh_bounds_offset_max_x), y=float(mesh_bounds_offset_max_y), z=float(mesh_bounds_offset_max_z))) # @TODO check
                asset.set_editor_property("generate_mesh_distance_field", False)

                body_setup = asset.get_editor_property('body_setup')
                if body_setup:
                    default_body_instance = body_setup.get_editor_property('default_instance')
                    if default_body_instance:
                        default_body_instance.set_editor_property('collision_profile_name', 'Custom')
                        default_body_instance.set_editor_property('collision_enabled', unreal.CollisionEnabled.NO_COLLISION)
                        default_body_instance.set_editor_property('object_type', unreal.CollisionChannel.ECC_WORLD_DYNAMIC)
                        #collision_responses = default_body_instance.get_editor_property('collision_responses')
                        #collision_array = collision_responses.get_editor_property('response_array')
                        #then what?

                mesh_nanite_settings = static_mesh_editor_subsystem.get_nanite_settings(asset)
                mesh_nanite_settings.enabled = False # @TODO double check this, lerp_u_vs might be the only thing that need to be turned off
                mesh_nanite_settings.lerp_u_vs = False
                static_mesh_editor_subsystem.set_nanite_settings(asset, mesh_nanite_settings)

                mesh_set = static_mesh_editor_subsystem.get_lod_build_settings(asset, 0)
                mesh_set.use_full_precision_u_vs = True # @TODO enable if needed
                mesh_set.generate_lightmap_u_vs = False
                mesh_set.distance_field_resolution_scale = 0.0
                static_mesh_editor_subsystem.set_lod_build_settings(asset, 0, mesh_set)

                static_mesh_editor_subsystem.enable_section_collision(asset, False, 0, 0) # this for material slot(s)
                static_mesh_editor_subsystem.remove_collisions(asset)

                unreal.EditorAssetLibrary.set_metadata_tag(asset, "BakedData", "VAT")

                material_function_path = "/BlenderDataBaker/VAT/Materials/Functions/MF_VAT"
                material_vat_function_asset = unreal.EditorAssetLibrary.load_asset(material_function_path)

                material_function_path = "/BlenderDataBaker/_Shared/Materials/Functions/MF_SelectTexCoords"
                material_texcoords_function_asset = unreal.EditorAssetLibrary.load_asset(material_function_path)
                if material_vat_function_asset and material_texcoords_function_asset:
                    material = asset_tools.create_asset(create_material_name, destination + create_material_subfolder, unreal.Material, unreal.MaterialFactoryNew())
                    if material:
                        #unreal.EditorAssetLibrary.sync_browser_to_objects([material])

                        material.set_editor_property("used_with_niagara_mesh_particles", True)
                        max_displacement = max(float(mesh_bounds_offset_min_x),
                                               max(float(mesh_bounds_offset_min_y),
                                                   max(float(mesh_bounds_offset_min_z),
                                                       max(float(mesh_bounds_offset_max_x),
                                                           max(float(mesh_bounds_offset_max_y),
                                                               float(mesh_bounds_offset_max_z))))))
                        material.set_editor_property("max_world_position_offset_displacement", max_displacement) # @TODO check

                        material_editing = unreal.MaterialEditingLibrary

                        # particle color
                        material_expression_pcol = material_editing.create_material_expression(material, unreal.MaterialExpressionParticleColor, node_pos_x=-500, node_pos_y=-350)
                        material_prop = unreal.MaterialProperty.MP_BASE_COLOR
                        material_editing.connect_material_property(material_expression_pcol, "", material_prop)

                        # dynamic parameter
                        material_expression_dynparam = material_editing.create_material_expression(material, unreal.MaterialExpressionDynamicParameter, node_pos_x=-2000, node_pos_y=0)
                        param_names = ["Frame", "PrevFrame", "Anim", "PrevAnim"]
                        material_expression_dynparam.set_editor_property("param_names", param_names)

                        # frames width/height
                        material_expression_frames_width = material_editing.create_material_expression(material, unreal.MaterialExpressionConstant, node_pos_x=-2000, node_pos_y=250)
                        material_expression_frames_width.set_editor_property("R", float(frames_width))

                        material_expression_frames_height = material_editing.create_material_expression(material, unreal.MaterialExpressionConstant, node_pos_x=-2000, node_pos_y=300)
                        material_expression_frames_height.set_editor_property("R", float(frames_height))

                        # interpolation & modes
                        material_expression_interpolation_auto = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2000, node_pos_y=400)
                        material_expression_interpolation_auto.set_editor_property("Value", False) # @TODO set

                        material_expression_interpolation_nearest = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2000, node_pos_y=475)
                        material_expression_interpolation_nearest.set_editor_property("Value", True) # @TODO set

                        material_expression_continuous = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2000, node_pos_y=550)
                        material_expression_continuous.set_editor_property("Value", True) # @TODO set

                        # vertex interpolator
                        material_expression_vertexinterpolator = material_editing.create_material_expression(material, unreal.MaterialExpressionVertexInterpolator, node_pos_x=-500, node_pos_y=-150)
                        material_prop = unreal.MaterialProperty.MP_NORMAL
                        material_editing.connect_material_property(material_expression_vertexinterpolator, "", material_prop)

                        # tex coords
                        material_expression_vat_function_texcoords = material_editing.create_material_expression(material, unreal.MaterialExpressionMaterialFunctionCall, node_pos_x=-2400, node_pos_y=-30)
                        material_expression_vat_function_texcoords.set_material_function(material_texcoords_function_asset)

                        material_expression_texcoords0 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=-100)
                        material_expression_texcoords0.set_editor_property("Value", int(uv_index) == 0)
                        material_expression_texcoords1 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=-25)
                        material_expression_texcoords1.set_editor_property("Value", int(uv_index) == 1)
                        material_expression_texcoords2 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=50)
                        material_expression_texcoords2.set_editor_property("Value", int(uv_index) == 2)
                        material_expression_texcoords3 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=125)
                        material_expression_texcoords3.set_editor_property("Value", int(uv_index) == 3)
                        material_expression_texcoords4 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=200)
                        material_expression_texcoords4.set_editor_property("Value", int(uv_index) == 4)
                        material_expression_texcoords5 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=275)
                        material_expression_texcoords5.set_editor_property("Value", int(uv_index) == 5)
                        material_expression_texcoords6 = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2600, node_pos_y=350)
                        material_expression_texcoords6.set_editor_property("Value", int(uv_index) == 6)

                        material_editing.connect_material_expressions(material_expression_texcoords0, "", material_expression_vat_function_texcoords, "0")
                        material_editing.connect_material_expressions(material_expression_texcoords1, "", material_expression_vat_function_texcoords, "1")
                        material_editing.connect_material_expressions(material_expression_texcoords2, "", material_expression_vat_function_texcoords, "2")
                        material_editing.connect_material_expressions(material_expression_texcoords3, "", material_expression_vat_function_texcoords, "3")
                        material_editing.connect_material_expressions(material_expression_texcoords4, "", material_expression_vat_function_texcoords, "4")
                        material_editing.connect_material_expressions(material_expression_texcoords5, "", material_expression_vat_function_texcoords, "5")
                        material_editing.connect_material_expressions(material_expression_texcoords6, "", material_expression_vat_function_texcoords, "6")

                        # normal transform
                        material_expression_normaltransform = material_editing.create_material_expression(material, unreal.MaterialExpressionTransform, node_pos_x=-800, node_pos_y=-160)
                        material_expression_normaltransform.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_INSTANCE)
                        material_expression_normaltransform.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
                        material_editing.connect_material_expressions(material_expression_normaltransform, "", material_expression_vertexinterpolator, "")

                        # normal VAT texture
                        material_expression_vat_texture_normal = material_editing.create_material_expression(material, unreal.MaterialExpressionTextureObject, node_pos_x=-2000, node_pos_y=-550)
                        # @TODO set texture

                        # normal remapping
                        texture_remap = False
                        textures = root.find("Textures")
                        if textures is not None:
                            for texture in textures.findall("Texture"):
                                texture_type = texture.get("type")
                                if texture_type is not None and texture_type == "Normal":
                                    texture_remap = texture.get("remap")
                                    break

                        material_expression_vat_normalremapped = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2000, node_pos_y=-300)
                        material_expression_vat_normalremapped.set_editor_property("Value", bool(texture_remap))

                        material_expression_vat_normalremapping = material_editing.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, node_pos_x=-2000, node_pos_y=-200)
                        material_prop = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
                        material_expression_vat_normalremapping.set_editor_property("Constant", material_prop)

                        # normal VAT function
                        material_expression_vat_function_normal = material_editing.create_material_expression(material, unreal.MaterialExpressionMaterialFunctionCall, node_pos_x=-1400, node_pos_y=-150)
                        material_expression_vat_function_normal.set_material_function(material_vat_function_asset)
                        material_editing.connect_material_expressions(material_expression_vat_function_normal, "", material_expression_normaltransform, "")
                        material_editing.connect_material_expressions(material_expression_vat_texture_normal, "", material_expression_vat_function_normal, "Tex")
                        material_editing.connect_material_expressions(material_expression_vat_normalremapped, "", material_expression_vat_function_normal, "Remapped")
                        material_editing.connect_material_expressions(material_expression_vat_normalremapping, "", material_expression_vat_function_normal, "Remapping")
                        material_editing.connect_material_expressions(material_expression_vat_function_texcoords, "", material_expression_vat_function_normal, "UV")
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "0", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "Input0", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "Param0", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "Parameter0", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "Parameter", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "DynamicParameter0", material_expression_vat_function_normal, "Frame"))
                        unreal.log_error(material_editing.connect_material_expressions(material_expression_dynparam, "DynamicParameter", material_expression_vat_function_normal, "Frame"))
                        material_editing.connect_material_expressions(material_expression_frames_width, "", material_expression_vat_function_normal, "FrameHeight")
                        material_editing.connect_material_expressions(material_expression_frames_height, "", material_expression_vat_function_normal, "FrameWidth")
                        material_editing.connect_material_expressions(material_expression_interpolation_auto, "", material_expression_vat_function_normal, "Interpolation_Auto")
                        material_editing.connect_material_expressions(material_expression_interpolation_nearest, "", material_expression_vat_function_normal, "Interpolation_Nearest")
                        material_editing.connect_material_expressions(material_expression_continuous, "", material_expression_vat_function_normal, "Continuous")

                        # offset transform
                        material_expression_offsettransform = material_editing.create_material_expression(material, unreal.MaterialExpressionTransform, node_pos_x=-800, node_pos_y=490)
                        material_expression_offsettransform.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_INSTANCE)
                        material_expression_offsettransform.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
                        #material_prop = unreal.MaterialProperty.MP_WorldPositionOffset # (12), doesn't exist in Python!?
                        #material_editing.connect_material_property(material_expression_offsettransform, "", material_prop)

                        unit_system = "METRIC"
                        unit_unit = "METERS"
                        unit_length = "1.0"
                        unit_scale = "100.0"
                        unit_invert_x = "False"
                        unit_invert_y = "True"
                        unit_invert_z = "False"
                        unit = root.find("Unit")
                        if unit is not None:
                            unit_system = unit.get("system")
                            unit_unit = unit.get("unit")
                            unit_length = unit.get("length")
                            unit_scale = unit.get("scale") # @TODO apply scale to material > (scale / length) ?
                            unit_invert_x = unit.get("invert_x")
                            unit_invert_y = unit.get("invert_y") # @TODO do smthing if not x/Y/z
                            unit_invert_z = unit.get("invert_z")

                        unit_length = float(unit_length)
                        unit_scale = float(unit_scale)
                        unit_invert_x = True if unit_invert_x == 'True' else False
                        unit_invert_y = True if unit_invert_y == 'True' else False
                        unit_invert_z = True if unit_invert_z == 'True' else False

                        # see if offset VAT is in centimeters
                        converted_scale = get_converted_scale(unit_system, unit_unit, unit_length, unit_scale)
                        converted = abs(converted_scale - 1.0) < 0.001

                        # see if offset VAT is inverted
                        inverted = (not unit_invert_x) and (unit_invert_y) and (not unit_invert_z)
                        if not inverted and converted: # @TODO fix
                            pass
                        else:
                            scale = unreal.Vector(-converted_scale if unit_invert_x else converted_scale,
                                                  converted_scale if unit_invert_y else -converted_scale,
                                                  -converted_scale if unit_invert_z else converted_scale)

                            material_expression_offsetscale_multiply = material_editing.create_material_expression(material, unreal.MaterialExpressionMultiply, node_pos_x=-450, node_pos_y=500)
                            material_expression_offsetscale = material_editing.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, node_pos_x=-800, node_pos_y=600)
                            material_prop = unreal.LinearColor(scale.x, scale.y, scale.z, 1.0)
                            material_expression_offsetscale.set_editor_property("Constant", material_prop)

                            material_editing.connect_material_expressions(material_expression_offsettransform, "", material_expression_offsetscale_multiply, "A")
                            material_editing.connect_material_expressions(material_expression_offsetscale, "", material_expression_offsetscale_multiply, "B")

                        # offset VAT texture
                        material_expression_vat_texture_offset = material_editing.create_material_expression(material, unreal.MaterialExpressionTextureObject, node_pos_x=-2000, node_pos_y=700)
                        # @TODO set texture

                        # previous frame switch
                        material_expression_vat_function_prevframeswitch = material_editing.create_material_expression(material, unreal.MaterialExpressionPreviousFrameSwitch, node_pos_x=-1050, node_pos_y=500)

                        # offset remapping
                        texture_remap = "False"
                        texture_remap_x = "0"
                        texture_remap_y = "0"
                        texture_remap_z = "0"
                        textures = root.find("Textures")
                        if textures is not None:
                            for texture in textures.findall("Texture"):
                                texture_type = texture.get("type")
                                if texture_type is not None and texture_type == "Offset":
                                    texture_remap = texture.get("remap")
                                    texture_remap_x = texture.get("remap_x")
                                    texture_remap_y = texture.get("remap_y")
                                    texture_remap_z = texture.get("remap_z")
                                    break

                        material_expression_vat_offsetremapped = material_editing.create_material_expression(material, unreal.MaterialExpressionStaticBool, node_pos_x=-2000, node_pos_y=850)
                        material_expression_vat_offsetremapped.set_editor_property("Value", bool(texture_remap))

                        material_expression_vat_offsetremapping = material_editing.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, node_pos_x=-2000, node_pos_y=1000)
                        material_prop = unreal.LinearColor(float(texture_remap_x), float(texture_remap_y), float(texture_remap_z), 1.0)
                        material_expression_vat_offsetremapping.set_editor_property("Constant", material_prop)

                        # offset VAT function
                        material_expression_vat_function_offset = material_editing.create_material_expression(material, unreal.MaterialExpressionMaterialFunctionCall, node_pos_x=-1700, node_pos_y=500)
                        material_expression_vat_function_offset.set_material_function(material_vat_function_asset)
                        material_editing.connect_material_expressions(material_expression_vat_texture_offset, "", material_expression_vat_function_offset, "Tex")
                        material_editing.connect_material_expressions(material_expression_vat_offsetremapped, "", material_expression_vat_function_offset, "Remapped")
                        material_editing.connect_material_expressions(material_expression_vat_offsetremapping, "", material_expression_vat_function_offset, "Remapping")
                        material_editing.connect_material_expressions(material_expression_vat_function_texcoords, "", material_expression_vat_function_offset, "UV")
                        material_editing.connect_material_expressions(material_expression_dynparam, "Param1", material_expression_vat_function_offset, "Frame")
                        material_editing.connect_material_expressions(material_expression_frames_width, "", material_expression_vat_function_offset, "FrameHeight")
                        material_editing.connect_material_expressions(material_expression_frames_height, "", material_expression_vat_function_offset, "FrameWidth")
                        material_editing.connect_material_expressions(material_expression_interpolation_auto, "", material_expression_vat_function_offset, "Interpolation_Auto")
                        material_editing.connect_material_expressions(material_expression_interpolation_nearest, "", material_expression_vat_function_offset, "Interpolation_Nearest")
                        material_editing.connect_material_expressions(material_expression_continuous, "", material_expression_vat_function_offset, "Continuous")

                        # previous offset VAT function
                        material_expression_vat_function_prevoffset = material_editing.create_material_expression(material, unreal.MaterialExpressionMaterialFunctionCall, node_pos_x=-1400, node_pos_y=700)
                        material_expression_vat_function_prevoffset.set_material_function(material_vat_function_asset)
                        material_editing.connect_material_expressions(material_expression_vat_texture_offset, "", material_expression_vat_function_prevoffset, "Tex")
                        material_editing.connect_material_expressions(material_expression_vat_offsetremapped, "", material_expression_vat_function_prevoffset, "Remapped")
                        material_editing.connect_material_expressions(material_expression_vat_offsetremapping, "", material_expression_vat_function_prevoffset, "Remapping")
                        material_editing.connect_material_expressions(material_expression_vat_function_texcoords, "", material_expression_vat_function_prevoffset, "UV")
                        material_editing.connect_material_expressions(material_expression_dynparam, "Param1", material_expression_vat_function_prevoffset, "0")
                        material_editing.connect_material_expressions(material_expression_frames_width, "", material_expression_vat_function_prevoffset, "FrameHeight")
                        material_editing.connect_material_expressions(material_expression_frames_height, "", material_expression_vat_function_prevoffset, "FrameWidth")
                        material_editing.connect_material_expressions(material_expression_interpolation_auto, "", material_expression_vat_function_prevoffset, "Interpolation_Auto")
                        material_editing.connect_material_expressions(material_expression_interpolation_nearest, "", material_expression_vat_function_prevoffset, "Interpolation_Nearest")
                        material_editing.connect_material_expressions(material_expression_continuous, "", material_expression_vat_function_prevoffset, "Continuous")

                        material_editing.connect_material_expressions(material_expression_vat_function_offset, "", material_expression_vat_function_prevframeswitch, "Current Frame")
                        material_editing.connect_material_expressions(material_expression_vat_function_prevoffset, "", material_expression_vat_function_prevframeswitch, "Previous Frame")

                        material_editing.connect_material_expressions(material_expression_vat_function_prevframeswitch, "", material_expression_offsettransform, "")

            elif isinstance(asset, unreal.Texture2D):
                asset.set_editor_property("sRGB", False)
                asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_HDR_F32)
                asset.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
                asset.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_EFFECTS_NOT_FILTERED)

    return (True, "")