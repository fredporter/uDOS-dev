// Tauri Markdown Application - Native macOS file management and keyboard shortcuts

#![cfg_attr(
  all(not(debug_assertions), target_os = "macos"),
  windows_subsystem = "windows"
)]

mod file_manager;

use tauri::State;
use file_manager::FileManagerState;

// Application state
#[derive(Default)]
pub struct AppState {
  pub current_file: String,
}

fn main() {
  tauri::Builder::default()
    .plugin(tauri_plugin_dialog::init())
    .manage(AppState::default())
    .manage(FileManagerState::default())
    .invoke_handler(tauri::generate_handler![
      handle_new_file,
      handle_open_file,
      handle_save_file,
      handle_command_palette,
      handle_settings,
      handle_hide_window,
      file_manager::get_default_md_folder,
      file_manager::set_default_md_folder,
      file_manager::open_file_dialog,
      file_manager::open_folder_dialog,
      file_manager::read_file,
      file_manager::write_file,
      file_manager::create_new_file,
      file_manager::list_files,
      file_manager::get_file_info,
      file_manager::open_in_finder,
      file_manager::get_documents_folder,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

// Command handlers

#[tauri::command]
fn handle_new_file(_app_state: State<AppState>) -> Result<String, String> {
  println!("Creating new document");
  Ok("New file created".to_string())
}

#[tauri::command]
fn handle_open_file(_app_state: State<AppState>) -> Result<String, String> {
  println!("Opening file");
  Ok("File opened".to_string())
}

#[tauri::command]
fn handle_save_file(_app_state: State<AppState>) -> Result<String, String> {
  println!("Saving file");
  Ok("File saved".to_string())
}

#[tauri::command]
fn handle_command_palette() -> Result<String, String> {
  println!("Opening command palette");
  Ok("Command palette opened".to_string())
}

#[tauri::command]
fn handle_settings() -> Result<String, String> {
  println!("Opening settings");
  Ok("Settings opened".to_string())
}

#[tauri::command]
fn handle_hide_window(window: tauri::Window) -> Result<String, String> {
  window.hide().map_err(|e| e.to_string())?;
  Ok("Window hidden".to_string())
}
