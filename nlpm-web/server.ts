import express from "express";
import path from "path";
import fs from "fs";
import os from "os";
import { Database } from "bun:sqlite";
import { renderIndexPage, renderPackagePage, renderFileExplorer } from "./views"; 

const app = express();
const PORT = 5618;

// Config
const NLPM_HOME = path.join(os.homedir(), ".nlpm");
const DB_PATH = path.join(NLPM_HOME, "registry.db");
const STORE_DIR = path.join(NLPM_HOME, "store");

// Database Setup
let db: Database;
try {
    if (!fs.existsSync(NLPM_HOME)) fs.mkdirSync(NLPM_HOME, { recursive: true });
    db = new Database(DB_PATH);
    db.exec("PRAGMA journal_mode = WAL;");
    db.exec("PRAGMA foreign_keys = ON;");
} catch (err) {
    console.error("Failed to open database:", err);
}

app.use(express.static("public"));

// --- HELPERS ---

function getLibrary(name: string) {
    if (!db) return null;
    return db.prepare("SELECT * FROM libraries WHERE name = ?").get(name);
}

function getVersions(libId: number) {
    if (!db) return [];
    return db.prepare("SELECT * FROM versions WHERE library_id = ? ORDER BY created_at DESC").all(libId);
}

function getLatestVersion(libId: number) {
    if (!db) return null;
    const row: any = db.prepare("SELECT version FROM versions WHERE library_id = ? ORDER BY created_at DESC LIMIT 1").get(libId);
    return row ? row.version : null;
}

// Get raw content from CAS Store
function getFileContent(fileHash: string): string | null {
    const prefix = fileHash.substring(0, 2);
    const suffix = fileHash.substring(2);
    const filePath = path.join(STORE_DIR, prefix, suffix);
    
    try {
        if (!fs.existsSync(filePath)) return "File not found in store.";
        // Check for binary files (simplistic check)
        const buffer = fs.readFileSync(filePath);
        // If it has null bytes, treat as binary
        if (buffer.includes(0)) return null; 
        return buffer.toString('utf-8');
    } catch (e) {
        return "Error reading file.";
    }
}

// --- ROUTES ---

// 1. Index Page
app.get("/", (req, res) => {
    if (!db) return res.send(renderIndexPage([]));

    try {
        const libs = db.prepare("SELECT * FROM libraries ORDER BY updated_at DESC").all();
        const packages = libs.map((lib: any) => ({
            ...lib,
            latest: getLatestVersion(lib.id) || "0.0.0",
        }));

        res.send(renderIndexPage(packages));
    } catch (e) {
        console.error(e);
        res.status(500).send("Database Error");
    }
});

// 2. Package Details
app.get("/package/:name", (req, res) => {
    const { name } = req.params;
    try {
        const lib: any = getLibrary(name);
        if (!lib) return res.status(404).send("Package not found");

        const versions = getVersions(lib.id);
        const latest = versions.length > 0 ? (versions[0] as any).version : null;
        
        const meta = { ...lib, latest };

        res.send(renderPackagePage(meta, versions));
    } catch (e) {
        console.error(e);
        res.status(500).send("Database error");
    }
});

// 3. Source Viewer Redirect
app.get("/package/:name/v/:version", (req, res) => {
    res.redirect(`/package/${req.params.name}/v/${req.params.version}/tree/root`);
});

// 4. Source Viewer Implementation
app.get("/package/:name/v/:version/tree/*filepath", (req, res) => {
    const { name, version } = req.params;
    
    // FIX: Ensure requestedPath is always a string.
    // Some routers return wildcards as arrays, others as strings.
    const rawPath = req.params.filepath;
    const requestedPath = Array.isArray(rawPath) ? rawPath.join("/") : (rawPath || "");

    try {
        const lib: any = getLibrary(name);
        if (!lib) return res.status(404).send("Package not found");

        // Get Version ID
        const verRow: any = db.prepare("SELECT id FROM versions WHERE library_id = ? AND version = ?").get(lib.id, version);
        if (!verRow) return res.status(404).send("Version not found");

        // Get All Files
        const files: any[] = db.prepare("SELECT file_path, file_hash FROM package_files WHERE version_id = ? ORDER BY file_path ASC").all(verRow.id);
        const filePaths = files.map(f => f.file_path);

        // Determine target file
        let targetFile: string | null = requestedPath === "root" ? null : requestedPath;
        
        // If "root" or empty, try finding README or use first file
        if (!targetFile) {
            targetFile = filePaths.find(p => p.toLowerCase().includes("readme")) || filePaths[0] || "";
        }

        // Find hash
        const fileRecord = files.find(f => f.file_path === targetFile);
        
        let content = "";
        if (fileRecord) {
            content = getFileContent(fileRecord.file_hash) || ""; // null means binary
        } else {
            content = "File not found.";
        }

        const latest = getLatestVersion(lib.id);
        const meta = { ...lib, latest };

        res.send(renderFileExplorer(meta, version, filePaths, targetFile, content));

    } catch (e) {
        console.error(e);
        res.status(500).send("Server Error");
    }
});

// --- API ROUTES ---

app.delete("/api/package/:name", (req, res) => {
    const { name } = req.params;
    try {
        const lib: any = getLibrary(name);
        if (!lib) return res.status(404).json({ error: "Not found" });
        const transaction = db.transaction(() => {
            db.prepare(`DELETE FROM package_files WHERE version_id IN (SELECT id FROM versions WHERE library_id = ?)`).run(lib.id);
            db.prepare("DELETE FROM versions WHERE library_id = ?").run(lib.id);
            db.prepare("DELETE FROM libraries WHERE id = ?").run(lib.id);
        });
        transaction();
        res.json({ success: true });
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Database error" });
    }
});

app.delete("/api/package/:name/:version", (req, res) => {
    const { name, version } = req.params;
    try {
        const lib: any = getLibrary(name);
        if (!lib) return res.status(404).json({ error: "Library not found" });
        const verRow: any = db.prepare("SELECT id FROM versions WHERE library_id = ? AND version = ?").get(lib.id, version);
        if (!verRow) return res.status(404).json({ error: "Version not found" });

        const transaction = db.transaction(() => {
            db.prepare("DELETE FROM package_files WHERE version_id = ?").run(verRow.id);
            db.prepare("DELETE FROM versions WHERE id = ?").run(verRow.id);
            db.prepare("UPDATE libraries SET updated_at = CURRENT_TIMESTAMP WHERE id = ?").run(lib.id);
        });
        transaction();
        res.json({ success: true });
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: "Database error" });
    }
});

app.listen(PORT, () => {
    console.log(`📦 NLPM Registry running at http://localhost:${PORT}`);
});