using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;

[assembly: SupportedOSPlatform("windows")]

internal static class Program
{
    private const uint Query=0x8, Duplicate=0x2, AssignPrimary=0x1;
    private const uint DisableMaxPrivilege=0x1, IntegrityAttribute=0x20;
    private static readonly JsonSerializerOptions Json=new(){WriteIndented=true};
    private sealed class ProbeFailure(string api,int code):Exception(api+" failed with Win32 code "+code)
    { public string Api {get;}=api;public int Code {get;}=code; }

    public static int Main(string[] args)
    {
        if(!OperatingSystem.IsWindows()) {Console.Error.WriteLine("Actual Windows token APIs required.");return 2;}
        string? output=null;
        try
        {
            if(args.Length==2&&args[0]=="--identity")
            { output=Path.GetFullPath(args[1]);Write(output,Identity());return 0; }
            if(args.Length==3&&args[0]=="--identity-pid")
            {
                output=Path.GetFullPath(args[2]);int pid=int.Parse(args[1]);
                IntPtr process=OpenProcess(0x1000,false,pid);
                if(process==IntPtr.Zero)throw Failed("OpenProcess(QueryLimitedInformation)");
                try
                {
                    if(!OpenProcessToken(process,Query|Duplicate,out IntPtr token))throw Failed("OpenProcessToken(Recipient)");
                    try {Write(output,Identity(token,pid));return 0;} finally {CloseHandle(token);}
                }
                finally {CloseHandle(process);}
            }
            if(args.Length!=5||args[0]!="--launch")throw new ArgumentException("Usage: --identity OUTPUT | --launch SHELL CHILD_SCRIPT BUNDLE OUTPUT_DIRECTORY");
            string shell=RequiredFile(args[1]),child=RequiredFile(args[2]),bundle=Path.GetFullPath(args[3]);
            output=Path.GetFullPath(args[4]);Directory.CreateDirectory(output);
            return Launch(shell,child,bundle,output);
        }
        catch(Exception error) when(error is ProbeFailure or ArgumentException or FormatException or OverflowException or IOException or UnauthorizedAccessException or Win32Exception)
        {
            var failure=new {status="inconclusive",error=error.Message,api=(error as ProbeFailure)?.Api,win32_code=(error as ProbeFailure)?.Code};
            if(output!=null)
            {
                string path=args.Length>0&&args[0].StartsWith("--identity",StringComparison.Ordinal)?output:Path.Combine(output,"launch-failure.json");
                try {Write(path,failure);} catch(IOException) { }
            }
            Console.Error.WriteLine(JsonSerializer.Serialize(failure,Json));return 2;
        }
    }

