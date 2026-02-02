import { h } from "preact";

export const SearchBox = () => (
    <input 
        type="text" 
        class="search-box" 
        placeholder="Search packages..." 
        // We use string attributes for inline JS in SSR-only mode
        {...{ onkeyup: "filterPackages(this.value)" }}
    />
);