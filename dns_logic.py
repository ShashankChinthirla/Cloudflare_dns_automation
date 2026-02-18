import re

def generate_updated_spf(raw_spf):
    """
    Ported logic from BulkResultsTable.tsx:
    const generateUpdatedSpf = (raw: string | null) => raw ? raw.replace(/-all|\?all/g, '~all') : 'v=spf1 a mx ~all';
    """
    if not raw_spf or str(raw_spf).strip().lower() == "missing":
        return "v=spf1 a mx ~all"
    
    # EXACT logic from TS: Replace -all or ?all with ~all
    # Using regex to match the global replace behavior
    updated = re.sub(r'-all|\?all', '~all', raw_spf.strip())
    return updated

def generate_updated_dmarc(raw_dmarc, domain):
    """
    Ported logic from BulkResultsTable.tsx:
    Identical logic for ensureMailto, hasSyntaxError, and strict record checks.
    """
    def ensure_mailto(val):
        # TS: return val.split(',').map(p => p.trim()).map(p => p.toLowerCase().startsWith('mailto:') ? p : `mailto:${p}`).join(', ');
        parts = [p.strip() for p in val.split(',') if p.strip()]
        fixed_parts = []
        for p in parts:
            if p.lower().startswith('mailto:'):
                fixed_parts.append(p)
            else:
                fixed_parts.append(f"mailto:{p}")
        return ", ".join(fixed_parts)

    def has_syntax_error(record):
        # TS: Checks rua and ruf for mailto prefix
        m_rua = re.search(r'rua=([^;]+)', record, re.IGNORECASE)
        if m_rua:
            parts = [p.strip() for p in m_rua.group(1).split(',') if p.strip()]
            if any(p and not p.lower().startswith('mailto:') for p in parts):
                return True
        m_ruf = re.search(r'ruf=([^;]+)', record, re.IGNORECASE)
        if m_ruf:
            parts = [p.strip() for p in m_ruf.group(1).split(',') if p.strip()]
            if any(p and not p.lower().startswith('mailto:') for p in parts):
                return True
        return False

    if not raw_dmarc or str(raw_dmarc).strip().lower() == "missing":
        raw_dmarc = None

    # TS logic: If already strict and no syntax error, keep existing
    is_already_strict = False
    if raw_dmarc:
        is_already_strict = 'p=reject' in raw_dmarc or ('p=quarantine' in raw_dmarc and 'pct=100' in raw_dmarc)
        syntax_error = has_syntax_error(raw_dmarc)
        
        # TS: if (isAlreadyStrict && !raw?.includes('p=none') && !syntaxError) return raw || '';
        if is_already_strict and 'p=none' not in raw_dmarc and not syntax_error:
            return raw_dmarc

    # Default values from TS
    rua = f"mailto:dmarc-reports@{domain}"
    ruf_str = ""
    
    if raw_dmarc:
        m_rua = re.search(r'rua=([^;]+)', raw_dmarc, re.IGNORECASE)
        if m_rua:
            rua = ensure_mailto(m_rua.group(1))
            
        m_ruf = re.search(r'ruf=([^;]+)', raw_dmarc, re.IGNORECASE)
        if m_ruf:
            ruf_str = f" ruf={ensure_mailto(m_ruf.group(1))};"

    # EXACT template from TS
    return f"v=DMARC1; p=reject; sp=reject; pct=100; rua={rua};{ruf_str} adkim=r; aspf=r;"