    private static string RequiredFile(string name)
    {string p=Path.GetFullPath(name);if(!File.Exists(p))throw new ArgumentException("Missing explicit input: "+p);return p;}
    private static void Write(string path,object value)=>File.WriteAllText(path,JsonSerializer.Serialize(value,Json)+"\n",new UTF8Encoding(false));
    private static ProbeFailure Failed(string api)=>new(api,Marshal.GetLastWin32Error());
    private static int TokenInt(IntPtr token,int kind)
    {
        IntPtr p=Marshal.AllocHGlobal(4);
        try {if(!GetTokenInformation(token,kind,p,4,out _))throw Failed("GetTokenInformation("+kind+")");return Marshal.ReadInt32(p);}
        finally {Marshal.FreeHGlobal(p);}
    }
    private static IntPtr TokenBuffer(IntPtr token,int kind)
    {
        GetTokenInformation(token,kind,IntPtr.Zero,0,out int size);
        if(size<=0)throw Failed("GetTokenInformation(size,"+kind+")");
        IntPtr p=Marshal.AllocHGlobal(size);
        if(!GetTokenInformation(token,kind,p,size,out _)) {Marshal.FreeHGlobal(p);throw Failed("GetTokenInformation("+kind+")");}
        return p;
    }
    private static object Identity()
    {
        using var identity=WindowsIdentity.GetCurrent();
        return Identity(identity.AccessToken.DangerousGetHandle(),Environment.ProcessId);
    }
    private static object Identity(IntPtr token,int observedPid)
    {
        using var identity=new WindowsIdentity(token);
        var groups=new List<object>();bool adminDenyOnly=false;
        IntPtr p=TokenBuffer(token,2);
        try
        {
            int count=Marshal.ReadInt32(p),offset=IntPtr.Size==8?8:4,size=Marshal.SizeOf<SidAndAttributes>();
            for(int i=0;i<count;i++)
            {
                var entry=Marshal.PtrToStructure<SidAndAttributes>(IntPtr.Add(p,offset+i*size));
                string sid=new SecurityIdentifier(entry.Sid).Value;
                if(sid=="S-1-5-32-544") {adminDenyOnly=(entry.Attributes&0x10)!=0;groups.Add(new {sid,attributes=entry.Attributes,deny_only=adminDenyOnly});}
            }
        }
        finally {Marshal.FreeHGlobal(p);}
        int integrity;
        p=TokenBuffer(token,25);
        try
        {
            var label=Marshal.PtrToStructure<SidAndAttributes>(p);
            var parts=new SecurityIdentifier(label.Sid).Value.Split('-');integrity=int.Parse(parts[^1]);
        }
        finally {Marshal.FreeHGlobal(p);}
        string userHash=Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(identity.User!.Value)));
        return new {pid=observedPid,observer_pid=Environment.ProcessId,administrator=new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator),elevated=TokenInt(token,20)!=0,elevation_type=TokenInt(token,18),integrity_rid=integrity,medium_integrity=integrity==8192,administrator_sid_deny_only=adminDenyOnly,administrator_group=groups,user_sid_sha256=userHash,scope="Actual process token; restricted same-user hosted execution is not a physical ordinary-user device or Windows10/11 assessment."};
    }

    private static int Launch(string shell,string child,string bundle,string output)
    {
        if(!OpenProcessToken(GetCurrentProcess(),Query|Duplicate|AssignPrimary|0x80,out IntPtr current))throw Failed("OpenProcessToken");
        IntPtr selected=IntPtr.Zero,admin=IntPtr.Zero,medium=IntPtr.Zero;
        IntPtr stdin=IntPtr.Zero,stdout=IntPtr.Zero,stderr=IntPtr.Zero;
        string method="",apiUsed="";var attempts=new List<object>();
        try
        {
            Write(Path.Combine(output,"parent-token.json"),Identity());
            // Prefer a real UAC-linked limited token when the host actually supplies one.
            IntPtr linked=Marshal.AllocHGlobal(IntPtr.Size);
            try
            {
                if(GetTokenInformation(current,19,linked,IntPtr.Size,out _))
                {
                    IntPtr candidate=Marshal.ReadIntPtr(linked);
                    if(TokenInt(candidate,18)==3) {selected=candidate;method="linked_limited_token";}
                    else {CloseHandle(candidate);attempts.Add(new {api="TokenLinkedToken",result="not_limited"});}
                }
                else attempts.Add(new {api="TokenLinkedToken",win32_code=Marshal.GetLastWin32Error()});
            }
            finally {Marshal.FreeHGlobal(linked);}
            if(selected==IntPtr.Zero)
            {
                if(!ConvertStringSidToSid("S-1-5-32-544",out admin))throw Failed("ConvertStringSidToSid(Admin)");
                var disabled=new[]{new SidAndAttributes {Sid=admin,Attributes=0}};
                if(!CreateRestrictedToken(current,DisableMaxPrivilege,1,disabled,0,IntPtr.Zero,0,IntPtr.Zero,out selected))throw Failed("CreateRestrictedToken");
                if(!ConvertStringSidToSid("S-1-16-8192",out medium))throw Failed("ConvertStringSidToSid(Medium)");
                var label=new SidAndAttributes {Sid=medium,Attributes=IntegrityAttribute};
                if(!SetTokenInformation(selected,25,ref label,Marshal.SizeOf<SidAndAttributes>()+GetLengthSid(medium)))throw Failed("SetTokenInformation(MediumIntegrity)");
                method="restricted_same_user_admin_deny_only_medium_integrity";
            }
            Write(Path.Combine(output,"token-method.json"),new {token_method=method,attempts});
            string assembly=Path.GetFullPath(typeof(Program).Assembly.Location);
            string line=string.Join(" ",new[]{shell,"-NoLogo","-NoProfile","-NonInteractive","-File",child,"-Bundle",bundle,"-Launcher",assembly,"-Output",output,"-Shell",shell}.Select(Quote));
            // Give the owned PowerShell actual inheritable standard handles. A process
            // with no valid stdout can fail native command creation before the app.
            var security=new SecurityAttributes {Length=Marshal.SizeOf<SecurityAttributes>(),Inherit=true};
            stdin=CreateFile("NUL",0x80000000,3,ref security,3,0x80,IntPtr.Zero);
            if(stdin==new IntPtr(-1))throw Failed("CreateFile(NUL)");
            stdout=CreateFile(Path.Combine(output,"selected-child.stdout.txt"),0x40000000,1,ref security,1,0x80,IntPtr.Zero);
            if(stdout==new IntPtr(-1))throw Failed("CreateFile(selected stdout)");
            stderr=CreateFile(Path.Combine(output,"selected-child.stderr.txt"),0x40000000,1,ref security,1,0x80,IntPtr.Zero);
            if(stderr==new IntPtr(-1))throw Failed("CreateFile(selected stderr)");
            var startup=new StartupInfo {Cb=Marshal.SizeOf<StartupInfo>(),Flags=0x100,StdInput=stdin,StdOutput=stdout,StdError=stderr};
            ProcessInformation process;
            bool launched=CreateProcessAsUser(selected,shell,new StringBuilder(line),IntPtr.Zero,IntPtr.Zero,true,0,IntPtr.Zero,output,ref startup,out process);
            if(launched)apiUsed="CreateProcessAsUser";
            else
            {
                int launchError=Marshal.GetLastWin32Error();
                attempts.Add(new {api="CreateProcessAsUser",win32_code=launchError});
                Write(Path.Combine(output,"launch-attempts.json"),new {token_method=method,attempts});
                throw new ProbeFailure("CreateProcessAsUser(inheritable stdio)",launchError);
            }
            try
            {
                Write(Path.Combine(output,"launch.json"),new {status="launched",token_method=method,launch_api=apiUsed,pid=process.ProcessId,attempts,scope="Only the selected child token is restricted; parent privileges, accounts, URLACL and execution policy unchanged."});
                uint wait=WaitForSingleObject(process.Process,55000);
                if(wait==0x102)
                {
                    try {Process.GetProcessById((int)process.ProcessId).Kill(true);}catch(ArgumentException) { }
                    Write(Path.Combine(output,"launch-result.json"),new {status="inconclusive",reason="Owned token child exceeded55seconds; terminated only its process tree.",token_method=method});return 2;
                }
                if(wait!=0)throw Failed("WaitForSingleObject");
                if(!GetExitCodeProcess(process.Process,out uint code))throw Failed("GetExitCodeProcess");
                Write(Path.Combine(output,"launch-result.json"),new {status="completed",child_exit_code=code,token_method=method,launch_api=apiUsed,attempts});return 0;
            }
            finally {CloseHandle(process.Thread);CloseHandle(process.Process);}
        }
        finally {foreach(var handle in new[]{stdin,stdout,stderr})if(handle!=IntPtr.Zero&&handle!=new IntPtr(-1))CloseHandle(handle);if(selected!=IntPtr.Zero)CloseHandle(selected);if(admin!=IntPtr.Zero)LocalFree(admin);if(medium!=IntPtr.Zero)LocalFree(medium);CloseHandle(current);}
    }
    private static string Quote(string value)
    {
        var b=new StringBuilder("\"");int backslashes=0;
        foreach(char c in value)
        {
            if(c=='\\') {backslashes++;continue;}
            if(c=='\"') {b.Append('\\',backslashes*2+1);b.Append(c);backslashes=0;continue;}
            b.Append('\\',backslashes);backslashes=0;b.Append(c);
        }
        b.Append('\\',backslashes*2);return b.Append('"').ToString();
    }
    [StructLayout(LayoutKind.Sequential)] private struct SecurityAttributes {public int Length;public IntPtr Descriptor;[MarshalAs(UnmanagedType.Bool)]public bool Inherit;}
    [DllImport("kernel32.dll",EntryPoint="CreateFileW",CharSet=CharSet.Unicode,SetLastError=true)] private static extern IntPtr CreateFile(string name,uint access,uint share,ref SecurityAttributes security,uint creation,uint attributes,IntPtr template);
    [StructLayout(LayoutKind.Sequential)] private struct SidAndAttributes {public IntPtr Sid;public uint Attributes;}
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] private struct StartupInfo
    {public int Cb;public string? Reserved;public string? Desktop;public string? Title;public uint X,Y,XSize,YSize,XCountChars,YCountChars,FillAttribute,Flags;public ushort ShowWindow,Reserved2;public IntPtr ReservedPointer,StdInput,StdOutput,StdError;}
    [StructLayout(LayoutKind.Sequential)] private struct ProcessInformation {public IntPtr Process,Thread;public uint ProcessId,ThreadId;}
    [DllImport("kernel32.dll")] private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll",SetLastError=true)] private static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] private static extern IntPtr LocalFree(IntPtr handle);
    [DllImport("advapi32.dll",SetLastError=true)] private static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
    [DllImport("advapi32.dll",SetLastError=true)] private static extern bool GetTokenInformation(IntPtr token,int kind,IntPtr information,int length,out int required);
    [DllImport("advapi32.dll",SetLastError=true)] private static extern bool SetTokenInformation(IntPtr token,int kind,ref SidAndAttributes information,int length);
    [DllImport("advapi32.dll",SetLastError=true)] private static extern bool CreateRestrictedToken(IntPtr token,uint flags,uint disabledCount,[In] SidAndAttributes[] disabled,uint deletedCount,IntPtr deleted,uint restrictedCount,IntPtr restricted,out IntPtr result);
    [DllImport("advapi32.dll",EntryPoint="ConvertStringSidToSidW",CharSet=CharSet.Unicode,SetLastError=true)] private static extern bool ConvertStringSidToSid(string text,out IntPtr sid);
    [DllImport("advapi32.dll")] private static extern int GetLengthSid(IntPtr sid);
    [DllImport("advapi32.dll",EntryPoint="CreateProcessAsUserW",CharSet=CharSet.Unicode,SetLastError=true)] private static extern bool CreateProcessAsUser(IntPtr token,string application,StringBuilder command,IntPtr processAttributes,IntPtr threadAttributes,bool inherit,uint flags,IntPtr environment,string directory,ref StartupInfo startup,out ProcessInformation process);
    [DllImport("advapi32.dll",EntryPoint="CreateProcessWithTokenW",CharSet=CharSet.Unicode,SetLastError=true)] private static extern bool CreateProcessWithToken(IntPtr token,uint logonFlags,string application,StringBuilder command,uint flags,IntPtr environment,string directory,ref StartupInfo startup,out ProcessInformation process);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
    [DllImport("kernel32.dll",SetLastError=true)] private static extern bool GetExitCodeProcess(IntPtr process,out uint code);
}
