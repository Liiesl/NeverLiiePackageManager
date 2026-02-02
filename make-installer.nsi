;--------------------------------
; nlpm User-Mode Installer (Updater Logic Added)
;--------------------------------

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"

; Define basic constants
!define PRODUCT_NAME "NeverLiie Package Manager"
!define PRODUCT_VERSION "0.1.1"
!define PRODUCT_PUBLISHER "Liiesl"
!define EXE_NAME "nlpm.exe"
!define SOURCE_EXE "main.exe" 
!define SOURCE_DIR "main.dist"

Name "${PRODUCT_NAME}"
OutFile "nlpm_setup_v${PRODUCT_VERSION}.exe"

; --- USER MODE SETTINGS ---
InstallDir "$LOCALAPPDATA\Programs\nlpm"
InstallDirRegKey HKCU "Software\${PRODUCT_NAME}" ""
RequestExecutionLevel user

;--------------------------------
; Compression
;--------------------------------
SetCompressor /SOLID lzma
SetCompressorDictSize 64

;--------------------------------
; Interface Settings
;--------------------------------
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;--------------------------------
; Variables
;--------------------------------
Var IsUpdate

;--------------------------------
; Pages
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Initialization
;--------------------------------
Function .onInit
    StrCpy $IsUpdate "0"
    ReadRegStr $0 HKCU "Software\${PRODUCT_NAME}" ""
    ${If} $0 != ""
        StrCpy $IsUpdate "1"
        StrCpy $INSTDIR $0
    ${EndIf}
FunctionEnd

;--------------------------------
; Installer Section
;--------------------------------
Section "Install" SecInstall

    ; --- PROCESS CHECK ---
    ; Check if running before doing anything
    CheckRunning:
    IfFileExists "$INSTDIR\${EXE_NAME}" 0 NotRunning
        ClearErrors
        FileOpen $0 "$INSTDIR\${EXE_NAME}" w
        IfErrors 0 CloseFile
        MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "${PRODUCT_NAME} is running. Close it to continue." IDRETRY CheckRunning IDCANCEL AbortInstall
        CloseFile:
        FileClose $0
    NotRunning:
    Goto Proceed
    AbortInstall:
    Abort
    Proceed:
    
    ; --- UPDATER LOGIC: CLEANUP ---
    ; If this is an update, delete the old files first to prevent orphans
    ${If} $IsUpdate == "1"
        DetailPrint "Update detected. Removing old files..."
        
        ; CAUTION: This removes the entire folder recursively.
        ; Ensure you don't keep user config files inside the bin folder.
        RMDir /r "$INSTDIR"
        
        ; Recreate the directory
        CreateDirectory "$INSTDIR"
    ${EndIf}

    ; --- COPY NEW FILES ---
    SetOutPath "$INSTDIR"
    File /r "${SOURCE_DIR}\*.*"
    
    ; Rename logic (if source is main.exe but you want nlpm.exe)
    Rename "$INSTDIR\${SOURCE_EXE}" "$INSTDIR\${EXE_NAME}"
    
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; --- REGISTRY ---
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKCU "Software\${PRODUCT_NAME}" "" $INSTDIR

    ; --- USER PATH UPDATE (CONDITIONAL) ---
    ; Only run this if it is a FRESH INSTALL. 
    ; If it is an update ($IsUpdate == "1"), we skip this block.
    
    ${If} $IsUpdate == "0"
        DetailPrint "Fresh install: Updating User PATH environment variable..."
        
        FileOpen $0 "$PLUGINSDIR\add_path.ps1" w
        FileWrite $0 "$$target = '$INSTDIR'$\r$\n"
        FileWrite $0 "$$oldPath = [Environment]::GetEnvironmentVariable('Path', 'User')$\r$\n"
        FileWrite $0 "if ($$oldPath -eq $$null) { $$oldPath = '' }$\r$\n"
        FileWrite $0 "if ($$oldPath -notlike '*$$target*') {$\r$\n"
        FileWrite $0 "    $$newPath = $$oldPath + ';' + $$target$\r$\n"
        FileWrite $0 "    if ($$oldPath -eq '') { $$newPath = $$target }$\r$\n" 
        FileWrite $0 "    [Environment]::SetEnvironmentVariable('Path', $$newPath, 'User')$\r$\n"
        FileWrite $0 "}$\r$\n"
        FileClose $0
        
        nsExec::ExecToLog 'powershell -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\add_path.ps1"'
        SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
    ${Else}
        DetailPrint "Update detected: Skipping PATH modification."
    ${EndIf}

SectionEnd

;--------------------------------
; Uninstaller Section
;--------------------------------
Section "Uninstall"

    ; --- USER PATH REMOVAL ---
    DetailPrint "Removing from User PATH..."
    
    FileOpen $0 "$PLUGINSDIR\remove_path.ps1" w
    FileWrite $0 "$$target = '$INSTDIR'$\r$\n"
    FileWrite $0 "$$oldPath = [Environment]::GetEnvironmentVariable('Path', 'User')$\r$\n"
    FileWrite $0 "if ($$oldPath -ne $$null) {$\r$\n"
    FileWrite $0 "    $$newPath = $$oldPath.Replace(';'+$$target, '').Replace($$target+';', '').Replace($$target, '')$\r$\n"
    FileWrite $0 "    [Environment]::SetEnvironmentVariable('Path', $$newPath, 'User')$\r$\n"
    FileWrite $0 "}$\r$\n"
    FileClose $0
    
    nsExec::ExecToLog 'powershell -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\remove_path.ps1"'
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

    Delete "$INSTDIR\${EXE_NAME}"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
    DeleteRegKey HKCU "Software\${PRODUCT_NAME}"

SectionEnd