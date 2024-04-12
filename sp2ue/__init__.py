"""Module to export texture to Unreal Engine"""

import importlib
import sp2ue.sp2uemain as sp2uemain
import sp2ue.unreal_remote.RPC as ue_rpc
import sp2ue.sp2ue_ui as sp2ue_ui

importlib.reload(sp2uemain)
importlib.reload(ue_rpc)
importlib.reload(sp2ue_ui)

SP2UE_PLUGIN = None


def start_plugin() -> None:
    global SP2UE_PLUGIN
    SP2UE_PLUGIN = sp2uemain.SP2UEMain()


def close_plugin() -> None:
    global SP2UE_PLUGIN
    del SP2UE_PLUGIN
