// Source-spelling HTTP URL split/join compatibility with CPython urllib.parse.
// Do not use WHATWG serialization: it encodes Unicode and normalizes hosts/paths.
// PSF License; see PYTHON-NOTICE.txt.
function split(value, defaultScheme='') {
  value=value.replace(/^[\x00-\x20]+/u,'').replace(/[\t\r\n]/gu,'');
  let scheme=defaultScheme,netloc='',query='',fragment='',path=value;
  const match=/^([a-zA-Z][a-zA-Z0-9+.-]*):/u.exec(path);
  if(match){scheme=match[1].toLowerCase();path=path.slice(match[0].length);}
  if(path.startsWith('//')){
    const end=path.slice(2).search(/[/?#]/u);const index=end<0?path.length:end+2;
    netloc=path.slice(2,index);path=path.slice(index);
    if(netloc.includes('[')!==netloc.includes(']'))throw Error('invalid_url');
    if(netloc.includes('[')){
      const host=netloc.slice(netloc.indexOf('[')+1,netloc.indexOf(']'));
      if(host.startsWith('v')){if(!/^v[0-9a-fA-F]+\..+$/u.test(host))throw Error('invalid_url');}
      else {try{new URL('http://['+host.replace(/%.*/u,'')+']/');}catch{throw Error('invalid_url');}}
    }
    const normalized=netloc.replace(/[@:#?]/gu,'').normalize('NFKC');
    if(normalized!==netloc.replace(/[@:#?]/gu,'')&&/[/?#@:]/u.test(normalized))throw Error('invalid_url');
  }
  let index=path.indexOf('#');if(index>=0){fragment=path.slice(index+1);path=path.slice(0,index);}
  index=path.indexOf('?');if(index>=0){query=path.slice(index+1);path=path.slice(0,index);}
  const authority=netloc.slice(netloc.lastIndexOf('@')+1);
  let hostname,port;
  if(authority.includes('[')){hostname=authority.slice(authority.indexOf('[')+1,authority.indexOf(']'));const tail=authority.slice(authority.indexOf(']')+1);port=tail.includes(':')?tail.slice(tail.indexOf(':')+1):'';}
  else {const colon=authority.indexOf(':');hostname=colon>=0?authority.slice(0,colon):authority;port=colon>=0?authority.slice(colon+1):'';}
  return {scheme,netloc,path,query,fragment,hostname:hostname.toLowerCase(),port,hasCredentials:netloc.includes('@')};
}
export function splitHTTP(value) {
  const parsed=split(value);
  if(!['http','https'].includes(parsed.scheme)||!parsed.hostname||parsed.hasCredentials||parsed.port&&(!/^[0-9]+$/u.test(parsed.port)||Number(parsed.port)>65535))throw Error('invalid_url');
  return parsed;
}
function parse(value,scheme='') {
  const out=split(value,scheme);out.params='';
  const semicolon=out.path.indexOf(';',out.path.lastIndexOf('/')+1);
  if(semicolon>=0){out.params=out.path.slice(semicolon+1);out.path=out.path.slice(0,semicolon);}
  return out;
}
const relative=new Set(['','ftp','http','gopher','nntp','imap','wais','file','https','shttp','mms','prospero','rtsp','rtsps','rtspu','sftp','svn','svn+ssh','ws','wss']);
const netlocSchemes=new Set([...relative,'telnet','snews','rsync','nfs','git','git+ssh']);
function unparse({scheme,netloc,path,params,query,fragment}) {
  if(params)path+=';'+params;
  if(netloc||scheme&&netlocSchemes.has(scheme)&&!path.startsWith('//')){
    if(path&&!path.startsWith('/'))path='/'+path;
    path='//'+netloc+path;
  }
  return (scheme?scheme+':':'')+path+(query?'?'+query:'')+(fragment?'#'+fragment:'');
}
export function joinURL(base,value) {
  if(!base)return value;if(!value)return base;
  const b=parse(base),u=parse(value,b.scheme);
  if(u.scheme!==b.scheme||!relative.has(u.scheme))return value;
  if(netlocSchemes.has(u.scheme)){if(u.netloc)return unparse(u);u.netloc=b.netloc;}
  if(!u.path&&!u.params){u.path=b.path;u.params=b.params;if(!u.query)u.query=b.query;return unparse(u);}
  const parts=b.path.split('/');if(parts.at(-1)!=='')parts.pop();
  let segments;
  if(u.path.startsWith('/'))segments=u.path.split('/');
  else{segments=parts.concat(u.path.split('/'));segments=[segments[0],...segments.slice(1,-1).filter(Boolean),...(segments.length>1?[segments.at(-1)]:[])];}
  const resolved=[];for(const s of segments){if(s==='..')resolved.pop();else if(s!=='.')resolved.push(s);}
  if(['.','..'].includes(segments.at(-1)))resolved.push('');
  u.path=resolved.join('/')||'/';return unparse(u);
}
