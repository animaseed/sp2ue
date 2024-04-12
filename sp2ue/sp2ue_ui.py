"""UI for sp2ue plugin"""
import codecs
import json
import os.path
import shutil
import time

import substance_painter.export as sp_export
import substance_painter.project as sp_project
import substance_painter.resource as sp_resource
import substance_painter.textureset as sp_textureset
import substance_painter.ui as sp_ui
from PySide2 import QtGui, QtWidgets, QtCore

import sp2ue.unreal_remote.remote_execution_inst as ue_re_inst
import sp2ue.unreal_remote.RPC as ue_re_rpc

RE = ue_re_inst.RE
RPC = ue_re_rpc.RPC

TEMP_TEX_FOLDER_PATH = os.path.join(os.path.dirname(__file__), 'TempTex').replace('\\', '/')
TEX_BIND_INFO_FOLDER_PATH = os.path.join(os.path.dirname(__file__), 'TexBindInfo').replace('\\', '/')
TEX_BIND_INFO_TXT_PATH = os.path.join(TEX_BIND_INFO_FOLDER_PATH, 'TexBindInfo.txt').replace('\\', '/')


def show_message_box(text):
    QtWidgets.QMessageBox.warning(sp_ui.get_main_window(), 'warning', text)


class TexBindPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._tex_bind_info_lay = None
        main_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(main_vlay)
        preset_vlay = QtWidgets.QVBoxLayout()
        main_vlay.addLayout(preset_vlay)
        preset_vlay.addWidget(QtWidgets.QLabel("Presets:"))
        self.preset_selector = QtWidgets.QComboBox()
        preset_vlay.addWidget(self.preset_selector)
        mesh_asset_path_hlay = QtWidgets.QHBoxLayout()
        main_vlay.addLayout(mesh_asset_path_hlay)
        mesh_asset_path_hlay.addWidget(QtWidgets.QLabel('Mesh Asset Path:'))
        self.mesh_path_edit = QtWidgets.QLineEdit()
        mesh_asset_path_hlay.addWidget(self.mesh_path_edit)
        rebind_btn = QtWidgets.QPushButton('Rebind Tex')
        rebind_btn.clicked.connect(self._on_rebind_tex_clicked)
        mesh_asset_path_hlay.addWidget(rebind_btn)
        self.bind_info_frame = QtWidgets.QWidget()
        self.bind_info_frame.setStyleSheet("border-radius: 4px;border: 1px solid gray;")
        main_vlay.addWidget(self.bind_info_frame)
        self.bind_info_vlay = QtWidgets.QVBoxLayout()
        self.bind_info_frame.setLayout(self.bind_info_vlay)
        mesh_asset_path, preset, tex_bind_info_list = self._get_tex_bind_info_from_file()
        self.bind_info_frame.hide()
        if len(tex_bind_info_list) > 0:
            self._update_bind_info(mesh_asset_path, tex_bind_info_list)
        self._update_presets(preset)

    def _update_presets(self, preset):
        self.your_export_preset_list = []
        self.starter_export_preset_list = []
        shelves = sp_resource.Shelves.all()
        for shelf in shelves:
            if shelf.name() == 'starter_assets':
                folder_path = os.path.join(shelf.path(), 'export-presets')
                for file in os.listdir(folder_path):
                    if file.endswith('.spexp'):
                        name = file[:file.rfind('.')]
                        self.starter_export_preset_list.append(name)
                        self.preset_selector.addItem(name)
            if shelf.name() == 'your_assets':
                folder_path = os.path.join(shelf.path(), 'export-presets')
                for file in os.listdir(folder_path):
                    if file.endswith('.spexp'):
                        name = file[:file.rfind('.')]
                        self.your_export_preset_list.append(name)
                        self.preset_selector.addItem(name)
        if preset != '':
            current_idx = 0
            for i in range(self.preset_selector.count()):
                if self.preset_selector.itemText(i) == preset:
                    current_idx = i
            self.preset_selector.setCurrentIndex(current_idx)

    def get_cur_preset(self):
        preset = self.preset_selector.currentText()
        shelf_name = ''
        if preset in self.your_export_preset_list:
            shelf_name = 'your_assets'
        if preset in self.starter_export_preset_list:
            shelf_name = 'starter_assets'
        return sp_resource.ResourceID(context=shelf_name, name=preset)

    def _update_bind_info(self, mesh_asset_path, info_list):
        self.bind_info_frame.show()
        self.mesh_path_edit.setText(mesh_asset_path)
        self._mesh_asset_path = mesh_asset_path
        items = []
        for i in range(self.bind_info_vlay.count()):
            items.append(self.bind_info_vlay.itemAt(i))
        for item in items:
            self.bind_info_vlay.removeItem(item)
        lable = QtWidgets.QLabel('Tex Bind Info:')
        lable.setStyleSheet("border-radius: 0px;border: 0px solid gray;")
        self.bind_info_vlay.addWidget(lable)
        scroll = QtWidgets.QScrollArea()
        scroll.setStyleSheet("border-radius: 0px;border: 0px solid gray;")
        self.bind_info_vlay.addWidget(scroll)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        widget = QtWidgets.QWidget()
        widget.setStyleSheet("border-radius: 4px;border: 1px solid gray;")
        scroll.setWidget(widget)
        vlay = QtWidgets.QVBoxLayout()
        widget.setLayout(vlay)
        tex_bind_info_glay = QtWidgets.QGridLayout()
        vlay.addLayout(tex_bind_info_glay)
        for i in range(len(info_list)):
            info = info_list[i]
            tex_bind_info_glay.addWidget(QtWidgets.QLabel(info[0]), i, 0)
            line_edit = QtWidgets.QLineEdit()
            tex_bind_info_glay.addWidget(line_edit, i, 1)
            line_edit.setText(info[1])
        btn_hlay = QtWidgets.QHBoxLayout()
        self.bind_info_vlay.addLayout(btn_hlay)
        btn_hlay.addStretch()
        btn = QtWidgets.QPushButton('Save')
        btn.setStyleSheet("border-radius: 2px;border: 1px solid gray;")

        btn_hlay.addWidget(btn)
        btn.clicked.connect(self._on_tex_bind_info_save_clicked)
        self.bind_info_vlay.addStretch()
        self._tex_bind_info_lay = tex_bind_info_glay

    def _on_rebind_tex_clicked(self):
        print('rebind tex clicked')
        mesh_asset_path = self.mesh_path_edit.text()
        if mesh_asset_path == '':
            show_message_box('Mesh Asset Path is Empty!!!')
            return
        if not RPC.does_assset_exist_rtbool(mesh_asset_path):
            show_message_box('Mesh Asset Not Exist!!!')
            return
        if not RPC.is_mesh_asset_rtbool(mesh_asset_path):
            show_message_box('Mesh asset must be SkeletalMesh or StaticMesh!!!')
            return
        tex_asset_path_list = RPC.get_mesh_used_tex_list_rtliststring(mesh_asset_path)
        # [print(x) for x in tex_asset_path_list]
        export_tex_name_list = self._get_export_tex_name_list()
        bind_info_list = []
        for export_tex_name in export_tex_name_list:
            info = [export_tex_name, '']
            for tex_asset_path in tex_asset_path_list:
                if export_tex_name in tex_asset_path:
                    info[1] = tex_asset_path
                    break
            bind_info_list.append(info)
        self._update_bind_info(mesh_asset_path, bind_info_list)

    def _on_tex_bind_info_save_clicked(self):
        print('save clicked')
        if self._tex_bind_info_lay is None:
            show_message_box('Please rebind tex first')
            return []
        infos = []
        for i in range(self._tex_bind_info_lay.count()):
            widget = self._tex_bind_info_lay.itemAt(i).widget()
            infos.append(widget.text())
        json_obj = {}
        if os.path.exists(TEX_BIND_INFO_TXT_PATH):
            with codecs.open(TEX_BIND_INFO_TXT_PATH, 'r', encoding='utf-8') as f:
                json_obj = json.loads(f.read())
        node = {'mesh_asset_path': self._mesh_asset_path, 'preset': self.preset_selector.currentText(), 'tex_bind_info_list': ','.join(infos)}
        proj_file_path = self._get_proj_file_path()
        json_obj[proj_file_path] = node
        if not os.path.exists(TEX_BIND_INFO_FOLDER_PATH):
            os.mkdir(TEX_BIND_INFO_FOLDER_PATH)
        with codecs.open(TEX_BIND_INFO_TXT_PATH, 'w', encoding='utf-8') as f:
            f.write(json.dumps(json_obj, indent=4))

    def _get_export_tex_name_list(self):
        if os.path.exists(TEMP_TEX_FOLDER_PATH):
            shutil.rmtree(TEMP_TEX_FOLDER_PATH)
        time.sleep(1)
        export_preset = self.get_cur_preset()
        exportList = []
        for texture_set in sp_textureset.all_texture_sets():
            for stack in texture_set.all_stacks():
                exportList.append({'rootPath': str(stack)})
        config = {
            "exportShaderParams": False,
            "exportPath": TEMP_TEX_FOLDER_PATH,
            "exportList": exportList,
            "exportPresets": [{"name": "default", "maps": []}],
            "defaultExportPreset": export_preset.url(),
            "exportParameters": [
                {
                    "parameters": {
                        "fileFormat": "tga",
                        "bitDepth": "8",
                        "dithering": True,
                        "paddingAlgorithm": "infinite"
                    }
                }
            ]
        }
        sp_export.export_project_textures(config)
        time.sleep(1)
        ret = []
        for file_name in os.listdir(TEMP_TEX_FOLDER_PATH):
            ret.append(file_name[:file_name.rfind('.')])
        shutil.rmtree(TEMP_TEX_FOLDER_PATH)
        return ret

    def _get_tex_bind_info_from_file(self):
        json_obj = {}
        if os.path.exists(TEX_BIND_INFO_TXT_PATH):
            with codecs.open(TEX_BIND_INFO_TXT_PATH, 'r', encoding='utf-8') as f:
                json_obj = json.loads(f.read())
        mesh_asset_path = ''
        preset = ''
        tex_bind_info_list = []
        for k, v in json_obj.items():
            if k == self._get_proj_file_path():
                mesh_asset_path = v['mesh_asset_path']
                preset = v['preset']
                elems = v['tex_bind_info_list'].split(',')
                for i in range(int(len(elems) / 2)):
                    tex_bind_info = [elems[i * 2], elems[i * 2 + 1]]
                    tex_bind_info_list.append(tex_bind_info)
        return mesh_asset_path, preset, tex_bind_info_list

    def get_tex_bind_info(self):
        elems = []
        for i in range(self._tex_bind_info_lay.count()):
            widget = self._tex_bind_info_lay.itemAt(i).widget()
            elems.append(widget.text())
        infos = []
        for i in range(int(len(elems) / 2)):
            info = [elems[i * 2], elems[i * 2 + 1]]
            infos.append(info)
        return infos

    def has_binded(self):
        return self._tex_bind_info_lay is not None

    def _get_proj_file_path(self):
        proj_file_path = sp_project.file_path()
        return proj_file_path


