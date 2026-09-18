# 손글씨 숫자 인식기 바로가기를 바탕 화면과 시작 메뉴에 만든다.
#
# 실행 방법: powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
#
# - pythonw.exe로 실행하므로 검은 콘솔 창이 뜨지 않는다.
# - 바로가기에 앱 ID를 넣어, 작업 표시줄에 고정한 아이콘과 실행 중인 창이 하나로 묶이게 한다.
# - 시작 메뉴에도 만들어 두면 실행 중인 창을 작업 표시줄에 바로 고정할 수 있다.

$ErrorActionPreference = 'Stop'

# ----- 설정값 -----
$프로젝트_폴더 = $PSScriptRoot
$바로가기_이름 = '손글씨 숫자 인식기'
$앱_ID = 'Logistex.MnistHandwriting'   # app.py의 앱_ID와 반드시 같아야 한다
$앱_파일 = Join-Path $프로젝트_폴더 'app.py'
$아이콘_파일 = Join-Path $프로젝트_폴더 'app_icon.ico'

# torch가 설치된 Python 3.13의 pythonw.exe를 찾는다 (py 기본값은 패키지가 없는 3.14)
$python_경로 = (& py -3.13 -c 'import sys; print(sys.executable)').Trim()
$pythonw_경로 = Join-Path (Split-Path $python_경로) 'pythonw.exe'
if (-not (Test-Path $pythonw_경로)) { throw "pythonw.exe를 찾지 못했습니다: $pythonw_경로" }

# 아이콘 파일이 없으면 먼저 만든다
if (-not (Test-Path $아이콘_파일)) { & $python_경로 (Join-Path $프로젝트_폴더 'make_icon.py') }

# 바로가기(.lnk)에 앱 ID 속성을 쓰기 위한 윈도우 API 연결
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class 바로가기_속성
{
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    struct PropertyKey { public Guid fmtid; public uint pid; }

    [StructLayout(LayoutKind.Explicit)]
    struct PropVariant
    {
        [FieldOffset(0)] public ushort vt;
        [FieldOffset(8)] public IntPtr 값;
    }

    [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"),
     InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IPropertyStore
    {
        void GetCount(out uint 개수);
        void GetAt(uint 순번, out PropertyKey 키);
        void GetValue(ref PropertyKey 키, out PropVariant 값);
        void SetValue(ref PropertyKey 키, ref PropVariant 값);
        void Commit();
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    static extern void SHGetPropertyStoreFromParsingName(
        string 경로, IntPtr bc, int 플래그, ref Guid iid,
        [MarshalAs(UnmanagedType.Interface)] out IPropertyStore 저장소);

    public static void 앱_ID_설정(string 바로가기_경로, string 앱_ID)
    {
        Guid iid = typeof(IPropertyStore).GUID;
        IPropertyStore 저장소;
        SHGetPropertyStoreFromParsingName(바로가기_경로, IntPtr.Zero, 2 /* 읽기쓰기 */, ref iid, out 저장소);

        // System.AppUserModel.ID 속성 키
        PropertyKey 키 = new PropertyKey {
            fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), pid = 5 };
        PropVariant 값 = new PropVariant { vt = 31 /* 유니코드 문자열 */,
                                           값 = Marshal.StringToCoTaskMemUni(앱_ID) };
        try
        {
            저장소.SetValue(ref 키, ref 값);
            저장소.Commit();
        }
        finally
        {
            Marshal.FreeCoTaskMem(값.값);
            Marshal.ReleaseComObject(저장소);
        }
    }
}
'@

function 바로가기_만들기([string]$저장_폴더) {
    $경로 = Join-Path $저장_폴더 "$바로가기_이름.lnk"
    $셸 = New-Object -ComObject WScript.Shell
    $바로가기 = $셸.CreateShortcut($경로)
    $바로가기.TargetPath = $pythonw_경로
    $바로가기.Arguments = "`"$앱_파일`""
    $바로가기.WorkingDirectory = $프로젝트_폴더
    $바로가기.IconLocation = "$아이콘_파일,0"
    $바로가기.Description = '마우스로 쓴 숫자를 인식하는 MNIST CNN 앱'
    $바로가기.Save()
    [바로가기_속성]::앱_ID_설정($경로, $앱_ID)
    Write-Host "바로가기 생성: $경로"
}

바로가기_만들기 ([Environment]::GetFolderPath('Desktop'))
바로가기_만들기 ([Environment]::GetFolderPath('Programs'))   # 시작 메뉴
