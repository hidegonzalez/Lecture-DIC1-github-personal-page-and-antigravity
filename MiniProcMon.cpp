#define _WIN32_DCOM
#include <windows.h>
#include <commctrl.h>
#include <comdef.h>
#include <Wbemidl.h>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <iostream>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "wbemuuid.lib")

#define ID_BTN_START 201
#define ID_BTN_STOP 202
#define ID_BTN_CLEAR 203
#define ID_LISTVIEW 101
#define WM_NEW_EVENT (WM_USER + 1)

struct ProcEvent {
    std::wstring timeStr;
    std::wstring procName;
    std::wstring pid;
    std::wstring operation;
    std::wstring detail;
};

// Global variables
HWND hMainWnd, hListView, hBtnStart, hBtnStop, hBtnClear;
bool isCapturing = false;
std::vector<ProcEvent> events;
std::mutex eventsMutex;

std::thread wmiThread;
bool exitWmiThread = false;

// Forward declarations
void InitializeListViewColumns(HWND hWndListView);
void InsertListViewItem(HWND hWndListView, const ProcEvent& ev, int index);

void RealTimeWMIListener() {
    HRESULT hres;

    hres = CoInitializeEx(0, COINIT_MULTITHREADED); 
    if (FAILED(hres)) return;

    hres = CoInitializeSecurity(NULL, -1, NULL, NULL, RPC_C_AUTHN_LEVEL_DEFAULT, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE, NULL);
    if (FAILED(hres) && hres != RPC_E_TOO_LATE) { CoUninitialize(); return; }
    
    IWbemLocator *pLoc = NULL;
    hres = CoCreateInstance(CLSID_WbemLocator, 0, CLSCTX_INPROC_SERVER, IID_IWbemLocator, (LPVOID *)&pLoc);
    if (FAILED(hres)) { CoUninitialize(); return; }

    IWbemServices *pSvc = NULL;
    hres = pLoc->ConnectServer(_bstr_t(L"ROOT\\CIMV2"), NULL, NULL, 0, NULL, 0, 0, &pSvc);
    if (FAILED(hres)) { pLoc->Release(); CoUninitialize(); return; }

    hres = CoSetProxyBlanket(pSvc, RPC_C_AUTHN_WINNT, RPC_C_AUTHZ_NONE, NULL, RPC_C_AUTHN_LEVEL_CALL, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE);
    if (FAILED(hres)) { pSvc->Release(); pLoc->Release(); CoUninitialize(); return; }

    IEnumWbemClassObject* pEnumerator = NULL;
    // We capture process starts and stops using __InstanceOperationEvent (either Creation or Deletion)
    hres = pSvc->ExecNotificationQuery(
        _bstr_t("WQL"), 
        _bstr_t("SELECT * FROM __InstanceOperationEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_Process'"),
        WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY, NULL, &pEnumerator);
    
    if (FAILED(hres)) { pSvc->Release(); pLoc->Release(); CoUninitialize(); return; }

    IWbemClassObject *pclsObj = NULL;
    ULONG uReturn = 0;
   
    while (!exitWmiThread) {
        if (!isCapturing) {
            Sleep(250);
            continue;
        }

        HRESULT hr = pEnumerator->Next(500, 1, &pclsObj, &uReturn); // 500ms timeout
        if (0 == uReturn) continue; 
        if (FAILED(hr)) break;      

        VARIANT vtClass;
        hr = pclsObj->Get(L"__Class", 0, &vtClass, 0, 0);
        std::wstring evtClass = (vtClass.vt == VT_BSTR && vtClass.bstrVal) ? vtClass.bstrVal : L"";
        VariantClear(&vtClass);

        VARIANT vtProp;
        hr = pclsObj->Get(L"TargetInstance", 0, &vtProp, 0, 0);
        if (SUCCEEDED(hr)) {
            IUnknown* pUnk = vtProp.punkVal;
            IWbemClassObject* pProcess = NULL;

            if (SUCCEEDED(pUnk->QueryInterface(IID_IWbemClassObject, (void**)&pProcess))) {
                VARIANT valProcessName, valPID, valCommandLine;
                pProcess->Get(L"Name", 0, &valProcessName, 0, 0);
                pProcess->Get(L"ProcessId", 0, &valPID, 0, 0);
                pProcess->Get(L"CommandLine", 0, &valCommandLine, 0, 0);

                ProcEvent ev;
                
                SYSTEMTIME st;
                GetLocalTime(&st);
                wchar_t timeBuf[64];
                swprintf_s(timeBuf, 64, L"%02d:%02d:%02d.%07d", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds * 10000); // format similar to procmon
                ev.timeStr = timeBuf;

                ev.procName = (valProcessName.vt == VT_BSTR && valProcessName.bstrVal) ? valProcessName.bstrVal : L"Unknown";
                
                if (valPID.vt == VT_I4) ev.pid = std::to_wstring(valPID.lVal);
                else if (valPID.vt == VT_BSTR && valPID.bstrVal) ev.pid = valPID.bstrVal;
                else ev.pid = L"?";

                if (evtClass == L"__InstanceCreationEvent") {
                    ev.operation = L"Process Create";
                    if (valCommandLine.vt == VT_BSTR && valCommandLine.bstrVal != NULL) ev.detail = valCommandLine.bstrVal; // CMD args
                    else ev.detail = L"SUCCESS";
                } else if (evtClass == L"__InstanceDeletionEvent") {
                    ev.operation = L"Process Exit";
                    ev.detail = L"SUCCESS";
                } else {
                    ev.operation = L"Process Event";
                    ev.detail = L"";
                }

                {
                    std::lock_guard<std::mutex> lock(eventsMutex);
                    events.push_back(ev);
                }

                VariantClear(&valProcessName);
                VariantClear(&valPID);
                VariantClear(&valCommandLine);
                pProcess->Release();

                // Notify UI to update
                PostMessage(hMainWnd, WM_NEW_EVENT, 0, 0);
            }
            VariantClear(&vtProp);
        }
        pclsObj->Release();
    }

    pSvc->Release();
    pLoc->Release();
    if (pEnumerator) pEnumerator->Release();
    CoUninitialize();
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE: {
            // Enable Common Controls
            INITCOMMONCONTROLSEX icex;
            icex.dwSize = sizeof(INITCOMMONCONTROLSEX);
            icex.dwICC = ICC_LISTVIEW_CLASSES | ICC_STANDARD_CLASSES;
            InitCommonControlsEx(&icex);

            // Create Top Panel Buttons
            hBtnStart = CreateWindow(L"BUTTON", L"Start Capture", WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON,
                10, 10, 110, 30, hwnd, (HMENU)ID_BTN_START, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
            hBtnStop = CreateWindow(L"BUTTON", L"Stop Capture", WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                130, 10, 110, 30, hwnd, (HMENU)ID_BTN_STOP, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
            hBtnClear = CreateWindow(L"BUTTON", L"Clear Display", WS_TABSTOP | WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                250, 10, 110, 30, hwnd, (HMENU)ID_BTN_CLEAR, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);

            EnableWindow(hBtnStart, TRUE);
            EnableWindow(hBtnStop, FALSE);

            // Create SysListView32
            hListView = CreateWindow(WC_LISTVIEW, L"",
                WS_CHILD | LVS_REPORT | WS_VISIBLE | WS_BORDER,
                10, 50, 800, 500,
                hwnd, (HMENU)ID_LISTVIEW, (HINSTANCE)GetWindowLongPtr(hwnd, GWLP_HINSTANCE), NULL);
            
            ListView_SetExtendedListViewStyle(hListView, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);
            InitializeListViewColumns(hListView);

            exitWmiThread = false;
            wmiThread = std::thread(RealTimeWMIListener);
            break;
        }
        case WM_SIZE: {
            RECT rc;
            GetClientRect(hwnd, &rc);
            SetWindowPos(hListView, NULL, 0, 50, rc.right, rc.bottom - 50, SWP_NOZORDER);
            break;
        }
        case WM_COMMAND: {
            int wmId = LOWORD(wParam);
            if (wmId == ID_BTN_START) {
                isCapturing = true;
                EnableWindow(hBtnStart, FALSE);
                EnableWindow(hBtnStop, TRUE);
            } else if (wmId == ID_BTN_STOP) {
                isCapturing = false;
                EnableWindow(hBtnStart, TRUE);
                EnableWindow(hBtnStop, FALSE);
            } else if (wmId == ID_BTN_CLEAR) {
                std::lock_guard<std::mutex> lock(eventsMutex);
                events.clear();
                ListView_DeleteAllItems(hListView);
            }
            break;
        }
        case WM_NEW_EVENT: {
            std::lock_guard<std::mutex> lock(eventsMutex);
            int count = ListView_GetItemCount(hListView);
            
            SendMessage(hListView, WM_SETREDRAW, FALSE, 0);
            for (size_t i = count; i < events.size(); i++) {
                InsertListViewItem(hListView, events[i], (int)i);
            }
            SendMessage(hListView, WM_SETREDRAW, TRUE, 0);

            // Auto-scroll to the bottom like ProcMon
            if (events.size() > 0) {
                ListView_EnsureVisible(hListView, events.size() - 1, FALSE);
            }
            break;
        }
        case WM_DESTROY:
            isCapturing = false;
            exitWmiThread = true;
            if (wmiThread.joinable()) {
                wmiThread.join();
            }
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

void InitializeListViewColumns(HWND hWndListView) {
    LVCOLUMN lvc;
    lvc.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM | LVCF_FMT;
    lvc.fmt = LVCFMT_LEFT;

    const wchar_t* columns[] = { L"Time of Day", L"Process Name", L"PID", L"Operation", L"Detail" };
    int widths[] = { 130, 200, 70, 150, 450 };

    for (int i = 0; i < 5; i++) {
        lvc.iSubItem = i;
        lvc.pszText = (LPWSTR)columns[i];
        lvc.cx = widths[i];
        ListView_InsertColumn(hWndListView, i, &lvc);
    }
}

void InsertListViewItem(HWND hWndListView, const ProcEvent& ev, int index) {
    LVITEM lvi = {0};
    lvi.mask = LVIF_TEXT;
    lvi.iItem = index;
    lvi.iSubItem = 0;
    lvi.pszText = (LPWSTR)ev.timeStr.c_str();
    ListView_InsertItem(hWndListView, &lvi);
    ListView_SetItemText(hWndListView, index, 1, (LPWSTR)ev.procName.c_str());
    ListView_SetItemText(hWndListView, index, 2, (LPWSTR)ev.pid.c_str());
    ListView_SetItemText(hWndListView, index, 3, (LPWSTR)ev.operation.c_str());
    ListView_SetItemText(hWndListView, index, 4, (LPWSTR)ev.detail.c_str());
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    const wchar_t CLASS_NAME[] = L"MiniProcMonClass";
    
    WNDCLASS wc = { };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);

    RegisterClass(&wc);

    hMainWnd = CreateWindowEx(
        0, CLASS_NAME, L"Mini Process Monitor",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1000, 600,
        NULL, NULL, hInstance, NULL
    );

    if (hMainWnd == NULL) return 0;
    
    ShowWindow(hMainWnd, nCmdShow);

    MSG msg = { };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}
