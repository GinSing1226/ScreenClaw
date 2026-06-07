using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

using Vortice.Direct3D;
using Vortice.Direct3D11;
using Vortice.DXGI;

using Windows.Graphics.Capture;
using Windows.Graphics.DirectX;
using Windows.Graphics.DirectX.Direct3D11;

using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;

using WinRT;

namespace ScreenClawWinCapture;

/// <summary>
/// 通过 Windows Graphics Capture 截取指定窗口。
/// 使用 .NET WinRT 投影的 TryCreateFromWindowId 创建捕获项。
/// </summary>
static class CaptureService
{
    private static ID3D11Device? _d3dDevice;
    private static ID3D11DeviceContext? _d3dContext;
    private static IDirect3DDevice? _winrtDevice;
    private static readonly object _lock = new();

    /// <summary>
    /// 截取指定窗口，返回 PNG 图片路径。
    /// </summary>
    public static CaptureResult CaptureWindow(IntPtr hwnd)
    {
        lock (_lock)
        {
            try
            {
                EnsureDevice();

                var item = GraphicsCaptureItem.TryCreateFromWindowId(
                    new Windows.UI.WindowId((ulong)hwnd));

                if (item == null)
                    return new CaptureResult(false, Error: "Cannot create capture item for this window (null)");

                return DoCapture(item);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[wincapture] CaptureWindow error: {ex}");
                return new CaptureResult(false, Error: ex.Message);
            }
        }
    }

    private static void EnsureDevice()
    {
        if (_d3dDevice != null) return;

        // 创建 D3D11 设备
        D3D11.D3D11CreateDevice(
            IntPtr.Zero,
            DriverType.Hardware,
            DeviceCreationFlags.BgraSupport,
            null!,
            out _d3dDevice,
            out _d3dContext);

        // 获取 IDXGIDevice -> 创建 WinRT IDirect3DDevice
        using var dxgiDevice = _d3dDevice.QueryInterface<IDXGIDevice>();
        _winrtDevice = CreateWinRTDeviceFromDXGI(dxgiDevice);
    }

    /// <summary>
    /// 将 IDXGIDevice 转换为 WinRT IDirect3DDevice。
    /// 使用 MarshalInspectable 创建正确的 WinRT 投影对象。
    /// </summary>
    private static IDirect3DDevice CreateWinRTDeviceFromDXGI(IDXGIDevice dxgiDevice)
    {
        var ptr = Interop.CreateDirect3D11DeviceFromDXGIDevice(dxgiDevice.NativePointer);
        if (ptr == IntPtr.Zero)
            throw new InvalidOperationException("CreateDirect3D11DeviceFromDXGIDevice failed");

        return MarshalInspectable<IDirect3DDevice>.FromAbi(ptr);
    }

    private static CaptureResult DoCapture(GraphicsCaptureItem item)
    {
        var size = item.Size;
        int width = size.Width;
        int height = size.Height;

        if (width <= 0 || height <= 0)
            return new CaptureResult(false, Error: "Window has invalid size");

        Direct3D11CaptureFramePool? framePool = null;
        GraphicsCaptureSession? session = null;
        ID3D11Texture2D? stagingTexture = null;

        try
        {
            Console.WriteLine($"[wincapture] Creating FramePool: device={_winrtDevice}, size={width}x{height}");

            framePool = Direct3D11CaptureFramePool.Create(
                _winrtDevice!,
                DirectXPixelFormat.B8G8R8A8UIntNormalized,
                2,
                new Windows.Graphics.SizeInt32(width, height));
            Console.WriteLine($"[wincapture] FramePool created");

            session = framePool.CreateCaptureSession(item);
            session.IsCursorCaptureEnabled = false;
            Console.WriteLine($"[wincapture] Session created, Starting capture...");
            session.StartCapture();
            Console.WriteLine("[wincapture] Capture started, polling for frame...");

            // 轮询方式获取帧 — 避免 FrameArrived 事件在控制台应用中不触发的问题
            Direct3D11CaptureFrame? capturedFrame = null;
            int maxAttempts = 60; // 60 × 50ms = 3s
            for (int i = 0; i < maxAttempts; i++)
            {
                capturedFrame = framePool.TryGetNextFrame();
                if (capturedFrame != null)
                {
                    Console.WriteLine($"[wincapture] Frame obtained on attempt {i + 1}");
                    break;
                }
                System.Threading.Thread.Sleep(50);
            }

            if (capturedFrame == null)
                return new CaptureResult(false, Error: "Frame capture timeout (polling)");

            using (capturedFrame)
            {
                var surface = capturedFrame.Surface;
                using var d3dTexture = GetD3D11TextureFromSurface(surface);
                var desc = d3dTexture.Description;

                // 创建 staging texture
                stagingTexture = _d3dDevice!.CreateTexture2D(new Texture2DDescription
                {
                    Width = desc.Width,
                    Height = desc.Height,
                    MipLevels = 1,
                    ArraySize = 1,
                    Format = desc.Format,
                    SampleDescription = new SampleDescription(1, 0),
                    Usage = ResourceUsage.Staging,
                    BindFlags = BindFlags.None,
                    CPUAccessFlags = CpuAccessFlags.Read,
                    MiscFlags = ResourceOptionFlags.None,
                });

                _d3dContext!.CopyResource(stagingTexture, d3dTexture);

                // Map 读取
                var dataBox = _d3dContext.Map(stagingTexture, 0, MapMode.Read, Vortice.Direct3D11.MapFlags.None);
                try
                {
                    var tempDir = Path.Combine(Path.GetTempPath(), "screenclaw-wincapture");
                    Directory.CreateDirectory(tempDir);
                    var imagePath = Path.Combine(tempDir, $"capture_{Environment.TickCount64}.png");

                    SaveAsPng(dataBox.DataPointer, (int)desc.Width, (int)desc.Height, (int)dataBox.RowPitch, imagePath);

                    return new CaptureResult(true, imagePath, (int)desc.Width, (int)desc.Height);
                }
                finally
                {
                    _d3dContext.Unmap(stagingTexture, 0);
                }
            }
        }
        finally
        {
            session?.Dispose();
            framePool?.Dispose();
            stagingTexture?.Dispose();
        }
    }

