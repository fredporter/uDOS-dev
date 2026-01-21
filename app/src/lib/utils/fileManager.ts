import { invoke } from "@tauri-apps/api/core";
import { toasts } from "../../components/UI/Toast/store";

export interface FileOperation {
  path: string;
  name: string;
  size: number;
  is_dir: boolean;
}

/**
 * File Manager Utilities
 * Provides high-level file operations via Tauri commands
 */

export const fileManager = {
  /**
   * Get the default markdown folder path
   */
  async getDefaultMdFolder(): Promise<string> {
    try {
      return await invoke("get_default_md_folder");
    } catch (error) {
      console.error("Error getting default folder:", error);
      throw error;
    }
  },

  /**
   * Set the default markdown folder
   */
  async setDefaultMdFolder(folderPath: string): Promise<void> {
    try {
      await invoke("set_default_md_folder", { folderPath });
      toasts.success(`Default folder updated`);
    } catch (error) {
      console.error("Error setting default folder:", error);
      toasts.error("Failed to set default folder");
      throw error;
    }
  },

  /**
   * Open file dialog and return selected file path
   */
  async openFileDialog(): Promise<string | null> {
    try {
      return await invoke("open_file_dialog");
    } catch (error) {
      console.error("Error opening file dialog:", error);
      return null;
    }
  },

  /**
   * Open folder dialog and return selected folder path
   */
  async openFolderDialog(): Promise<string | null> {
    try {
      return await invoke("open_folder_dialog");
    } catch (error) {
      console.error("Error opening folder dialog:", error);
      return null;
    }
  },

  /**
   * Read file contents
   */
  async readFile(filePath: string): Promise<string> {
    try {
      const content = await invoke("read_file", { filePath });
      return content as string;
    } catch (error) {
      console.error("Error reading file:", error);
      toasts.error(`Failed to read file`);
      throw error;
    }
  },

  /**
   * Write file contents
   */
  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      await invoke("write_file", { filePath, content });
      toasts.success(`File saved: ${extractFileName(filePath)}`);
    } catch (error) {
      console.error("Error writing file:", error);
      toasts.error("Failed to save file");
      throw error;
    }
  },

  /**
   * Create new markdown file with timestamp
   */
  async createNewFile(folderPath: string): Promise<string> {
    try {
      const filePath = await invoke("create_new_file", { folderPath });
      toasts.success("New document created");
      return filePath as string;
    } catch (error) {
      console.error("Error creating file:", error);
      toasts.error("Failed to create new file");
      throw error;
    }
  },

  /**
   * List files in folder
   */
  async listFiles(folderPath: string): Promise<FileOperation[]> {
    try {
      const files = await invoke("list_files", { folderPath });
      return files as FileOperation[];
    } catch (error) {
      console.error("Error listing files:", error);
      throw error;
    }
  },

  /**
   * Get file metadata
   */
  async getFileInfo(filePath: string): Promise<FileOperation> {
    try {
      const info = await invoke("get_file_info", { filePath });
      return info as FileOperation;
    } catch (error) {
      console.error("Error getting file info:", error);
      throw error;
    }
  },

  /**
   * Open file in Finder (macOS)
   */
  async openInFinder(filePath: string): Promise<void> {
    try {
      await invoke("open_in_finder", { filePath });
    } catch (error) {
      console.error("Error opening in Finder:", error);
      toasts.error("Failed to open in Finder");
      throw error;
    }
  },

  /**
   * Get user's Documents folder
   */
  async getDocumentsFolder(): Promise<string> {
    try {
      return await invoke("get_documents_folder");
    } catch (error) {
      console.error("Error getting documents folder:", error);
      throw error;
    }
  },
};

/**
 * Helper function to extract filename from path
 */
export function extractFileName(filePath: string): string {
  return filePath.split(/[\\/]/).pop() || "file";
}

/**
 * Helper function to extract file extension
 */
export function getFileExtension(filePath: string): string {
  const match = filePath.match(/\.([^.]+)$/);
  return match ? match[1].toLowerCase() : "";
}

/**
 * Helper function to check if file is markdown
 */
export function isMarkdownFile(filePath: string): boolean {
  const ext = getFileExtension(filePath);
  return ext === "md" || ext === "markdown";
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}
