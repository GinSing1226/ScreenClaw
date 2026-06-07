fn main() {
    let mut attributes = tauri_build::Attributes::new();

    // 在 Windows 上嵌入 application manifest 以请求管理员权限（UAC 提示）
    #[cfg(target_os = "windows")]
    {
        let mut windows = tauri_build::WindowsAttributes::new();

        // 设置管理员权限 manifest - 每次执行都会弹出 UAC 提示
        // 同时声明对 comctl32 v6 的依赖（TaskDialogIndirect API 需要）
        windows = windows.app_manifest(r#"
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
      <security>
          <requestedPrivileges>
              <requestedExecutionLevel level="requireAdministrator" uiAccess="false" />
          </requestedPrivileges>
      </security>
  </trustInfo>
</assembly>
"#);

        attributes = attributes.windows_attributes(windows);
    }

    tauri_build::try_build(attributes).expect("failed to build Tauri app");
}
