// Fix: Add global type definitions for Vite environment variables to fix issues
// with `import.meta.env` when a tsconfig.json is not properly configured.
declare global {
    interface ImportMetaEnv {
      readonly VITE_API_BASE_URL: string;
    }
  
    interface ImportMeta {
      readonly env: ImportMetaEnv;
    }
}

export interface FileDocument {
    _id: string;
    file_ref: string;
    file_name: string;
    file_size: number;
    file_type: string;
    mime_type: string;
    caption: string;
}