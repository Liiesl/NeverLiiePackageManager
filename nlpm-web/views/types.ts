// src/types.ts
export interface PackageMeta {
    name: string;
    description: string;
    updated_at: string;
    import_name?: string;
    latest?: string;
    // New Fields
    author?: string;
    language?: string;
    framework?: string;
    license?: string;
    keywords?: string; // Stored as comma-separated string
}

export interface Version {
    version: string;
    created_at: string;
}