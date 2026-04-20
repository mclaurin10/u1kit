// u1kit GUI backend. Plugins:
//   - shell: required by `Command` from @tauri-apps/plugin-shell (the
//     wrapper that invokes the u1kit CLI sidecar).
//   - dialog: required by the file-picker and save-as flows
//     (@tauri-apps/plugin-dialog).
//   - opener: for external URL handling if/when we need it.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
