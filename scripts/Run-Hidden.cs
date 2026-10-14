using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Web.Script.Serialization;
using System.Runtime.InteropServices;

public static class WoolRadarConsoleProbe {
    [DllImport("kernel32.dll")] private static extern IntPtr GetConsoleWindow();
    public static bool HasConsole() { return GetConsoleWindow() != IntPtr.Zero; }
}

internal static class WoolRadarHidden {
    private static void Receipt(string path, string value) {
        try { File.WriteAllText(path, value, new UTF8Encoding(false)); } catch { }
    }
    [STAThread]
    private static int Main(string[] args) {
        if (args.Length < 2) return 64;
        string mode = args[0], node = "", root;
        var nodes = new HashSet<string> { "twitter-monitor", "openmagpie", "digest-ai-agent", "clawradar", "linuxdo-monitor" };
        if (mode == "node" && args.Length == 3 && nodes.Contains(args[1])) { node = args[1]; root = args[2]; }
        else if (mode == "report" && args.Length == 2) { root = args[1]; }
        else return 64;
        try { if (!String.Equals(Path.GetFullPath(root), @"C:\WoolRadar", StringComparison.OrdinalIgnoreCase)) return 64; }
        catch { return 64; }
        string script = Path.Combine(root, "scripts", mode == "node" ? "Run-Node.ps1" : "Run-Report.ps1");
        string executable = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), @"System32\WindowsPowerShell\v1.0\powershell.exe");
        string command = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File \"" + script + "\"";
        if (mode == "node") command += " -Node " + node;
        command += " -Root \"" + root + "\"";
        string log = Path.Combine(root, "logs", "hidden-launch-" + (mode == "node" ? node : "report") + ".json");
        var info = new ProcessStartInfo(executable, command) {
            WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true,
            WindowStyle = ProcessWindowStyle.Hidden, RedirectStandardOutput = true, RedirectStandardError = true
        };
        var serializer = new JavaScriptSerializer();
        int parent = Process.GetCurrentProcess().Id;
        string start = DateTime.UtcNow.ToString("o");
        try {
            Directory.CreateDirectory(Path.GetDirectoryName(log));
            using (var child = new Process { StartInfo = info }) {
                child.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) { };
                child.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { };
                if (!child.Start()) return 127;
                try {
                child.BeginOutputReadLine(); child.BeginErrorReadLine(); child.WaitForExit();
                int exit = child.ExitCode;
                Receipt(log, serializer.Serialize(new { mode, node, started_at = start, finished_at = DateTime.UtcNow.ToString("o"),
                    launcher_pid = parent, powershell_pid = child.Id, launcher_has_console = WoolRadarConsoleProbe.HasConsole(), create_no_window = true, shell_execute = false, running = false, exit_code = exit }));
                return exit;
                } catch {
                    try { if (!child.HasExited) { child.Kill(); child.WaitForExit(); } } catch { }
                    throw;
                }
            }
        } catch (Exception error) {
            try { File.WriteAllText(log, serializer.Serialize(new { mode, node, started_at = start, launcher_pid = parent,
                create_no_window = true, running = false, exit_code = 127, error_type = error.GetType().Name }), new UTF8Encoding(false)); }
            catch { }
            return 127;
        }
    }
}
