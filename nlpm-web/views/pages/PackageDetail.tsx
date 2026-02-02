// src/pages/PackageDetail.tsx
import { h, Fragment } from "preact";
import { Layout } from "../components/Layout";
import type { PackageMeta, Version } from "../types";

export const PackageDetail = ({ meta, versions }: { meta: PackageMeta; versions: Version[] }) => {
    const sortedVersions = [...versions].sort((a, b) => 
        b.created_at.localeCompare(a.created_at)
    );
    const latestVersion = meta.latest || (sortedVersions[0] ? sortedVersions[0].version : '0.0.0');
    const keywords = meta.keywords ? meta.keywords.split(',').map(k => k.trim()) : [];

    return (
        <Layout title={`${meta.name} - NLPM`}>
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '5px' }}>{meta.name}</h1>
                    <p style={{ fontSize: '1.2rem', color: '#555', marginBottom: '15px' }}>
                        {meta.description || "No description available."}
                    </p>
                </div>
                <div style="display:flex; gap: 10px;">
                    <a href={`/package/${meta.name}/v/${latestVersion}`} class="btn-secondary" style={{textDecoration: 'none'}}>
                        &lt;/&gt; View Code
                    </a>
                    <button class="btn-delete" {...{ onclick: `deletePackage('${meta.name}')` }}>
                        Delete Package
                    </button>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 3fr 1fr; gap: 30px; margin-top: 20px;">
                {/* Left Column: Install and Versions */}
                <div>
                    <h3>Install</h3>
                    <div class="install-box">
                        <span>nlpm install {meta.name}</span>
                        <span style={{ color: '#999', fontSize: '0.8rem', cursor: 'pointer' }} 
                            {...{ onclick: `navigator.clipboard.writeText('nlpm install ${meta.name}')` }}>copy</span>
                    </div>

                    <h3>Versions</h3>
                    <div class="card">
                        <table class="version-list">
                            <thead>
                                <tr>
                                    <th>Version</th>
                                    <th>Published</th>
                                    <th style={{ textAlign: 'right' }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedVersions.map(v => (
                                    <tr>
                                        <td>
                                            <a href={`/package/${meta.name}/v/${v.version}`} style="font-weight:bold; color: var(--primary);">
                                                {v.version}
                                            </a> 
                                            {v.version === meta.latest && <span class="tag">latest</span>}
                                        </td>
                                        <td>{new Date(v.created_at).toLocaleString()}</td>
                                        <td style={{ textAlign: 'right' }}>
                                            <button class="btn-delete" {...{ onclick: `deleteVersion('${meta.name}', '${v.version}')` }}>
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Right Column: Metadata Sidebar */}
                <div class="sidebar">
                    <h4>Details</h4>
                    <div class="meta-item"><strong>Import:</strong> <code>{meta.import_name || meta.name}</code></div>
                    {meta.author && <div class="meta-item"><strong>Author:</strong> {meta.author}</div>}
                    {meta.language && <div class="meta-item"><strong>Language:</strong> {meta.language}</div>}
                    {meta.framework && meta.framework !== 'none' && <div class="meta-item"><strong>Framework:</strong> {meta.framework}</div>}
                    {meta.license && <div class="meta-item"><strong>License:</strong> {meta.license}</div>}
                    
                    {keywords.length > 0 && (
                        <div style="margin-top: 20px;">
                            <h4>Keywords</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                                {keywords.map(k => <span class="tag">{k}</span>)}
                            </div>
                        </div>
                    )}
                </div>
            </div>
            
            <style dangerouslySetInnerHTML={{ __html: `
                .meta-item { margin-bottom: 8px; font-size: 0.9rem; }
                .sidebar h4 { margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
                .btn-secondary { background: #f6f8fa; border: 1px solid #d0d7de; color: #24292f; padding: 10px 20px; border-radius: 6px; font-weight: bold; }
            `}} />
        </Layout>
    );
};