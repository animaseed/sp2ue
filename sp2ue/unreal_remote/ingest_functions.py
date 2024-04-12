import unreal


class IngestFunctions:
    '''
    Fuctions called in UE
    '''

    @staticmethod
    def test_link():
        print('Link OK')

    @staticmethod
    def does_assset_exist_rtbool(asset_path):
        return unreal.EditorAssetLibrary.does_asset_exist(asset_path)

    @staticmethod
    def is_mesh_asset_rtbool(asset_path):
        asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        if asset_data is None:
            return False
        asset_type = asset_data.asset_class_path.asset_name
        if asset_type == 'SkeletalMesh' or asset_type == 'StaticMesh':
            return True
        else:
            return False

    @staticmethod
    def get_mesh_used_tex_list_rtliststring(mesh_asset_path):
        ret = []
        asset_data = unreal.EditorAssetLibrary.find_asset_data(mesh_asset_path)
        if asset_data is None:
            return ret
        mesh = asset_data.get_asset()
        if mesh is None:
            return ret
        asset_type = asset_data.asset_class_path.asset_name
        if asset_type == 'SkeletalMesh':
            mats = mesh.materials
            for mat in mats:
                if mat is None:
                    continue
                mat_inst = mat.material_interface
                if mat_inst is None:
                    continue
                texture_parameter_values = mat_inst.get_editor_property('texture_parameter_values')
                for texture_parameter_value in texture_parameter_values:
                    tex_asset_path = texture_parameter_value.parameter_value.get_path_name()
                    tex_asset_path = tex_asset_path[:tex_asset_path.rfind('.')]
                    ret.append(tex_asset_path)
        elif asset_type == 'StaticMesh':
            mats = mesh.static_materials
            for mat in mats:
                if mat is None:
                    continue
                mat_inst = mat.material_interface
                if mat_inst is None:
                    continue
                texture_parameter_values = mat_inst.get_editor_property('texture_parameter_values')
                for texture_parameter_value in texture_parameter_values:
                    tex_asset_path = texture_parameter_value.parameter_value.get_path_name()
                    tex_asset_path = tex_asset_path[:tex_asset_path.rfind('.')]
                    ret.append(tex_asset_path)
        return list(set(ret))

    @staticmethod
    def reimport_tex(file_path_list, tex_asset_folder_list, tex_asset_name_list):
        tasks = []
        for i in range(len(file_path_list)):
            file_path = file_path_list[i]
            tex_asset_folder = tex_asset_folder_list[i]
            tex_asset_name = tex_asset_name_list[i]
            task = unreal.AssetImportTask()
            task.filename = file_path
            task.destination_path = tex_asset_folder
            task.destination_name = tex_asset_name
            task.save = False
            task.automated = True
            task.async_ = False
            task.replace_existing = True
            task.replace_existing_settings = False
            tasks.append(task)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
