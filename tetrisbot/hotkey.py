"""Global hotkey via Carbon RegisterEventHotKey (no Accessibility permission needed;
the key combo is consumed so the browser never sees it)."""
import ctypes

_carbon = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Carbon.framework/Carbon")


class _HotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]


class _EventTypeSpec(ctypes.Structure):
    _fields_ = [("eventClass", ctypes.c_uint32), ("eventKind", ctypes.c_uint32)]


_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
_carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
_carbon.InstallEventHandler.argtypes = [ctypes.c_void_p, _HANDLER, ctypes.c_uint32,
                                        ctypes.POINTER(_EventTypeSpec), ctypes.c_void_p,
                                        ctypes.POINTER(ctypes.c_void_p)]
_carbon.InstallEventHandler.restype = ctypes.c_int32
_carbon.RegisterEventHotKey.argtypes = [ctypes.c_uint32, ctypes.c_uint32, _HotKeyID, ctypes.c_void_p,
                                        ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
_carbon.RegisterEventHotKey.restype = ctypes.c_int32


def _fourcc(s):
    return int.from_bytes(s.encode(), "big")


CMD, SHIFT, OPTION, CONTROL = 0x100, 0x200, 0x800, 0x1000
KEY_K = 40

_keep = []  # keep ctypes callbacks alive


def register(callback, keycode=KEY_K, modifiers=CMD | SHIFT):
    """Call `callback()` on the main thread whenever the hotkey is pressed.
    Requires a running NSApplication / Carbon event loop. Returns True on success."""

    def handler(next_handler, event, user_data):
        try:
            callback()
        except Exception as e:  # never let an exception cross into Carbon
            print("hotkey callback error:", e)
        return 0

    cb = _HANDLER(handler)
    spec = _EventTypeSpec(_fourcc("keyb"), 5)  # kEventClassKeyboard, kEventHotKeyPressed
    ref = ctypes.c_void_p()
    target = _carbon.GetApplicationEventTarget()
    if _carbon.InstallEventHandler(target, cb, 1, ctypes.byref(spec), None, ctypes.byref(ref)) != 0:
        return False
    hk_ref = ctypes.c_void_p()
    status = _carbon.RegisterEventHotKey(keycode, modifiers, _HotKeyID(_fourcc("TBot"), 1), target, 0,
                                         ctypes.byref(hk_ref))
    _keep.extend([cb, spec, ref, hk_ref])
    return status == 0