class SP2UEWidget(QtWidgets.QWidget):
    def __init__(self, used_ue_node):
        super().__init__()
        self.setWindowTitle("Send To Unreal")
        main_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(main_vlay)
        ue_node_vlay = QtWidgets.QVBoxLayout()
        main_vlay.addLayout(ue_node_vlay)
        if used_ue_node is None:
            ue_node_vlay.addWidget(QtWidgets.QLabel("Unreal Editor is not linked. Please make sure Unreal Editor is opened, then restart this plugin."))
            main_vlay.addStretch()
            return
        else:
            label = QtWidgets.QLabel("Unreal Editor: {0} ({1})".format(used_ue_node.get("project_name"), used_ue_node.get("project_root")))
            ue_node_vlay.addWidget(label)

        self._tex_bind_panel = TexBindPanel()
        main_vlay.addWidget(self._tex_bind_panel)

        update_btn = QtWidgets.QPushButton('Update(Ctrl+Alt+z)')
        update_btn.setShortcut(QtGui.QKeySequence("Ctrl+Alt+z"))
        update_btn.clicked.connect(self._on_update_clicked)
        main_vlay.addWidget(update_btn)

        main_vlay.addStretch()

    def _on_update_clicked(self):
        '''
        Use tex bind info, export current stack's tex, and import used tex in UE
        '''
        if not self._tex_bind_panel.has_binded():
            show_message_box('Please bind tex first')
            return
        # export tex
        stack_name = str(sp_textureset.get_active_stack())
        export_preset = self._tex_bind_panel.get_cur_preset()
        config = {
            "exportShaderParams": False,
            "exportPath": TEMP_TEX_FOLDER_PATH,
            "exportList": [{"rootPath": stack_name}],
            "exportPresets": [{"name": "default", "maps": []}],
            "defaultExportPreset": export_preset.url(),
            "exportParameters": [
                {
                    "parameters": {
                        "fileFormat": "tga",
                        "bitDepth": "8",
                        "dithering": True,
                        "paddingAlgorithm": "infinite"
                    }
                }
            ]
        }
        sp_export.export_project_textures(config)

        # import used tex in UE
        bind_info_list = self._tex_bind_panel.get_tex_bind_info()
        file_path_list = []
        asset_folder_list = []
        asset_name_list = []
        for bind_info in bind_info_list:
            file_name = bind_info[0]
            asset_path = bind_info[1]
            if stack_name in file_name and asset_path != '':
                file_path = os.path.join(TEMP_TEX_FOLDER_PATH, file_name + '.tga').replace('\\', '/')
                pos = asset_path.rfind('/')
                asset_folder = asset_path[:pos]
                asset_name = asset_path[pos + 1:]
                file_path_list.append(file_path)
                asset_folder_list.append(asset_folder)
                asset_name_list.append(asset_name)
        RPC.reimport_tex(file_path_list, asset_folder_list, asset_name_list)
