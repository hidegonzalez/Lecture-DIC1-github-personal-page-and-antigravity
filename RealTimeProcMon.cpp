#define _WIN32_DCOM
#include <iostream>
#include <comdef.h>
#include <Wbemidl.h>
#include <string>

// Link against the WMI library
#pragma comment(lib, "wbemuuid.lib")

void RealTimeProcessMonitor() {
    HRESULT hres;

    // 1. Initialize COM
    hres = CoInitializeEx(0, COINIT_MULTITHREADED); 
    if (FAILED(hres)) {
        std::cout << "Failed to initialize COM library. Error code = 0x" << std::hex << hres << std::endl;
        return;
    }

    // 2. Set general COM security levels
    hres =  CoInitializeSecurity(
        NULL, -1, NULL, NULL, 
        RPC_C_AUTHN_LEVEL_DEFAULT, 
        RPC_C_IMP_LEVEL_IMPERSONATE, 
        NULL, EOAC_NONE, NULL);
                      
    if (FAILED(hres) && hres != RPC_E_TOO_LATE) {
        std::cout << "Failed to initialize security. Error code = 0x" << std::hex << hres << std::endl;
        CoUninitialize();
        return; 
    }
    
    // 3. Obtain the initial locator to WMI
    IWbemLocator *pLoc = NULL;
    hres = CoCreateInstance(CLSID_WbemLocator, 0, CLSCTX_INPROC_SERVER, IID_IWbemLocator, (LPVOID *)&pLoc);
 
    if (FAILED(hres)) {
        std::cout << "Failed to create IWbemLocator object. Err code = 0x" << std::hex << hres << std::endl;
        CoUninitialize();
        return;
    }

    // 4. Connect to WMI through the IWbemLocator
    IWbemServices *pSvc = NULL;
    hres = pLoc->ConnectServer(
         _bstr_t(L"ROOT\\CIMV2"), // Object path of WMI namespace
         NULL, NULL, 0, NULL, 0, 0, &pSvc);
    
    if (FAILED(hres)) {
        std::cout << "Could not connect. Error code = 0x" << std::hex << hres << std::endl;
        pLoc->Release();     
        CoUninitialize();
        return;
    }

    // 5. Set security levels on the proxy
    hres = CoSetProxyBlanket(
       pSvc, RPC_C_AUTHN_WINNT, RPC_C_AUTHZ_NONE, NULL, 
       RPC_C_AUTHN_LEVEL_CALL, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE);
    
    if (FAILED(hres)) {
        std::cout << "Could not set proxy blanket. Error code = 0x" << std::hex << hres << std::endl;
        pSvc->Release();
        pLoc->Release();     
        CoUninitialize();
        return;
    }

    // 6. Receive event notifications
    // We query for __InstanceCreationEvent of Win32_Process to get real-time process starts
    IEnumWbemClassObject* pEnumerator = NULL;
    hres = pSvc->ExecNotificationQuery(
        _bstr_t("WQL"), 
        _bstr_t("SELECT * FROM __InstanceCreationEvent WITHIN 1 WHERE TargetInstance ISA 'Win32_Process'"),
        WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY, 
        NULL, 
        &pEnumerator);
    
    if (FAILED(hres)) {
        std::cout << "Query for processes failed. Error code = 0x" << std::hex << hres << std::endl;
        pSvc->Release();
        pLoc->Release();
        CoUninitialize();
        return;
    }

    std::cout << "Listening for REAL-TIME new process creation events...\n";
    std::cout << "Try opening Notepad, Calculator, or Chrome to see events.\n";
    std::cout << "Press [Ctrl+C] to exit...\n\n";
    std::cout << "---------------------------------------------------\n";

    IWbemClassObject *pclsObj = NULL;
    ULONG uReturn = 0;
   
    // 7. Loop to listen for events
    while (pEnumerator) {
        HRESULT hr = pEnumerator->Next(WBEM_INFINITE, 1, &pclsObj, &uReturn);

        if (0 == uReturn || FAILED(hr)) break;

        VARIANT vtProp;
        // Get the TargetInstance object (which is the created Win32_Process)
        hr = pclsObj->Get(L"TargetInstance", 0, &vtProp, 0, 0);
        
        if (!FAILED(hr)) {
            IUnknown* pUnk = vtProp.punkVal;
            IWbemClassObject* pProcess = NULL;

            if (SUCCEEDED(pUnk->QueryInterface(IID_IWbemClassObject, (void**)&pProcess))) {
                VARIANT valProcessName, valPID, valCommandLine;
                
                pProcess->Get(L"Name", 0, &valProcessName, 0, 0);
                pProcess->Get(L"ProcessId", 0, &valPID, 0, 0);
                pProcess->Get(L"CommandLine", 0, &valCommandLine, 0, 0);

                // Print the real-time event
                std::wcout << L"[*] NEW PROCESS: " << valProcessName.bstrVal << L"\n"
                           << L"    PID: " << (valPID.vt == VT_I4 ? std::to_wstring(valPID.lVal) : std::wstring(valPID.bstrVal)) << L"\n";
                           
                if (valCommandLine.vt == VT_BSTR && valCommandLine.bstrVal != NULL) {
                    std::wcout << L"    CMD: " << valCommandLine.bstrVal << L"\n";
                } else {
                    std::wcout << L"    CMD: [Access Denied or Not Available]\n";
                }
                std::wcout << L"---------------------------------------------------\n";

                VariantClear(&valProcessName);
                VariantClear(&valPID);
                VariantClear(&valCommandLine);
                pProcess->Release();
            }
        }
        VariantClear(&vtProp);
        pclsObj->Release();
    }

    // Cleanup
    pSvc->Release();
    pLoc->Release();
    if(pEnumerator) pEnumerator->Release();
    CoUninitialize();
}

int main() {
    std::cout << "Sysinternals-style Real-Time Process Monitor\n";
    std::cout << "============================================\n";
    RealTimeProcessMonitor();
    return 0;
}
