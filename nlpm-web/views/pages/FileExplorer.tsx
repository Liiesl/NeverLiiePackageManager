import { h } from "preact";
import { Layout } from "../components/Layout";
import type { PackageMeta } from "../types";

interface FileExplorerProps {
    meta: PackageMeta;
    version: string;
    files: string[];     
    currentPath: string; 
    content: string;     
}

export const FileExplorer = ({ meta, version, files, currentPath, content }: FileExplorerProps) => {
    
    // Defensive check: Ensure currentPath is a string before splitting
    const safePath = String(currentPath || "");
    const ext = safePath.split('.').pop() || 'txt';
    const isBinary = content === null; 

    return (
        <Layout title={`${meta.name} - Source`}>
            <div class="breadcrumbs">
                <a href={`/package/${meta.name}`}>&larr; Back to Package</a>
                <span>/</span>
                {meta.name} <span>@</span> {version}
            </div>

            <div class="explorer-container">
                {/* Sidebar: File List */}
                <div class="explorer-sidebar">
                    <ul class="file-list">
                        {files.sort().map(f => (
                            <li class="file-item">
                                <a 
                                    href={`/package/${meta.name}/v/${version}/tree/${f}`} 
                                    class={`file-link ${f === safePath ? 'active' : ''}`}
                                >
                                    📄 {f}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Main: Code Viewer */}
                <div class="explorer-content">
                    {isBinary ? (
                        <div style="padding: 50px; text-align: center; color: #666;">
                            Binary file (cannot render preview)
                        </div>
                    ) : (
                        <pre>
                            <code class={`language-${ext}`}>{content}</code>
                        </pre>
                    )}
                </div>
            </div>
        </Layout>
    );
};