import os
import sys
from PyInstaller.utils.hooks import collect_system_data_files

datas = []

if sys.platform == "win32":
    ucrt_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64",
        r"C:\Program Files (x86)\Windows Kits\10\Redist\10.0.19041.0\ucrt\DLLs\x64",
        r"C:\Program Files (x86)\Windows Kits\10\Redist\10.0.22621.0\ucrt\DLLs\x64",
        r"C:\Windows\System32"
    ]
    
    ucrt_dlls = [
        "api-ms-win-core-path-l1-1-0.dll",
        "api-ms-win-core-winrt-l1-1-0.dll",
        "api-ms-win-core-winrt-string-l1-1-0.dll",
        "api-ms-win-core-file-l1-1-0.dll",
        "api-ms-win-core-file-l1-2-0.dll",
        "api-ms-win-core-localization-l1-2-0.dll",
        "api-ms-win-core-processthreads-l1-1-0.dll",
        "api-ms-win-core-string-l1-1-0.dll",
        "api-ms-win-core-synch-l1-1-0.dll",
        "api-ms-win-core-synch-l1-2-0.dll",
        "api-ms-win-core-sysinfo-l1-1-0.dll",
        "api-ms-win-core-timezone-l1-1-0.dll",
        "api-ms-win-core-util-l1-1-0.dll",
        "api-ms-win-shcore-scaling-l1-1-1.dll",
        "api-ms-win-crt-runtime-l1-1-0.dll",
        "api-ms-win-crt-heap-l1-1-0.dll",
        "api-ms-win-crt-stdio-l1-1-0.dll",
        "api-ms-win-crt-string-l1-1-0.dll",
        "api-ms-win-crt-convert-l1-1-0.dll",
        "api-ms-win-crt-environment-l1-1-0.dll",
        "api-ms-win-crt-filesystem-l1-1-0.dll",
        "api-ms-win-crt-math-l1-1-0.dll",
        "api-ms-win-crt-multibyte-l1-1-0.dll",
        "api-ms-win-crt-process-l1-1-0.dll",
        "api-ms-win-crt-time-l1-1-0.dll",
        "api-ms-win-crt-utility-l1-1-0.dll"
    ]

    for path in ucrt_paths:
        if os.path.exists(path):
            for dll in ucrt_dlls:
                dll_path = os.path.join(path, dll)
                if os.path.exists(dll_path):
                    datas.append((dll_path, "."))
                    print(f"Adding UCRT DLL: {dll_path}")
                    
    if os.path.exists(r"C:\Windows\System32\ucrtbase.dll"):
        datas.append((r"C:\Windows\System32\ucrtbase.dll", "."))
        print("Adding ucrtbase.dll")