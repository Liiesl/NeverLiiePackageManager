import { h } from "preact";
import { render } from "preact-render-to-string";
import { Index } from "./pages/index";
import { PackageDetail } from "./pages/PackageDetail";
import { FileExplorer } from "./pages/FileExplorer"; // Import new page
import type { PackageMeta, Version } from "./types";

export const renderIndexPage = (packages: PackageMeta[]) => {
    return "<!DOCTYPE html>" + render(h(Index, { packages }));
};

export const renderPackagePage = (meta: PackageMeta, versions: Version[]) => {
    return "<!DOCTYPE html>" + render(h(PackageDetail, { meta, versions }));
};

// New Export
export const renderFileExplorer = (meta: PackageMeta, version: string, files: string[], currentPath: string, content: string | null) => {
    return "<!DOCTYPE html>" + render(h(FileExplorer, { meta, version, files, currentPath, content }));
};