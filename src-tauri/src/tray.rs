//! 托盘图标模块

use tauri::{menu::{Menu, MenuItem}, AppHandle};

/// 创建托盘菜单
#[allow(dead_code)]
pub fn create_tray_menu(app: &AppHandle) -> Result<Menu<tauri::Wry>, Box<dyn std::error::Error>> {
    let show = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&show, &quit])?;

    Ok(menu)
}
