import { h } from "preact";
import type { PackageMeta } from "../types";

export const PackageCard = ({ pkg }: { pkg: PackageMeta }) => {
    // Combine keywords, language, and framework for better searching
    const searchTerms = [
        pkg.name,
        pkg.language,
        pkg.framework,
        pkg.author,
        pkg.keywords
    ].filter(Boolean).join(' ').toLowerCase();

    return (
        <div class="card" data-search={searchTerms}>
            <div class="pkg-header">
                <a href={`/package/${pkg.name}`}>
                    <h2 class="pkg-title">{pkg.name}</h2>
                </a>
                <div style="display: flex; gap: 8px; align-items: center;">
                    {pkg.language && (
                        <span class="tag" style="background: #e1f5fe; color: #01579b; border: 1px solid #b3e5fc;">
                            {pkg.language}
                        </span>
                    )}
                    <span class="pkg-meta">v{pkg.latest || '0.0.0'}</span>
                </div>
            </div>
            <p class="pkg-desc">{pkg.description || "No description provided."}</p>
            <div class="pkg-meta">
                {pkg.author && <span>By <strong>{pkg.author}</strong> | </span>}
                Updated: {pkg.updated_at ? new Date(pkg.updated_at).toLocaleDateString() : 'Never'}
                {pkg.license && <span> | License: {pkg.license}</span>}
            </div>
        </div>
    );
};

// Ensure this is exported!
export const EmptyState = () => (
    <div class="card">
        <p>No packages found in registry DB.</p>
    </div>
);