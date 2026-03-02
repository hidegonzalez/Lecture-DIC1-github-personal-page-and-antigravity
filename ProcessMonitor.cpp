#include <iostream>
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <iomanip>
#include <string>

// Link against Psapi.lib for MSVC (MinGW automatically links it usually)
#pragma comment(lib, "psapi.lib")

// Function to get memory usage of a process
SIZE_T GetProcessMemoryUsage(DWORD processID) {
    // Use PROCESS_QUERY_INFORMATION and PROCESS_VM_READ to get memory info
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, processID);
    if (hProcess == NULL) {
        return 0; // Access denied or process no longer exists (e.g. System Idle Process)
    }

    PROCESS_MEMORY_COUNTERS pmc;
    SIZE_T memUsage = 0;
    if (GetProcessMemoryInfo(hProcess, &pmc, sizeof(pmc))) {
        memUsage = pmc.WorkingSetSize; // Working set size in bytes
    }

    CloseHandle(hProcess);
    return memUsage;
}

// A more advanced Windows Process Monitor
void PrintProcesses() {
    HANDLE hProcessSnap;
    PROCESSENTRY32 pe32;

    // Take a snapshot of all processes in the system
    hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcessSnap == INVALID_HANDLE_VALUE) {
        std::cerr << "CreateToolhelp32Snapshot failed. Error: " << GetLastError() << std::endl;
        return;
    }

    // Set the size of the structure before using it
    pe32.dwSize = sizeof(PROCESSENTRY32);

    // Retrieve information about the first process
    if (!Process32First(hProcessSnap, &pe32)) {
        std::cerr << "Process32First failed. Error: " << GetLastError() << std::endl;
        CloseHandle(hProcessSnap);
        return;
    }

    // Print table header
    std::cout << std::left 
              << std::setw(35) << "Process Name" 
              << std::setw(10) << "PID" 
              << std::setw(10) << "PPID" 
              << std::setw(10) << "Threads" 
              << std::setw(15) << "Memory (KB)" << std::endl;
    std::cout << std::string(80, '-') << std::endl;

    // Walk the snapshot of processes and display information
    do {
        // Get memory usage in KB
        SIZE_T memUsageBytes = GetProcessMemoryUsage(pe32.th32ProcessID);
        SIZE_T memUsageKB = memUsageBytes / 1024;

        std::cout << std::left 
                  << std::setw(35) << pe32.szExeFile 
                  << std::setw(10) << pe32.th32ProcessID 
                  << std::setw(10) << pe32.th32ParentProcessID 
                  << std::setw(10) << pe32.cntThreads;
                  
        if (memUsageKB > 0) {
            std::cout << std::setw(15) << memUsageKB;
        } else {
            std::cout << std::setw(15) << "N/A"; // Access Denied for System processes unless run as Admin
        }
        std::cout << std::endl;

    } while (Process32Next(hProcessSnap, &pe32));

    // Clean up the snapshot object
    CloseHandle(hProcessSnap);
}

// Function to clear the console cleanly
void ClearScreen() {
    HANDLE hStdOut = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_SCREEN_BUFFER_INFO csbi;
    DWORD count;
    DWORD cellCount;
    COORD homeCoords = { 0, 0 };

    if (hStdOut == INVALID_HANDLE_VALUE) return;

    if (!GetConsoleScreenBufferInfo(hStdOut, &csbi)) return;
    cellCount = csbi.dwSize.X * csbi.dwSize.Y;

    if (!FillConsoleOutputCharacter(hStdOut, (TCHAR) ' ', cellCount, homeCoords, &count)) return;
    if (!FillConsoleOutputAttribute(hStdOut, csbi.wAttributes, cellCount, homeCoords, &count)) return;

    SetConsoleCursorPosition(hStdOut, homeCoords);
}

int main() {
    bool liveMode = false;
    char choice;
    
    std::cout << "Windows Process Monitor - Advanced" << std::endl;
    std::cout << "==================================" << std::endl;
    std::cout << "Do you want to run in live monitoring mode? (y/n): ";
    std::cin >> choice;

    if (choice == 'y' || choice == 'Y') {
        liveMode = true;
    }

    if (liveMode) {
        // Active monitoring with polling
        while (true) {
            ClearScreen();
            std::cout << "Windows Process Monitor (Refreshing every 2 seconds)" << std::endl;
            std::cout << "Press [Ctrl+C] to exit." << std::endl;
            std::cout << "=====================================================" << std::endl;
            PrintProcesses();
            Sleep(2000); // 2000 ms = 2 seconds heartbeat
        }
    } else {
        // One-time static print
        std::cout << "\nStatic Process List:" << std::endl;
        std::cout << "=====================================================" << std::endl;
        PrintProcesses();
        std::cout << "\nPress Enter to exit...";
        
        // Clear cin buffer before waiting for Enter
        std::cin.ignore(10000, '\n');
        std::cin.get();
    }

    return 0;
}
