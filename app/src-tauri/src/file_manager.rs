use std::path::Path;
use tauri::State;
use serde::{Deserialize, Serialize};
use std::fs;
use tauri_plugin_dialog::DialogExt;
use std::sync::Mutex;

#[derive(Default)]
pub struct FileManagerState {
    pub default_md_folder: Mutex<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FileOperation {
    pub path: String,
    pub name: String,
    pub size: u64,
    pub is_dir: bool,
}

/// Get the default markdown folder path
#[tauri::command]
pub fn get_default_md_folder(state: State<FileManagerState>) -> Result<String, String> {
    let folder = state.default_md_folder.lock().map_err(|e| e.to_string())?;
    if !folder.is_empty() {
        Ok(folder.clone())
    } else {
        // Default to user's Documents folder
        let home = dirs::home_dir().ok_or("Unable to find home directory")?;
        let docs = home.join("Documents");
        Ok(docs.to_string_lossy().to_string())
    }
}

/// Set the default markdown folder
#[tauri::command]
pub fn set_default_md_folder(folder_path: String, state: State<FileManagerState>) -> Result<(), String> {
    if Path::new(&folder_path).is_dir() {
        let mut folder = state.default_md_folder.lock().map_err(|e| e.to_string())?;
        *folder = folder_path;
        Ok(())
    } else {
        Err("Invalid folder path".to_string())
    }
}

/// Open file dialog and return selected file path
#[tauri::command]
pub fn open_file_dialog(window: tauri::Window) -> Result<Option<String>, String> {
    use std::sync::mpsc::channel;
    use std::sync::Arc;
    use std::sync::Mutex;

    let (tx, rx) = channel();
    let tx = Arc::new(Mutex::new(tx));
    
    window
        .dialog()
        .file()
        .add_filter("Markdown", &["md", "markdown"])
        .add_filter("All Files", &["*"])
        .pick_file({
            let tx = tx.clone();
            move |path| {
                let _ = tx.lock().unwrap().send(path);
            }
        });

    // Wait for result from callback
    let file_path = rx.recv().map_err(|e| format!("Dialog cancelled or error: {}", e))?;
    Ok(file_path.and_then(|p| {
        p.into_path().ok().map(|pb| pb.to_string_lossy().to_string())
    }))
}

/// Open folder dialog and return selected folder path
#[tauri::command]
pub fn open_folder_dialog(window: tauri::Window) -> Result<Option<String>, String> {
    use std::sync::mpsc::channel;
    use std::sync::Arc;
    use std::sync::Mutex;

    let (tx, rx) = channel();
    let tx = Arc::new(Mutex::new(tx));
    
    window
        .dialog()
        .file()
        .pick_folder({
            let tx = tx.clone();
            move |path| {
                let _ = tx.lock().unwrap().send(path);
            }
        });

    // Wait for result from callback
    let folder_path = rx.recv().map_err(|e| format!("Dialog cancelled or error: {}", e))?;
    Ok(folder_path.and_then(|p| {
        p.into_path().ok().map(|pb| pb.to_string_lossy().to_string())
    }))
}

/// Read file contents
#[tauri::command]
pub fn read_file(file_path: String) -> Result<String, String> {
    fs::read_to_string(&file_path)
        .map_err(|e| format!("Error reading file: {}", e))
}

/// Write file contents
#[tauri::command]
pub fn write_file(file_path: String, content: String) -> Result<(), String> {
    fs::write(&file_path, content)
        .map_err(|e| format!("Error writing file: {}", e))
}

/// Create new markdown file with timestamp
#[tauri::command]
pub fn create_new_file(folder_path: String) -> Result<String, String> {
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = format!("document_{}.md", timestamp);
    let file_path = Path::new(&folder_path).join(&filename);
    
    // Create empty file
    fs::write(&file_path, "# New Document\n\nStart typing here...")
        .map_err(|e| format!("Error creating file: {}", e))?;

    Ok(file_path.to_string_lossy().to_string())
}

/// List files in folder
#[tauri::command]
pub fn list_files(folder_path: String) -> Result<Vec<FileOperation>, String> {
    let mut files = Vec::new();
    
    let entries = fs::read_dir(&folder_path)
        .map_err(|e| format!("Error reading folder: {}", e))?;

    for entry in entries {
        if let Ok(entry) = entry {
            let path = entry.path();
            if let Ok(metadata) = entry.metadata() {
                files.push(FileOperation {
                    path: path.to_string_lossy().to_string(),
                    name: entry.file_name().to_string_lossy().to_string(),
                    size: metadata.len(),
                    is_dir: metadata.is_dir(),
                });
            }
        }
    }

    // Sort by name
    files.sort_by(|a, b| a.name.cmp(&b.name));
    
    Ok(files)
}

/// Get file metadata
#[tauri::command]
pub fn get_file_info(file_path: String) -> Result<FileOperation, String> {
    let path = Path::new(&file_path);
    let metadata = fs::metadata(path)
        .map_err(|e| format!("Error getting file info: {}", e))?;

    let file_name = path.file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| "unknown".to_string());

    Ok(FileOperation {
        path: file_path,
        name: file_name,
        size: metadata.len(),
        is_dir: metadata.is_dir(),
    })
}

/// Open file in default application (Finder on macOS)
#[tauri::command]
pub fn open_in_finder(file_path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg("-R")
            .arg(&file_path)
            .output()
            .map_err(|e| format!("Error opening Finder: {}", e))?;
    }
    
    #[cfg(not(target_os = "macos"))]
    {
        // For non-macOS, try opening the folder
        std::process::Command::new("open")
            .arg(&file_path)
            .output()
            .map_err(|e| format!("Error opening folder: {}", e))?;
    }

    Ok(())
}

/// Get Documents folder path
#[tauri::command]
pub fn get_documents_folder() -> Result<String, String> {
    let home = dirs::home_dir().ok_or("Unable to find home directory")?;
    let docs = home.join("Documents");
    Ok(docs.to_string_lossy().to_string())
}
