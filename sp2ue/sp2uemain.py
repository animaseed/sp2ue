'''Main class for sp2ue plugin'''
import os
import time

import substance_painter.ui as sp_ui
import substance_painter.event as sp_event
import substance_painter.project as sp_project

import sp2ue.unreal_remote.remote_execution_inst as ue_re_inst
import sp2ue.unreal_remote.RPC as ue_re_rpc
import sp2ue.sp2ue_ui as sp2ue_ui

RE = ue_re_inst.RE
RPC = ue_re_rpc.RPC


class SP2UEMain:
    '''
    Main class for sp2ue plugin
    '''

    def __init__(self):
        self.plugin_widgets = []
        if sp_project.is_open():
            self._init_after_project_opened(None)
        else:
            sp_event.DISPATCHER.connect(sp_event.ProjectOpened, self._init_after_project_opened)

    def __del__(self):
        for widget in self.plugin_widgets:
            sp_ui.delete_ui_element(widget)
        self._stop_re()

    def _init_after_project_opened(self, e):
        used_ue_node = self._start_re()
        if used_ue_node is not None:
            self._ingest_functions_to_ue()
            print('UE Linked')
        self._init_ui(used_ue_node)

    def _start_re(self):
        self._stop_re()
        RE.start()
        time.sleep(1.0)
        ue_nodes = RE.remote_nodes
        if len(ue_nodes) == 0:
            return None
        else:
            used_ue_node = ue_nodes[0]
            RE.open_command_connection(used_ue_node)
            return used_ue_node

    def _stop_re(self):
        if RE.has_command_connection():
            RE.close_command_connection()
        RE.stop()

    def _ingest_functions_to_ue(self):
        '''
        Ingest function in ingest_function.py to UE python context
        '''

        ingest_fuctions_py_dir = os.path.join(os.path.dirname(__file__), 'unreal_remote')
        cmd_to_add_path = 'sys.path.append("{0}")'.format(ingest_fuctions_py_dir)
        cmd_to_add_path = cmd_to_add_path.replace('\\', '/')
        cmds = [
            'import sys',
            cmd_to_add_path,
            'import importlib',
            'import ingest_functions',
            'importlib.reload(ingest_functions)',
            'print("ingest function complete")'
        ]
        for cmd in cmds:
            RE.run_command(cmd)

    def _init_ui(self, used_ue_node):
        '''
        Init plugin UI

        Args:
            used_ue_node: node to represent for Unreal Editor
        '''

        self.window = sp2ue_ui.SP2UEWidget(used_ue_node)
        sp_ui.add_dock_widget(self.window)
        self.plugin_widgets.append(self.window)
