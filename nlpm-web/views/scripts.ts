export const CLIENT_SCRIPTS = `
    async function deletePackage(name) {
        if(!confirm('Delete entire package ' + name + '?')) return;
        const res = await fetch('/api/package/' + name, { method: 'DELETE' });
        if(res.ok) window.location.href = '/';
        else alert('Error deleting package');
    }
    async function deleteVersion(name, version) {
        if(!confirm('Delete version ' + version + '?')) return;
        const res = await fetch('/api/package/' + name + '/' + version, { method: 'DELETE' });
        if(res.ok) window.location.reload();
        else alert('Error deleting version');
    }
    function filterPackages(val) {
        const term = val.toLowerCase();
        document.querySelectorAll('.card').forEach(c => {
            const txt = c.getAttribute('data-search') || '';
            c.style.display = txt.includes(term) ? 'block' : 'none';
        });
    }
`;