using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace ScreenClawWinCapture;

/// <summary>
/// screenclaw-wincapture-service
/// 常驻进程，通过 HTTP API 提供 Windows Graphics Capture 截图服务。
/// Python 主服务通过 HTTP 调用此进程完成 DX/UE 游戏截图。
/// </summary>
class Program
{
    private static HttpListener? _listener;
    private static CancellationTokenSource? _cts;

    [STAThread]
    static async Task Main(string[] args)
    {
        int port = 12262;

        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == "--port" && int.TryParse(args[i + 1], out int p))
                port = p;
        }

        _cts = new CancellationTokenSource();

        _listener = new HttpListener();
        _listener.Prefixes.Add($"http://127.0.0.1:{port}/");

        Console.WriteLine($"[wincapture] Starting on port {port}");

        try
        {
            _listener.Start();
        }
        catch (HttpListenerException ex)
        {
            Console.WriteLine($"[wincapture] FATAL: {ex.Message}");
            return;
        }

        Console.WriteLine("[wincapture] Ready.");

        Console.CancelKeyPress += (_, e) => { e.Cancel = true; _cts.Cancel(); };

        try
        {
            while (!_cts.Token.IsCancellationRequested)
            {
                var ctx = await _listener.GetContextAsync();
                if (_cts.Token.IsCancellationRequested) break;
                _ = Task.Run(() => HandleRequest(ctx), _cts.Token);
            }
        }
        catch (HttpListenerException) when (_cts.Token.IsCancellationRequested) { }
        finally
        {
            _listener.Stop();
            Console.WriteLine("[wincapture] Stopped.");
        }
    }

    private static async Task HandleRequest(HttpListenerContext ctx)
    {
        var path = ctx.Request.Url?.AbsolutePath ?? "/";
        var method = ctx.Request.HttpMethod;
        byte[] body;
        int code = 200;

        try
        {
            switch (path)
            {
                case "/health":
                    body = Json("ok", "status");
                    break;

                case "/shutdown":
                    body = Json("shutting_down", "status");
                    _ = Task.Run(async () => { await Task.Delay(100); _cts?.Cancel(); });
                    break;

                case "/capture":
                    if (method != "POST")
                    {
                        code = 405;
                        body = Json("POST required", "error");
                        break;
                    }
                    body = await HandleCapture(ctx.Request);
                    break;

                default:
                    code = 404;
                    body = Json("not_found", "error");
                    break;
            }
        }
        catch (Exception ex)
        {
            code = 500;
            body = Json(ex.Message, "error");
        }

        ctx.Response.StatusCode = code;
        ctx.Response.ContentType = "application/json";
        ctx.Response.ContentLength64 = body.Length;
        await ctx.Response.OutputStream.WriteAsync(body, _cts?.Token ?? CancellationToken.None);
        ctx.Response.Close();
    }

    private static async Task<byte[]> HandleCapture(HttpListenerRequest request)
    {
        string body;
        using (var reader = new StreamReader(request.InputStream, Encoding.UTF8))
            body = await reader.ReadToEndAsync();

        var req = JsonSerializer.Deserialize<CaptureRequest>(body);
        if (req == null || req.hwnd <= 0)
            return Json("invalid_request: hwnd required", "error");

        Console.WriteLine($"[wincapture] Capture hwnd={req.hwnd}");

        var result = CaptureService.CaptureWindow(new IntPtr(req.hwnd));

        if (result.Success)
        {
            return Encoding.UTF8.GetBytes(
                $"{{\"success\":true,\"image_path\":\"{EscapeJson(result.ImagePath!)}\"," +
                $"\"width\":{result.Width},\"height\":{result.Height}}}");
        }
        else
        {
            return Encoding.UTF8.GetBytes(
                $"{{\"success\":false,\"error\":\"{EscapeJson(result.Error!)}\"}}");
        }
    }

    private static byte[] Json(string value, string key)
        => Encoding.UTF8.GetBytes($"{{\"{key}\":\"{EscapeJson(value)}\"}}");

    private static string EscapeJson(string s)
        => s.Replace("\\", "\\\\").Replace("\"", "\\\"");
}

record CaptureRequest(int hwnd);
record CaptureResult(bool Success, string? ImagePath = null, int Width = 0, int Height = 0, string? Error = null);
