import { h } from "preact";
import { Layout } from "../components/Layout";
import { SearchBox } from "../components/SearchBox";
import { PackageCard, EmptyState } from "../components/PackageCard";
import type { PackageMeta } from "../types";

export const Index = ({ packages }: { packages: PackageMeta[] }) => (
    <Layout title="NLPM Registry">
        <SearchBox />
        {packages.length === 0 ? <EmptyState /> : packages.map(p => <PackageCard pkg={p} />)}
    </Layout>
);