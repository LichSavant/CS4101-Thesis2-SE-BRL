// Compatibility translation of CPython 3.12.10 email.utils.parseaddr(strict=True)
// and email._parseaddr.AddrlistClass. PSF License; see PYTHON-NOTICE.txt.
// Returns the canonical pair, including ('','') for invalid/multiple addresses.
const specials='()<>@,:;."[]', fws=' \t\r\n', atomends=specials+fws;
const strip=s=>s.replace(/^[\t-\r\x1c-\x20\x85\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t-\r\x1c-\x20\x85\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/gu,'');
function* escaped(s) {
  let escape=false;
  for(let pos=0;pos<s.length;pos++) {
    if(escape){yield[pos,'\\'+s[pos]];escape=false;}
    else if(s[pos]==='\\')escape=true;
    else yield[pos,s[pos]];
  }
  if(escape)yield[s.length-1,'\\'];
}
function balanced(s) {
  let start=0,open=null,parts=[];
  for(const [pos,ch]of escaped(s))if(ch==='"') {
    if(open===null)open=pos;
    else {if(start!==open)parts.push(s.slice(start,open));start=pos+1;open=null;}
  }
  if(start<s.length)parts.push(s.slice(start));
  let count=0;
  for(const [,ch]of escaped(parts.join(''))) {
    if(ch==='(')count++;
    else if(ch===')'&&--count<0)return false;
  }
  return count===0;
}
class AddressParser {
  constructor(field){this.field=field;this.pos=0;this.comments=[];}
  get ch(){return this.field[this.pos];}
  get more(){return this.pos<this.field.length;}
  next(){let ws='';while(this.more){if(fws.includes(this.ch)){if(!'\n\r'.includes(this.ch))ws+=this.ch;this.pos++;}else if(this.ch==='(')this.comments.push(this.comment());else break;}return ws;}
  delimited(begin,ends,comments=true){
    if(this.ch!==begin)return '';
    let out='',quote=false;this.pos++;
    while(this.more){
      if(quote){out+=this.ch;quote=false;}
      else if(ends.includes(this.ch)){this.pos++;break;}
      else if(comments&&this.ch==='('){out+=this.comment();continue;}
      else if(this.ch==='\\')quote=true;
      else out+=this.ch;
      this.pos++;
    }
    return out;
  }
  comment(){return this.delimited('(',')\r');}
  quote(){return this.delimited('"','"\r',false);}
  atom(ends=atomends){let out='';while(this.more&&!ends.includes(this.ch)){out+=this.ch;this.pos++;}return out;}
  phrase(){const out=[],ends=atomends.replace('.','');while(this.more){if(fws.includes(this.ch))this.pos++;else if(this.ch==='"')out.push(this.quote());else if(this.ch==='(')this.comments.push(this.comment());else if(ends.includes(this.ch))break;else out.push(this.atom(ends));}return out;}
  domain(){
    let out='';while(this.more){
      if(' \t'.includes(this.ch))this.pos++;
      else if(this.ch==='(')this.comments.push(this.comment());
      else if(this.ch==='[')out+='['+this.delimited('[',']\r',false)+']';
      else if(this.ch==='.'){this.pos++;out+='.';}
      else if(this.ch==='@')return '';
      else if(atomends.includes(this.ch))break;
      else out+=this.atom();
    }return out;
  }
  spec(){
    const out=[];this.next();
    while(this.more){
      let preserve=true;
      if(this.ch==='.') {if(out.length&&!strip(out.at(-1)))out.pop();out.push('.');this.pos++;preserve=false;}
      else if(this.ch==='"')out.push('"'+this.quote().replace(/\\/gu,'\\\\').replace(/"/gu,'\\"')+'"');
      else if(atomends.includes(this.ch)){if(out.length&&!strip(out.at(-1)))out.pop();break;}
      else out.push(this.atom());
      const ws=this.next();if(preserve&&ws)out.push(ws);
    }
    if(!this.more||this.ch!=='@')return out.join('');
    out.push('@');this.pos++;this.next();const domain=this.domain();
    return domain?out.join('')+domain:'';
  }
  route(){
    if(this.ch!=='<')return '';
    let expect=false,out='';this.pos++;this.next();
    while(this.more){
      if(expect){this.domain();expect=false;}
      else if(this.ch==='>'){this.pos++;break;}
      else if(this.ch==='@'){this.pos++;expect=true;}
      else if(this.ch===':')this.pos++;
      else{out=this.spec();this.pos++;break;}
      this.next();
    }return out;
  }
  address(){
    this.comments=[];this.next();const oldpos=this.pos,oldcomments=this.comments;
    const words=this.phrase();this.next();let out=[];
    if(!this.more){if(words.length)out=[[this.comments.join(' '),words[0]]];}
    else if('.@'.includes(this.ch)){this.pos=oldpos;this.comments=oldcomments;const spec=this.spec();out=[[this.comments.join(' '),spec]];}
    else if(this.ch===':'){
      this.pos++;while(this.more){this.next();if(this.more&&this.ch===';'){this.pos++;break;}out.push(...this.address());}
    }else if(this.ch==='<'){
      const route=this.route();out=[[words.join(' ')+(this.comments.length?' ('+this.comments.join(' ')+')':''),route]];
    }else if(words.length)out=[[this.comments.join(' '),words[0]]];
    else if(specials.includes(this.ch))this.pos++;
    this.next();if(this.more&&this.ch===',')this.pos++;
    return out;
  }
  list(){const out=[];while(this.more){const items=this.address();out.push(...(items.length?items:[['','']]));}return out;}
}
export function parseAddress(value) {
  if(typeof value!=='string')return ['',''];
  const addresses=new AddressParser(balanced(value)?value:"('', '')").list().map(v=>v[1].includes('[')?['','']:v);
  return addresses.length===1?addresses[0]:['',''];
}
