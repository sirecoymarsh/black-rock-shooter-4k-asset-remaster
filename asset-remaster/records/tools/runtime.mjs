import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const active=JSON.parse(fs.readFileSync(path.join(root,'workspace/runtime/active_session.json'),'utf8').replace(/^\uFEFF/,''));
if(!path.resolve(active.path).startsWith(path.join(root,'workspace/sessions')+path.sep)) throw new Error('Foreign session');
if(active.port!==49321)throw new Error('Foreign debugger port');
const ws=new WebSocket('ws://127.0.0.1:'+active.port+'/debugger');
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;setTimeout(()=>j(new Error('connect timeout')),8000).unref()});
let n=0;function call(event,fields={}){return new Promise((r,j)=>{const ticket=String(++n);const t=setTimeout(()=>{ws.removeEventListener('message',f);j(new Error('timeout '+event))},10000);const f=e=>{const a=JSON.parse(e.data);if(a.ticket===ticket){clearTimeout(t);ws.removeEventListener('message',f);a.event==='error'?j(new Error(JSON.stringify(a))):r(a)}};ws.addEventListener('message',f);ws.send(JSON.stringify({event,ticket,...fields}));})}
try{
 const identity=await call('game.status');if(identity.game?.id!=='NPUH10126')throw new Error('Wrong game');
 const [action='game.status',fields='{}',label='']=process.argv.slice(2);const res=await call(action,JSON.parse(fields));
 if(res.uri && label){if(!/^[a-z0-9_-]+$/i.test(label))throw new Error('Unsafe label');const dest=path.join(active.path,'captures',label+'.png');fs.writeFileSync(dest,Buffer.from(res.uri.split(',')[1],'base64'));delete res.uri;res.path=dest;}
 if(label)fs.writeFileSync(path.join(active.path,'captures',label+'.json'),JSON.stringify({identity,result:res},null,2));
 console.log(JSON.stringify(res));
}catch(e){console.error(String(e));process.exitCode=1}finally{ws.close()}