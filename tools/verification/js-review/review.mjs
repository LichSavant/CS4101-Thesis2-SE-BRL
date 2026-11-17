// Experimental browser-compatible port. No model, network, persistence or release authority.
import C from './contracts.mjs';
export class ReviewContractError extends Error {}
export class SemanticInferenceUnavailable extends Error {}
const fail = code => { throw new ReviewContractError(code); };
const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const cp = s => Array.from(s);
export const codePointLength = s => cp(s).length;
export const codePointSlice = (s, a, b) => cp(s).slice(a, b).join('');
export function utf16ToCodePoint(s, offset) {
  if (!Number.isInteger(offset) || offset < 0 || offset > s.length ||
      (offset && /[\uD800-\uDBFF]/u.test(s[offset - 1]) && /[\uDC00-\uDFFF]/u.test(s[offset] ?? ''))) fail('invalid_utf16_boundary');
  return codePointLength(s.slice(0, offset));
}
export function codePointToUtf16(s, offset) {
  if (!Number.isInteger(offset) || offset < 0 || offset > codePointLength(s)) fail('invalid_codepoint_boundary');
  return codePointSlice(s, 0, offset).length;
}
const WS = '[\\t-\\r\\x1c-\\x20\\x85\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
const WORD = '[\\p{L}\\p{N}_]';
const trim = s => s.replace(new RegExp(`^${WS}+|${WS}+$`, 'gu'), '');
const fold = s => cp(s).map(c => C.casefold[c] ?? c.toLowerCase()).join('');
// Python re Unicode boundaries/space/digits and dot semantics, including its four
// extra ASCII-ignorecase letters. Match positions are converted explicitly.
export function pyRegex(source, insensitive = true) {
  let out = '', inClass = false;
  for (let i = 0; i < source.length; i++) {
    let c = source[i];
    if (c === '\\') {
      const n = source[++i];
      out += n === 'b' ? `(?:(?<=${WORD})(?!${WORD})|(?<!${WORD})(?=${WORD}))`
        : n === 'w' ? (inClass ? WORD.slice(1,-1) : WORD) : n === 's' ? (inClass ? WS.slice(1,-1) : WS) : n === 'd' ? '\\p{Nd}' : n === 'Z' ? '$(?![\\s\\S])' : '\\' + n;
    } else {
      if (c === '[') inClass = true;
      if (c === ']') inClass = false;
      out += c === '.' && !inClass ? '[^\\n]' : insensitive && !inClass && /[iI]/u.test(c) ? '[iIİı]' : c;
    }
  }
  return new RegExp(out, insensitive ? 'giu' : 'gu');
}
const matches = (pattern, text) => [...text.matchAll(pyRegex(pattern))].map(m => ({
  text: m[0], start: utf16ToCodePoint(text, m.index), end: utf16ToCodePoint(text, m.index + m[0].length)
}));
const has = (pattern, text) => pyRegex(pattern).test(text);
const equal = (a, b) => canonical(a) === canonical(b);
const keys = (o, names) => obj(o) && equal(Object.keys(o).sort(), [...names].sort());
function finiteJSON(x, depth = 0) {
  if (depth > 16) fail('metadata_depth');
  if (x === null || typeof x === 'boolean' || typeof x === 'string') return;
  if (typeof x === 'number' && Number.isFinite(x)) return;
  if (Array.isArray(x)) { x.forEach(v => finiteJSON(v, depth + 1)); return; }
  if (obj(x) && Object.getPrototypeOf(x) === Object.prototype) { Object.values(x).forEach(v => finiteJSON(v, depth + 1)); return; }
  fail('finite_json_required');
}
function canonical(x) {
  finiteJSON(x);
  const sorted = v => Array.isArray(v) ? v.map(sorted) : obj(v)
    ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sorted(v[k])])) : v;
  return JSON.stringify(sorted(x)).replace(/[\u007f-\uffff]/g, ch => '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'));
}
export async function fingerprint(x) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(x))))].map(v => v.toString(16).padStart(2, '0')).join('');
}
function excluded(value) {
  if (typeof value === 'string') {
    const n = fold(value.normalize('NFKC')).replace(/[^a-z0-9]/gu, '');
    if (n.includes('spaphish') || n.includes('spafish') || C.excluded_hashes.includes(value.toLowerCase())) fail('excluded_corpus');
  } else if (Array.isArray(value)) value.forEach(excluded);
  else if (obj(value)) Object.entries(value).forEach(([k, v]) => { excluded(k); excluded(v); });
}
function unescapeHTML(text) {
  return text.replace(/&(#(?:[0-9]+|[xX][0-9a-fA-F]+);?|[^\t\n\f <&#;]{1,32};?)/gu, (whole, v) => {
    if (v[0] === '#') {
      const n = Number.parseInt(v.slice(/[xX]/u.test(v[1]) ? 2 : 1), /[xX]/u.test(v[1]) ? 16 : 10);
      const replacements = {0:65533,13:13,128:8364,130:8218,131:402,132:8222,133:8230,134:8224,135:8225,136:710,137:8240,138:352,139:8249,140:338,142:381,145:8216,146:8217,147:8220,148:8221,149:8226,150:8211,151:8212,152:732,153:8482,154:353,155:8250,156:339,158:382,159:376};
      if (n in replacements) return String.fromCodePoint(replacements[n]);
      if (n > 0x10ffff || n >= 0xd800 && n <= 0xdfff) return '\ufffd';
      if ((n >= 1 && n <= 8) || n === 11 || (n >= 14 && n <= 31) || (n >= 127 && n <= 159 && ![129,141,143,144,157].includes(n)) || (n >= 0xfdd0 && n <= 0xfdef) || (n & 0xffff) >= 0xfffe) return '';
      return String.fromCodePoint(n);
    }
    for (let n = v.length; n > 1; n--) if (v.slice(0, n) in C.entities) return C.entities[v.slice(0, n)] + v.slice(n);
    return whole;
  });
}
const normalize = text => trim(fold(unescapeHTML(text).normalize('NFKC'))).replace(new RegExp(`${WS}+`, 'gu'), ' ');
const textValue = x => {
  if (typeof x !== 'string' || codePointLength(x) > 200000 || x.includes('\0')) fail('invalid_or_oversized_text');
  return x;
};
function urlValue(x) {
  textValue(x);
  try {
    const u = new URL(x);
    if (!/^https?:\/\//iu.test(x) || !u.hostname || u.username || u.password || has('\\s', x) || /[\x00-\x1f]/u.test(x)) fail('invalid_url');
    return x;
  } catch { fail('invalid_url'); }
}
const segment = (field, start, text, location = field, quoted = false) => ({field, start, end: start + codePointLength(text), text, location, quoted});
const plainSpan = s => ({field:s.field, start:s.start, end:s.end, text:s.text, location:s.location});
function emailSegments(field, text) {
  let offset = 0, reply = false;
  return (text.match(/[^\r\n\v\f\x1c-\x1e\x85\u2028\u2029]*(?:\r\n|[\r\n\v\f\x1c-\x1e\x85\u2028\u2029]|$)/gu) ?? [])
    .filter(Boolean).map(line => {
      if (field === 'body' && has('^\\s*(?:On .+ wrote:|-+\\s*(?:Original|Forwarded) Message\\s*-+|Begin forwarded message:)', line)) reply = true;
      const s = segment(field, offset, line, field, field === 'body' && (reply || trim(line).startsWith('>')));
      offset = s.end; return s;
    });
}
// Source-spelling HTML scanner. No DOM, script execution or normalized offsets.
// Unsupported token forms fail explicitly; differential coverage is mandatory.
function htmlSegments(html) {
  const segments = [], structures = [], stack = [];
  let i = 0, nodes = 0;
  const voids = new Set('area base br col embed hr img input link meta param source track wbr'.split(' '));
  const hiddenTags = new Set('script style template noscript textarea'.split(' '));
  const data = (start, end) => {
    if (end === start || stack.some(n => n.hidden)) return;
    const location = stack.map(n => n.location).join('/') || 'document';
    const s = segment('html', utf16ToCodePoint(html, start), html.slice(start, end), location, stack.some(n => n.quoted));
    const prev = segments.at(-1);
    if (prev && prev.end === s.start && prev.location === location) { prev.end = s.end; prev.text += s.text; }
    else segments.push(s);
  };
  while (i < html.length) {
    if (['script', 'style'].includes(stack.at(-1)?.tag)) {
      const re = new RegExp(`</${stack.at(-1).tag}\\s*>`, 'giu'); re.lastIndex = i;
      const m = re.exec(html); if (!m) { i = html.length; break; } i = m.index;
    }
    if (html.startsWith('<!--', i)) {
      const m = /--\s*>/gu; m.lastIndex = i + 4; const end = m.exec(html);
      if (!end) fail('static_html_parsing_failed'); i = m.lastIndex; continue;
    }
    if (html.startsWith('<!', i)) {
      const end = html.indexOf('>', i + 2);
      if (end < 0 || !/^DOCTYPE[ \t\n\r\f]+html[ \t\n\r\f]*$/iu.test(html.slice(i + 2, end))) fail('static_html_parsing_failed');
      i = end + 1; continue;
    }
    if (html.startsWith('<?', i)) fail('static_html_parsing_failed');
    if (/^<\/[a-zA-Z]/u.test(html.slice(i))) {
      const m = /^<\/([a-zA-Z][^\t\n\r\f />]*)\s*>/u.exec(html.slice(i));
      if (!m) fail('unsupported_html_end_tag');
      const tag = m[1].toLowerCase(), index = stack.findLastIndex(n => n.tag === tag);
      if (index >= 0) stack.splice(index); i += m[0].length; continue;
    }
    if (/^<[a-zA-Z]/u.test(html.slice(i))) {
      const m = /^<([a-zA-Z][^\t\n\r\f />]*)(?:[^>"']|"[^"]*"|'[^']*')*>/u.exec(html.slice(i));
      if (!m) fail('unsupported_html_start_tag');
      nodes++; if (nodes > 20000 || stack.length >= 128) fail('html_structure_budget');
      const tag = m[1].toLowerCase(), attrs = {};
      const rest = m[0].slice(1 + m[1].length, -1).replace(/\/$/u, '');
      const attribute = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]*)))?/gu;
      for (const a of rest.matchAll(attribute)) attrs[a[1].toLowerCase()] = a[2] === undefined && a[3] === undefined && a[4] === undefined ? null : unescapeHTML(a[2] ?? a[3] ?? a[4]);
      const style = (attrs.style ?? '').replace(new RegExp(`${WS}+`, 'gu'), '').toLowerCase();
      const hidden = stack.some(n => n.hidden) || hiddenTags.has(tag) || 'hidden' in attrs || attrs['aria-hidden'] === 'true' || style.includes('display:none') || style.includes('visibility:hidden') || tag === 'input' && (attrs.type ?? '').toLowerCase() === 'hidden';
      const quoted = stack.some(n => n.quoted) || tag === 'blockquote';
      const location = `${tag}[${nodes}]`;
      if (!hidden) structures.push({tag, location:[...stack.map(n => n.location), location].join('/'), start:utf16ToCodePoint(html, i), end:utf16ToCodePoint(html, i + m[0].length)});
      if (!voids.has(tag) && !/\/>$/u.test(m[0])) stack.push({tag, location, hidden, quoted});
      i += m[0].length; continue;
    }
    let end = html.indexOf('<', i + 1); if (end < 0) end = html.length;
    data(i, end); i = end;
  }
  return {segments, structures};
}
const kinds = {email:'content_bearing_email', webpage:'content_bearing_webpage', url:'standalone_url', technical:'engineered_technical_record'};
export function preprocess(raw) {
  if (!obj(raw) || !(raw.kind in kinds)) fail('artifact_kind');
  const allowed = {email:['subject','body','sender','reply_to','headers','body_collection_authorized','study_purpose'], webpage:['html','visible_text','title','page_url'], url:['url'], technical:[]}[raw.kind].concat(['kind','urls','link_extraction_authorized']);
  if (Object.keys(raw).some(k => !allowed.includes(k))) fail('unknown_artifact_fields');
  for (const flag of ['body_collection_authorized','link_extraction_authorized']) if (flag in raw && typeof raw[flag] !== 'boolean') fail('boolean_consent_required');
  if ('urls' in raw && (!Array.isArray(raw.urls) || raw.urls.length > 500)) fail('invalid_url_collection');
  if (raw.urls?.length && raw.link_extraction_authorized !== true) fail('link_consent_required');
  (raw.urls ?? []).forEach(urlValue);
  let segments = [], structures = [];
  if (raw.kind === 'email') {
    if ('body' in raw && (raw.body_collection_authorized !== true || !trim(textValue(raw.study_purpose ?? '')))) fail('body_consent_required');
    for (const field of ['subject','body']) if (field in raw) segments.push(...emailSegments(field, textValue(raw[field])));
    for (const field of ['sender','reply_to']) if (field in raw) textValue(raw[field]);
    if ('headers' in raw && (!obj(raw.headers) || Object.keys(raw.headers).some(k => !['date','message-id','in-reply-to','references','content-type'].includes(k.toLowerCase())))) fail('invalid_headers');
    Object.values(raw.headers ?? {}).forEach(textValue);
  } else if (raw.kind === 'webpage') {
    if ('html' in raw && 'visible_text' in raw) fail('duplicate_content_views');
    for (const field of ['title','visible_text']) if (field in raw) segments.push(segment(field, 0, textValue(raw[field])));
    if ('html' in raw) {
      // URL joining and malformed HTML corner cases require their own exact port.
      if (raw.link_extraction_authorized) fail('html_link_extraction_not_yet_ported');
      const parsed = htmlSegments(textValue(raw.html)); segments.push(...parsed.segments); structures = parsed.structures;
    }
    if ('page_url' in raw) urlValue(raw.page_url);
  } else if (raw.kind === 'url') urlValue(raw.url);
  if (raw.link_extraction_authorized) for (const s of segments) {
    for (const m of matches('https?://[^\\s<>"\']+', s.text)) urlValue(m.text.replace(/[.,;!?\)\]]+$/u, ''));
  }
  const model_text = normalize(segments.filter(s => !s.quoted).map(s => s.text).join('\n'));
  return {segments, structures, modality_id:kinds[raw.kind], required_content_available:!!model_text,
    conditional_evidence_available:!!(raw.sender && trim(raw.sender)) || !!structures.length,
    sender:raw.sender ?? null, reply_to:raw.reply_to ?? null, page_url:raw.page_url ?? null};
}
class ContextIndex {
  constructor(artifact) {
    this.positions = new Map(); this.fields = {}; this.quotes = {};
    for (const s of artifact.segments) {
      if (s.quoted || [...this.positions.keys()].some(p => equal(p,s))) continue;
      this.positions.set(s, codePointLength(this.fields[s.field] ?? ''));
      this.fields[s.field] = (this.fields[s.field] ?? '') + s.text + '\n';
    }
    for (const [field, text] of Object.entries(this.fields)) this.quotes[field] = matches(C.patterns.QUOTATION,text);
  }
  suppressed(s, a, b, negative = false) {
    if (s.quoted || !this.positions.has(s)) return true;
    const offset = this.positions.get(s), start = offset + a, end = offset + b, text = this.fields[s.field], chars = cp(text);
    const punctuation = chars.flatMap((c,i) => /[.!?]/u.test(c) ? [i] : []);
    const left = (punctuation.filter(p => p < start).at(-1) ?? -1) + 1;
    const right = punctuation.find(p => p >= end) ?? chars.length;
    const context = chars.slice(Math.max(left,start-320),Math.min(right,end+320)).join('');
    const nearby = chars.slice(Math.max(0,start-320),Math.min(chars.length,end+320)).join('');
    const quote = this.quotes[s.field].filter(q => q.start <= end-1).at(-1);
    if (quote && quote.end > start) return true;
    if ((chars.slice(Math.max(left,start-320),start).filter(c => c === '"').length % 2)) return true;
    return has(C.patterns.EDUCATIONAL,nearby) || has(C.patterns.REPORTED,nearby) || has(C.patterns[negative ? 'COUNTEREXAMPLE' : 'NEGATION'],context);
  }
}
function contextAllowed(s,a,b,indicator,guards) {
  return !(indicator === 'confidentiality_isolation' && matches(C.patterns.NEGATION,codePointSlice(s.text,a,b)).length > 1 || has('\\b(?:hypothetical|suppose|imagine|educational|security lesson|for instance|as an example)\\b',s.text) || s.text.includes('?') || guards.suppressed(s,a,b,indicator === 'confidentiality_isolation'));
}
function units(artifact) {
  const all = [];
  for (const s of artifact.segments) for (const m of matches('[^.!?;\\n]+[.!?;]?',s.text)) {
    const text = trim(m.text); if (!text) continue;
    const start = m.start + codePointLength(m.text) - codePointLength(m.text.replace(new RegExp(`^${WS}+`,'u'),''));
    all.push([s,start,start+codePointLength(text)]); if (all.length > 64) return all;
  }
  return all;
}
function locate(artifact, span) {
  if (!obj(span) || typeof span.field !== 'string' || typeof span.location !== 'string' || typeof span.text !== 'string' || typeof span.quoted !== 'boolean' || !Number.isInteger(span.start) || !Number.isInteger(span.end)) fail('invalid_independent_span');
  for (const s of artifact.segments) if (s.field === span.field && s.location === span.location && s.start <= span.start && span.start < span.end && span.end <= s.end && span.quoted === s.quoted && codePointSlice(s.text,span.start-s.start,span.end-s.start) === span.text) return [s,span.start-s.start,span.end-s.start];
  fail('independent_span_not_in_artifact');
}
const domainOK = x => typeof x === 'string' && /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/u.test(x) && x.length <= 253;
function detectorContext(context) {
  const ctx = context ?? {identities:[],authority_reviews:[]};
  if (!keys(ctx,['identities','authority_reviews'])) fail('typed_context_required');
  for (const items of [ctx.identities,ctx.authority_reviews]) if (!Array.isArray(items) || items.length > 64) fail('reference_budget');
  for (const r of ctx.identities) {
    if (!keys(r,['indicator_id','entity','claim','authorized_domains','reference_id','delegation_audited']) || !['impersonation','brand_exploitation'].includes(r.indicator_id) || typeof r.entity !== 'string' || !trim(r.entity) || typeof r.reference_id !== 'string' || !trim(r.reference_id) || typeof r.delegation_audited !== 'boolean' || !Array.isArray(r.authorized_domains) || !r.authorized_domains.length || r.authorized_domains.some(d => !domainOK(d)) || new Set(r.authorized_domains).size !== r.authorized_domains.length) fail('invalid_identity_reference');
  }
  for (const r of ctx.authority_reviews) if (!keys(r,['role','directive','authorization','reference_id']) || !['authorized','contradicted','unknown'].includes(r.authorization) || typeof r.reference_id !== 'string' || !trim(r.reference_id)) fail('invalid_authority_review');
  for (const [items, key] of [[ctx.identities,r=>[r.indicator_id,r.claim]],[ctx.authority_reviews,r=>[r.role,r.directive]]]) if (new Set(items.map(r=>canonical(key(r)))).size !== items.length) fail('duplicate_references');
  return ctx;
}
function identityFields(a) {
  const fields = [];
  for (const field of ['sender','reply_to']) if (a[field]) {
    const value = a[field];
    // Deliberately reject complex RFC5322 syntax until exact parseaddr parity is established.
    const m = /^(?:[^<>]*<([^<>]+)>|([^<>\s]+))$/u.exec(value);
    if (!m) fail('unsupported_mailbox_syntax');
    const address = m[1] ?? m[2], domain = address.split('@').at(-1).toLowerCase();
    if (address.split('@').length === 2 && domainOK(domain)) fields.push([domain,segment(field,0,value)]);
  }
  if (a.page_url) {
    const host = new URL(a.page_url).hostname;
    if (domainOK(host)) fields.push([host,segment('page_url',0,a.page_url)]);
  }
  return fields;
}
function trust(a,ctx,guards,available) {
  const reports = Object.fromEntries(['authority','impersonation','brand_exploitation'].map(i=>[i,{evaluated:false,hits:[]} ]));
  if (!available) return reports;
  for (const r of ctx.identities) locate(a,r.claim);
  for (const r of ctx.authority_reviews) { locate(a,r.role); locate(a,r.directive); }
  const fields = identityFields(a);
  for (const i of ['impersonation','brand_exploitation']) {
    const relevant = ctx.identities.filter(r=>r.indicator_id === i); let evaluated = 0;
    for (const r of relevant) {
      if (!r.delegation_audited || !fields.length) continue;
      const unit = locate(a,r.claim);
      const escaped = r.entity.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      if (!has(`^(?:we are|this is|official notice from|on behalf of)\\s+${escaped}\\Z`,r.claim.text) || guards.suppressed(...unit)) continue;
      evaluated++;
      if (fields.some(([domain])=>!r.authorized_domains.includes(domain))) reports[i].hits.push({spans:[r.claim,...fields.map(([,s])=>s)],rule:'identity.audited_domain_conflict',reference:r.reference_id});
    }
    reports[i].evaluated = !!reports[i].hits.length || !!(relevant.length && evaluated === relevant.length);
  }
  let observed = 0, reviewed = 0;
  for (const s of guards.positions.keys()) for (const m of matches(C.patterns.ROLE,s.text)) {
    const tail = codePointSlice(s.text,m.end,m.end+160).split(/[.!?\n]/u,1)[0];
    const d = matches(C.patterns.DIRECTIVE,tail)[0]; if (!d) continue;
    const role = segment(s.field,s.start+m.start,m.text,s.location,s.quoted);
    const directive = segment(s.field,s.start+m.end+d.start,d.text,s.location);
    if (guards.suppressed(s,m.start,m.end+d.end)) continue;
    observed++;
    const r = ctx.authority_reviews.find(r=>equal(r.role,role)&&equal(r.directive,directive));
    if (r && r.authorization !== 'unknown') { reviewed++; if (r.authorization === 'contradicted') reports.authority.hits.push({spans:[role,directive],rule:'authority.role_with_directive',reference:r.reference_id}); }
  }
  reports.authority.evaluated = !!reports.authority.hits.length || !!(observed && reviewed === observed);
  return reports;
}
function symbolic(record,ctx) {
  if (!obj(record) || typeof record.record_id !== 'string' || !trim(record.record_id) || typeof record.source_dataset !== 'string' || !trim(record.source_dataset)) fail('canonical_record_required');
  excluded([record.source_dataset,record.record_id,record.source_record_id ?? null,record.provenance,record.source_metadata ?? {}]);
  if (!obj(record.provenance) || !Object.keys(record.provenance).length || !obj(record.source_metadata ?? {})) fail('provenance_required');
  finiteJSON(record);
  const raw = record.artifact_input;
  if (!obj(raw) || kinds[raw.kind] !== record.modality) fail('modality_mismatch');
  const expected = Object.keys(raw).filter(k=>!['kind','study_purpose','body_collection_authorized','link_extraction_authorized'].includes(k));
  if (!Array.isArray(record.fields_available) || new Set(record.fields_available).size !== record.fields_available.length || !equal([...record.fields_available].sort(),expected.sort())) fail('available_fields_mismatch');
  const a = preprocess(raw);
  if (record.content_available !== null && record.content_available !== undefined && (typeof record.content_available !== 'boolean' || record.content_available !== a.required_content_available)) fail('content_availability_mismatch');
  const cb = C.codebook, order = cb.vector_ordering.dimension_order, modality = cb.modalities.find(m=>m.id === a.modality_id);
  const mask = order.map(d=>+(modality.support_by_dimension[d] !== 'U' && a.required_content_available && (modality.support_by_dimension[d] !== 'A*' || a.conditional_evidence_available)));
  const guards = new ContextIndex(a), evidence = {}, parents = {};
  for (const d of cb.dimensions) for (const i of d.indicators) { evidence[i.id]=[]; parents[i.id]=d.id; }
  const seen = new Set();
  for (const s of guards.positions.keys()) for (const r of C.rules) if (mask[order.indexOf(parents[r.indicator_id])]) for (const m of matches(r.pattern,s.text)) {
    if (guards.suppressed(s,m.start,m.end,r.allow_negative_instruction)) continue;
    const span = plainSpan(segment(s.field,s.start+m.start,m.text,s.location));
    const key = canonical([r.rule_id,s.field,span.start,span.end]); if (seen.has(key)) continue; seen.add(key);
    evidence[r.indicator_id].push({span,supporting_spans:[],rule_id:r.rule_id,reference_id:null,provenance:'rule-based'});
  }
  const reports = trust(a,ctx,guards,!!mask[order.indexOf(parents.authority)]);
  for (const [id,r] of Object.entries(reports)) for (const hit of r.hits) evidence[id].push({span:plainSpan(hit.spans[0]),supporting_spans:hit.spans.slice(1).map(plainSpan),rule_id:hit.rule,reference_id:hit.reference,provenance:'rule-based'});
  const implemented = new Set(C.rules.map(r=>r.indicator_id));
  for (const [id,r] of Object.entries(reports)) if (r.evaluated) implemented.add(id);
  const rows = Object.entries(parents).map(([id,dimension])=>({indicator_id:id,dimension_id:dimension,
    deterministic_state:!mask[order.indexOf(dimension)] ? 'unavailable' : !implemented.has(id) ? null : evidence[id].length ? 'supported' : 'absent',
    evaluation_status:!mask[order.indexOf(dimension)] ? 'unavailable' : !implemented.has(id) ? 'not_evaluated' : 'rule_evaluated',evidence:evidence[id]}));
  return {a,guards,rows,mask,order,reports};
}
export const LABELS = Object.freeze(['entailment','neutral','contradiction']);
export function validateScores(scores) {
  if (!Array.isArray(scores) || scores.length !== 3) fail('three_score_records_required');
  return scores.map(item=>{
    if (!obj(item)) fail('malformed_score_record');
    const out = Object.fromEntries(LABELS.map(k=>[k,item[k]]));
    if (Object.values(out).some(v=>typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 1) || Math.abs(LABELS.reduce((s,k)=>s+out[k],0)-1) > .001) fail('invalid_probabilities');
    return out;
  });
}
function reason(scores,state) {
  const tops = scores.map(s=>LABELS.reduce((best,k)=>s[k] > s[best] ? k : best,LABELS[0]));
  if (scores.some(s=>LABELS.filter(k=>s[k]===Math.max(...Object.values(s))).length > 1) || new Set(tops).size > 1) return 'hypothesis_disagreement';
  if (tops[0] === 'entailment' && state !== 'supported') return 'semantic_candidate_without_rule_support';
  if (tops[0] !== 'entailment' && state === 'supported') return 'semantic_rule_disagreement';
  return null;
}
const semanticContract = () => ({...Object.fromEntries(['model','tokenizer','revision','hypotheses_sha256','max_tokens','oversized_evidence_policy','confidence_calibrated'].map(k=>[k,C.model[k]])),scorer_provenance:'explicit_injection_not_independently_authenticated'});
async function header(record,ctx,base) {
  return {schema_version:'1.0.0',policy_id:'deterministic_labels_semantic_review_v1',policy_version:'1.0.0',codebook_version:C.codebook.codebook_version,
    artifact_id:record.record_id,source_id:record.source_dataset,modality:record.modality,artifact_sha256:await fingerprint(record.artifact_input),ruleset_version:C.ruleset,
    semantic_contract:semanticContract(),provenance_metadata:{source_provenance_sha256:await fingerprint(record.provenance),detector_reference_ids:[...new Set([...ctx.identities,...ctx.authority_reviews].map(r=>r.reference_id))].sort(),independent_identity_truth_authenticated:false,source_custody_authenticated:false},
    preprocessing_contract:C.preprocessing,dimension_order:base.order,availability_mask:base.mask,semantic_changes_labels:false,learned_values:[null,null,null,null],
    research_release:{approved_for_E2_E3:false,approved_for_sealed_test:false,publishable_as_validated_results:false}};
}
function eligibility(row,base,ctx,all) {
  const identity = !['impersonation','brand_exploitation'].includes(row.indicator_id) || base.reports[row.indicator_id].evaluated && ctx.identities.some(r=>r.indicator_id === row.indicator_id && r.delegation_audited);
  const modality = !!base.mask[base.order.indexOf(row.dimension_id)];
  const eligibleUnits = all.filter(u=>contextAllowed(...u,row.indicator_id,base.guards));
  return {eligible:modality&&identity,eligibleUnits,blocked:eligibleUnits.length !== all.length,constraints:{modality_before:modality,identity_before:identity,context_before:eligibleUnits.length === all.length,spans_before_and_after:true,scores_after:true,label_preservation_after:true}};
}
export async function reviewRecord(record,{scorer=null,detectorContext:context=null}={}) {
  if (scorer !== null && typeof scorer?.score !== 'function') fail('explicit_scorer_interface_required');
  const ctx = detectorContext(context), base = symbolic(record,ctx), all = units(base.a), overflow=all.length>64;
  const limited=all.slice(0,64); let calls=0;
  const rows=[];
  for (const row of base.rows) {
    const {eligible,eligibleUnits,blocked,constraints}=eligibility(row,base,ctx,limited);
    const reasons=new Set(),failures=new Set(),candidates=[];
    if (row.evaluation_status==='not_evaluated') reasons.add('deterministic_not_evaluated');
    if (scorer !== null && eligible) {
      if (overflow) failures.add('semantic_budget_exhausted');
      for (const [s,start,end] of eligibleUnits) {
        if (calls>=512) {failures.add('semantic_budget_exhausted');break;} calls++;
        let scores;
        try { scores=validateScores(await scorer.score(codePointSlice(s.text,start,end),row.indicator_id)); }
        catch(e) {failures.add(e instanceof SemanticInferenceUnavailable ? 'semantic_unavailable':'semantic_failed');continue;}
        const r=reason(scores,row.deterministic_state);if(r)reasons.add(r);
        candidates.push({evidence:plainSpan(segment(s.field,s.start+start,codePointSlice(s.text,start,end),s.location)),scores,decision:'candidate_only',confidence_calibrated:false});
      }
    }
    if(blocked)reasons.add('context_requires_review');if(failures.size)reasons.add('semantic_failure');
    rows.push({...row,candidate_state:eligible?'abstained':'unavailable',semantic_status:!eligible?'unavailable':scorer===null?'not_requested':candidates.length&&failures.size?'partial':candidates.length?'scored':failures.size?'failed':'context_blocked',semantic_candidates:candidates,failure_codes:[...failures].sort(),needs_review:!!reasons.size,review_reasons:[...reasons].sort(),constraints});
  }
  const out={...await header(record,ctx,base),indicators:rows};
  await validateReview(out,record,{detectorContext:ctx});
  return out;
}
export function validateSpan(span,raw) {
  if(!obj(span)||typeof span.field!=='string'||typeof raw[span.field]!=='string'||!Number.isInteger(span.start)||!Number.isInteger(span.end)||span.start<0||span.start>=span.end||span.end>codePointLength(raw[span.field])||codePointSlice(raw[span.field],span.start,span.end)!==span.text)fail('invalid_evidence_span');
}
export async function validateReview(payload,record,{detectorContext:context=null}={}) {
  const ctx=detectorContext(context),base=symbolic(record,ctx),expected=await header(record,ctx,base);
  if(!keys(payload,[...Object.keys(expected),'indicators']))fail('review_schema_mismatch');
  for(const [k,v] of Object.entries(expected))if(!equal(payload[k],v))fail('review_identity_policy_or_version_mismatch');
  if(!Array.isArray(payload.indicators)||payload.indicators.length!==base.rows.length)fail('canonical_indicator_coverage_required');
  const all=units(base.a).slice(0,64);let total=0;
  for(let i=0;i<base.rows.length;i++) {
    const row=payload.indicators[i],original=base.rows[i];
    if(!keys(row,[...Object.keys(original),'candidate_state','semantic_status','semantic_candidates','failure_codes','needs_review','review_reasons','constraints']))fail('indicator_schema_mismatch');
    for(const [k,v] of Object.entries(original))if(!equal(row[k],v))fail('deterministic_labels_or_evidence_changed');
    const {eligible,blocked,constraints}=eligibility(original,base,ctx,all);
    if(row.candidate_state!==(eligible?'abstained':'unavailable')||!equal(row.constraints,constraints))fail('constraint_or_availability_mismatch');
    if(typeof row.needs_review!=='boolean'||!Array.isArray(row.review_reasons)||!Array.isArray(row.failure_codes)||row.failure_codes.some(v=>!['semantic_unavailable','semantic_failed','semantic_budget_exhausted'].includes(v))||new Set(row.failure_codes).size!==row.failure_codes.length||new Set(row.review_reasons).size!==row.review_reasons.length||row.needs_review!==!!row.review_reasons.length)fail('invalid_review_or_failure_state');
    if(!Array.isArray(row.semantic_candidates)||row.semantic_candidates.length>64)fail('invalid_candidate_collection');
    const n=row.semantic_candidates.length;
    if((total+=n)>512)fail('semantic_budget_exceeded');
    const statuses=!eligible?['unavailable']:n&&row.failure_codes.length?['partial']:n?['scored']:row.failure_codes.length?['failed']:['not_requested','context_blocked'];
    if(!statuses.includes(row.semantic_status)||row.semantic_status==='context_blocked'&&!blocked||!eligible&&(n||row.failure_codes.length))fail('inconsistent_semantic_status');
    const reasons=new Set();if(original.evaluation_status==='not_evaluated')reasons.add('deterministic_not_evaluated');if(blocked)reasons.add('context_requires_review');if(row.failure_codes.length)reasons.add('semantic_failure');
    const seen=new Set();
    for(const c of row.semantic_candidates) {
      if(!keys(c,['evidence','scores','decision','confidence_calibrated']))fail('candidate_schema_mismatch');
      const span=c.evidence;validateSpan(span,record.artifact_input);
      if(!keys(span,['field','start','end','text','location'])||typeof span.location!=='string')fail('invalid_candidate_locator');
      const key=canonical([span.field,span.location,span.start,span.end]);
      const unit=all.find(([s,a,b])=>s.field===span.field&&s.location===span.location&&s.start+a===span.start&&s.start+b===span.end);
      if(seen.has(key)||!unit||!contextAllowed(...unit,original.indicator_id,base.guards))fail('candidate_context_ineligible');seen.add(key);
      const scores=validateScores(c.scores);
      if(c.scores.some(s=>!keys(s,LABELS)))fail('evidence_only_semantic_scores_required');
      const r=reason(scores,original.deterministic_state);if(r)reasons.add(r);
      if(c.decision!=='candidate_only'||c.confidence_calibrated!==false)fail('unapproved_score_interpretation');
    }
    if(!equal([...reasons].sort(),[...row.review_reasons].sort()))fail('review_signal_not_supported_by_evidence');
  }
}
export function predictorValues(){fail('review_candidates_are_not_approved_predictors');}
export function recordFromRequest(r) {
  if(!keys(r,['schema_version','codebook_version','artifact_id','source_id','source_reference','modality','language','fields','body_collection_authorized','link_extraction_authorized','study_purpose']))fail('evidence_request_schema_mismatch');
  if(r.schema_version!=='1.0.0'||r.codebook_version!==C.codebook.codebook_version)fail('incompatible_evidence_request_version');
  for(const k of ['artifact_id','source_id','source_reference']) {if(typeof r[k]!=='string'||!trim(r[k])||codePointLength(r[k])>1024||/[\x00-\x1f]/u.test(r[k]))fail('bounded_opaque_identifier_required');excluded(r[k]);}
  const kind=Object.keys(kinds).find(k=>kinds[k]===r.modality);if(!kind)fail('canonical_modality_required');
  if(typeof r.language!=='string'||! /^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/u.test(r.language))fail('explicit_language_required');
  if(['email','webpage'].includes(kind)&&r.language.split('-')[0]!=='en')fail('unsupported_or_unknown_language');
  const fields={email:['subject','body','sender','reply_to','headers','urls'],webpage:['html','visible_text','title','page_url','urls'],url:['url','urls'],technical:[]}[kind];
  if(!obj(r.fields)||Object.keys(r.fields).some(k=>!fields.includes(k))||Object.keys(r.fields).length>8)fail('evidence_only_fields_required');
  if(typeof r.body_collection_authorized!=='boolean'||typeof r.link_extraction_authorized!=='boolean')fail('explicit_boolean_consent_required');
  if(typeof r.study_purpose!=='string'||codePointLength(r.study_purpose)>2000)fail('bounded_study_purpose_required');
  if(kind!=='email'&&r.body_collection_authorized)fail('email_body_consent_not_applicable');
  const raw={kind,...r.fields,link_extraction_authorized:r.link_extraction_authorized};
  if(kind==='email')Object.assign(raw,{body_collection_authorized:r.body_collection_authorized,study_purpose:r.study_purpose});
  const record={record_id:r.artifact_id,source_dataset:r.source_id,modality:r.modality,artifact_input:raw,fields_available:Object.keys(r.fields),content_available:null,provenance:{reference:r.source_reference,language_declared:r.language},source_record_id:null,source_metadata:{}};
  symbolic(record,detectorContext(null));return record;
}
