import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const [sessionName,action='game.status',fields='{}',label='']=process.argv.slice(2);
if(!/^UIF-Q\d{3}-[a-z-]+$/.test(sessionName||''))throw new Error('Explicit QA session required');
const session=path.join(root,'workspace/sessions',sessionName);
const meta=JSON.parse(fs.readFileSync(path.join(session,'session.json'),'utf8').replace(/^\uFEFF/,''));
if(meta.port!==49322 || path.resolve(meta.path)!==session || !meta.exe.includes('qa-ppsspp-1.20.4'))throw new Error('Foreign target');
const installed=fs.readFileSync(path.join(path.dirname(meta.exe),'installed.txt'),'utf8').trim().replace(/^\uFEFF/,'');
if(path.resolve(installed)!==path.join(session,'memstick'))throw new Error('QA session not active');
const ws=new WebSocket('ws://127.0.0.1:49322/debugger');
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;setTimeout(()=>j(new Error('Connection timeout')),8000).unref()});
let n=0;
function call(event,fields={},broadcast=false){return new Promise((r,j)=>{
 const ticket=String(++n);const timer=setTimeout(()=>{ws.removeEventListener('message',listen);j(new Error('Timeout '+event));},25000);
 function listen(e){const a=JSON.parse(e.data);if(a.ticket===ticket || broadcast&&a.event===event){clearTimeout(timer);ws.removeEventListener('message',listen);a.event==='error'?j(new Error(JSON.stringify(a))):r(a);}}
 ws.addEventListener('message',listen);ws.send(JSON.stringify({event,ticket,...fields}));
});}
function saveResult(res,suffix=''){
 if(res.uri){
  if(!/^[a-z0-9_-]+$/i.test(label))throw new Error('Capture label required');
  const ext=res.uri.startsWith('data:image/png')?'.png':'.ppdmp';
  const dest=path.join(session,'captures',label+suffix+ext);fs.writeFileSync(dest,Buffer.from(res.uri.split(',')[1],'base64'));delete res.uri;res.path=dest;
 }
 return res;
}
try{
 await call('version');
 const identity=await call('game.status');if(identity.game?.id!=='NPUH10126')throw new Error('Wrong game');
 let result;
 if(action==='capture'){
  const before=await call('cpu.status');if(before.stepping)throw new Error('Already paused; no state takeover');
  try{await call('cpu.stepping',{},true);result={};for(const kind of ['screenshot','renderColor','texture']){
    try{result[kind]=saveResult(await call('gpu.buffer.'+kind,{alpha:true}),'-'+kind);}catch(e){result[kind]={error:String(e)};}
  }}finally{const current=await call('cpu.status');if(current.stepping)await call('cpu.resume',{},true);}
 }else result=saveResult(await call(action,JSON.parse(fields)));
 if(label)fs.writeFileSync(path.join(session,'captures',label+'.json'),JSON.stringify({identity,result},null,2));
 console.log(JSON.stringify(result));
}finally{ws.close();}