    private static readonly Guid IID_ID3D11Texture2D = new("6f15aaf2-d208-4e89-9ab4-489535d34f9c");
    private static readonly Guid IID_IDirect3DDxgiInterfaceAccess = new("A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1");

    /// <summary>
    /// 从 IDirect3DSurface 获取 ID3D11Texture2D。
    /// 通过 WinRT 对象的 IInspectable.QueryInterface 获取 IDirect3DDxgiInterfaceAccess，
    /// 再通过该接口的 GetInterface 获取原生 ID3D11Texture2D 指针。
    /// </summary>
    private static ID3D11Texture2D GetD3D11TextureFromSurface(IDirect3DSurface surface)
    {
        // 获取底层 IInspectable 原始指针
        IntPtr inspectablePtr;
        if (surface is IWinRTObject winrtObj)
        {
            // .NET WinRT 投影对象 — 通过 NativeObject 获取原始指针
            inspectablePtr = winrtObj.NativeObject.GetRef();
        }
        else
        {
            // fallback: Marshal.GetIUnknownForObject
            inspectablePtr = Marshal.GetIUnknownForObject(surface);
        }

        if (inspectablePtr == IntPtr.Zero)
            throw new InvalidOperationException("Cannot get native pointer from IDirect3DSurface");

        try
        {
            // QI for IDirect3DDxgiInterfaceAccess
            var iidDxgiAccess = IID_IDirect3DDxgiInterfaceAccess;
            IntPtr accessPtr;
            int hr = Marshal.QueryInterface(inspectablePtr, in iidDxgiAccess, out accessPtr);
            if (hr != 0)
                throw new InvalidOperationException($"QueryInterface for IDirect3DDxgiInterfaceAccess failed: 0x{hr:X8}");

            try
            {
                // 通过 vtable 调用 GetInterface 方法（IUnknown vtable: 0=QI,1=AddRef,2=Release,3=GetInterface）
                IntPtr vtable = Marshal.ReadIntPtr(accessPtr);
                IntPtr getInterfaceFn = Marshal.ReadIntPtr(vtable, 3 * IntPtr.Size);

                var getInterface = (GetInterfaceDelegate)Marshal.GetDelegateForFunctionPointer(getInterfaceFn, typeof(GetInterfaceDelegate));
                var iidTexture = IID_ID3D11Texture2D;
                IntPtr texturePtr;
                hr = getInterface(accessPtr, ref iidTexture, out texturePtr);
                if (hr != 0)
                    throw new InvalidOperationException($"GetInterface for ID3D11Texture2D failed: 0x{hr:X8}");

                if (texturePtr == IntPtr.Zero)
                    throw new InvalidOperationException("GetInterface returned null texture pointer");

                return new ID3D11Texture2D(texturePtr);
            }
            finally
            {
                Marshal.Release(accessPtr);
            }
        }
        finally
        {
            if (surface is not IWinRTObject)
                Marshal.Release(inspectablePtr);
        }
    }

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    private delegate int GetInterfaceDelegate(IntPtr thisPtr, ref Guid iid, out IntPtr outPtr);

    private static unsafe void SaveAsPng(IntPtr pixelData, int width, int height, int rowPitch, string path)
    {
        using var image = new Image<Bgra32>(width, height);

        image.ProcessPixelRows(accessor =>
        {
            for (int y = 0; y < height; y++)
            {
                var rowPtr = (byte*)pixelData + y * rowPitch;
                var row = accessor.GetRowSpan(y);

                for (int x = 0; x < width; x++)
                {
                    row[x] = new Bgra32(
                        b: rowPtr[x * 4],
                        g: rowPtr[x * 4 + 1],
                        r: rowPtr[x * 4 + 2],
                        a: rowPtr[x * 4 + 3]);
                }
            }
        });

        image.SaveAsPng(path);
        Console.WriteLine($"[wincapture] Saved: {path} ({width}x{height})");
    }
}

// 辅助类
static class Interop
{
    [DllImport("d3d11.dll", PreserveSig = false)]
    public static extern IntPtr CreateDirect3D11DeviceFromDXGIDevice(IntPtr dxgiDevice);
}
