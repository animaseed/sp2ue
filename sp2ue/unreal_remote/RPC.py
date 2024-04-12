import sp2ue.unreal_remote.remote_execution_inst as ue_re_inst

RE = ue_re_inst.RE


class _RPC:
    '''
    For UE remote call
    '''

    def __getattr__(self, __name: str):
        '''
        Translate local call to UE remote call
        Args:
            __name: remote call name (defined in ingest_functions.py)
        Returns:
            function object for remote call
        '''

        def excecute(*args, **kwargs):
            arg_str_list = []
            for arg in args:
                if type(arg) is str:
                    arg_str = "'''" + arg + "'''"
                else:
                    arg_str = str(arg)
                arg_str_list.append(arg_str)
            cmd = 'ingest_functions.IngestFunctions.{0}({1})'.format(__name, ','.join(arg_str_list))
            # print('cmd:', cmd)
            res = RE.run_command(cmd, exec_mode=ue_re_inst.ue_re.MODE_EVAL_STATEMENT)
            return self._get_result(res)

        return excecute

    def _get_result(self, res):
        '''
        Translate remote call result from string format to its real format

        Args:
            res: remote call result in string format

        Returns:
            remote call result in its real format
        '''
        result = res['result']
        cmd: str = res['command']
        func_end_pos = cmd.find('(')
        func_start_pos = cmd.rfind('.', 0, func_end_pos)
        func_name = cmd[func_start_pos + 1:func_end_pos]
        return_type = func_name.split('_')[-1]
        if return_type == 'rtbool':
            if result == 'True':
                return True
            else:
                return False
        elif return_type == 'rtliststring':
            elem_str_list = [x.strip() for x in result[1:-1].split(',')]
            elem_list = [x[1:-1] for x in elem_str_list]
            return elem_list
        else:
            return None


RPC = _RPC()
