import fs from 'node:fs';
const root='P:/AI/Codex/projects/black-rock-shooter-hd-retexture';
const meta=JSON.parse(fs.readFileSync(root+'/workspace/model_port/runtime_test/active_test.json','utf8').replace(/^\uFEFF/,''));
if(meta.port!==49219)throw Error('Unexpected test target');
const ws=new WebSocket('ws://127.0.0.1:49219/debugger');
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;setTimeout(()=>j(Error('connect timeout')),7000).unref()});
let ticket=0;
function call(event,fields={}){return new Promise((resolve,reject)=>{const id=String(++ticket),timer=setTimeout(()=>{ws.removeEventListener('message',listen);reject(Error('timeout '+event))},7000);function listen(e){const m=JSON.parse(e.data);if(m.ticket===id){clearTimeout(timer);ws.removeEventListener('message',listen);m.event==='error'?reject(Error(JSON.stringify(m))):resolve(m)}}ws.addEventListener('message',listen);ws.send(JSON.stringify({event,ticket:id,...fields}))})}
const action=process.argv[2]||'status';
try{
 const status=await call('game.status');
 if(status.game?.id!=='NPUH10126')throw Error('Wrong game');
 if(action==='status'){console.log(JSON.stringify({status,cpu:await call('cpu.status'),version:await call('version')}))}
 else if(action==='press'){for(const button of process.argv[3].split(',')){await call('input.buttons.press',{button,duration:4});await new Promise(r=>setTimeout(r,900));}console.log('pressed '+process.argv[3]);}
 else if(action==='event'){console.log(JSON.stringify(await call(process.argv[3],JSON.parse(process.argv[4]||'{}'))));}
 else if(action==='model-memory'){
  const memory=Buffer.alloc(32*1024*1024);
  for(let start=0;start<memory.length;start+=1024*1024){const r=await call('memory.read',{address:0x08000000+start,size:1024*1024});Buffer.from(r.base64,'base64').copy(memory,start)}
  const found=[];let at=-1;while((at=memory.indexOf('INSM',at+1))!==-1){found.push({address:0x08000000+at,header:memory.subarray(at,at+56).toString('hex')})}
  fs.writeFileSync(meta.path+'/captures/model-ram.bin',memory);fs.writeFileSync(meta.path+'/captures/model-ram.json',JSON.stringify({iso:meta.iso,found},null,2));console.log(JSON.stringify(found));
 }
 else throw Error('Unknown action');
}finally{ws.close()}
