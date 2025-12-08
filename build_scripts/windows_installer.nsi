; NSIS Installer Script for AITS Print Server
; This creates a professional Windows installer (.exe)

!define PRODUCT_NAME "AITS Print Server"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Actief IT Services"
!define PRODUCT_WEB_SITE "https://www.intevi.nl"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AITS_Print_Server.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI Settings
!include "MUI2.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "..\static\icon.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\AITS_Print_Server.exe"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; Installer attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "AITS_Print_Server_Setup.exe"
InstallDir "$PROGRAMFILES\AITS Print Server"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Copy main executable (from dist folder in build_scripts)
  File "dist\AITS_Print_Server.exe"
  
  ; Copy configuration files
  File /nonfatal "..\config.yaml.example"
  
  ; Copy static files
  SetOutPath "$INSTDIR\static"
  File /r "..\static\*.*"
  
  ; Copy documentation
  SetOutPath "$INSTDIR\docs"
  File /nonfatal "..\README.md"
  File /nonfatal "..\QUICKSTART.md"
  File /nonfatal "..\QUICK_REFERENCE.md"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\AITS Print Server"
  CreateShortCut "$SMPROGRAMS\AITS Print Server\AITS Print Server.lnk" "$INSTDIR\AITS_Print_Server.exe"
  CreateShortCut "$SMPROGRAMS\AITS Print Server\Web Configuration.lnk" "http://localhost:8888/config"
  CreateShortCut "$SMPROGRAMS\AITS Print Server\Uninstall.lnk" "$INSTDIR\uninst.exe"
  CreateShortCut "$DESKTOP\AITS Print Server.lnk" "$INSTDIR\AITS_Print_Server.exe"
  
  ; Add to startup (optional, can be configured in app)
  ; CreateShortCut "$SMSTARTUP\AITS Print Server.lnk" "$INSTDIR\AITS_Print_Server.exe"
  
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\AITS Print Server\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\AITS_Print_Server.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\AITS_Print_Server.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  
  ; Get install size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ; Remove shortcuts
  Delete "$DESKTOP\AITS Print Server.lnk"
  Delete "$SMPROGRAMS\AITS Print Server\*.*"
  RMDir "$SMPROGRAMS\AITS Print Server"
  Delete "$SMSTARTUP\AITS Print Server.lnk"
  
  ; Remove files and directories
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\AITS_Print_Server.exe"
  Delete "$INSTDIR\config.yaml.example"
  Delete "$INSTDIR\config.yaml"
  Delete "$INSTDIR\printserver.log"
  
  RMDir /r "$INSTDIR\static"
  RMDir /r "$INSTDIR\docs"
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  SetAutoClose true
SectionEnd
