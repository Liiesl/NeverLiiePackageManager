# src/registry.py
import sqlite3
from datetime import datetime
from . import db

def ensure_initialized():
    db.init_db()

def library_exists(name):
    ensure_initialized()
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT id FROM libraries WHERE name = ?", (name,)).fetchone()
        return row is not None
    finally:
        conn.close()

def register_library(name, import_name, description="", language="", framework="", author="", license="", keywords=""):
    """Reserves the library name or updates metadata if it exists."""
    ensure_initialized()
    conn = db.get_conn()
    try:
        # Check if exists
        row = conn.execute("SELECT id FROM libraries WHERE name = ?", (name,)).fetchone()
        
        if row:
            # UPDATE existing metadata
            conn.execute("""
                UPDATE libraries 
                SET import_name=?, description=?, language=?, framework=?, author=?, license=?, keywords=?, updated_at=?
                WHERE name=?
            """, (import_name, description, language, framework, author, license, keywords, datetime.now(), name))
        else:
            # INSERT new library
            conn.execute("""
                INSERT INTO libraries 
                (name, import_name, description, language, framework, author, license, keywords, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, import_name, description, language, framework, author, license, keywords, datetime.now()))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_import_name(name):
    ensure_initialized()
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT import_name FROM libraries WHERE name = ?", (name,)).fetchone()
        if row and row['import_name']:
            return row['import_name']
        return None
    finally:
        conn.close()

def publish_version(name, version, file_map):
    """
    Publishes a new version.
    file_map: dict { "relative/path.py": "sha256_hash" }
    """
    ensure_initialized()
    conn = db.get_conn()
    cursor = conn.cursor()
    
    try:
        # 1. Get Library ID
        row = cursor.execute("SELECT id FROM libraries WHERE name = ?", (name,)).fetchone()
        if not row:
            raise ValueError(f"Library '{name}' not registered.")
        lib_id = row['id']

        # 2. Insert Version
        cursor.execute(
            "INSERT INTO versions (library_id, version) VALUES (?, ?)",
            (lib_id, version)
        )
        version_id = cursor.lastrowid

        # 3. Insert Files (Bulk)
        files_data = [(version_id, path, fhash) for path, fhash in file_map.items()]
        cursor.executemany(
            "INSERT INTO package_files (version_id, file_path, file_hash) VALUES (?, ?, ?)",
            files_data
        )

        # 4. Update library timestamp
        cursor.execute("UPDATE libraries SET updated_at = ? WHERE id = ?", (datetime.now(), lib_id))

        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Version {version} already exists for {name}.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_latest_version(name):
    ensure_initialized() 
    conn = db.get_conn()
    try:
        query = """
            SELECT v.version 
            FROM versions v
            JOIN libraries l ON v.library_id = l.id
            WHERE l.name = ?
            ORDER BY v.created_at DESC
            LIMIT 1
        """
        row = conn.execute(query, (name,)).fetchone()
        return row['version'] if row else None
    finally:
        conn.close()

def get_package_files(name, version):
    ensure_initialized() 
    conn = db.get_conn()
    try:
        query = """
            SELECT pf.file_path, pf.file_hash
            FROM package_files pf
            JOIN versions v ON pf.version_id = v.id
            JOIN libraries l ON v.library_id = l.id
            WHERE l.name = ? AND v.version = ?
        """
        rows = conn.execute(query, (name, version)).fetchall()
        return {row['file_path']: row['file_hash'] for row in rows} if rows else None
    finally:
        conn.close()

def list_libraries():
    """Returns list of (name, latest_version, language, framework) tuples."""
    ensure_initialized() 
    conn = db.get_conn()
    try:
        libs = conn.execute("SELECT name, language, framework FROM libraries ORDER BY name").fetchall()
        
        results = []
        for lib in libs:
            ver = get_latest_version(lib['name']) 
            # Return tuple: (name, version, language, framework)
            results.append((lib['name'], ver, lib['language'], lib['framework']))
        return results
    finally:
        conn.close()