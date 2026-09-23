import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
const locator=JSON.parse(fs.readFileSync(path.resolve(import.meta.dirname,'../outputs/combined-build-latest.json'),'utf8'));
const root=locator.path;
const launch=JSON.parse(fs.readFileSync(path.join(root,'launch-session.json'),'utf8').replace(/^\uFEFF/,''));
if(launch.port!==49324 || !launch.executable.endsWith('PPSSPPBRS4KTest.exe'))throw Error('Unexpected target');
if(fs.readFileSync(path.join(root,'runtime/installed.txt'),'utf8').trim()!==path.join(root,'memstick'))throw Error('Wrong memstick');
const ws=new WebSocket('ws://127.0.0.1:49324/debugger');
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;setTimeout(()=>reject(Error('connection timeout')),7000).unref()});
let n=0;
function call(event,fields={},broadcast=false){return new Promise((resolve,reject)=>{
 const ticket=String(++n),timer=setTimeout(()=>{ws.removeEventListener('message',listen);reject(Error('timeout '+event))},10000);
 function listen(e){const m=JSON.parse(e.data);if(m.ticket===ticket || broadcast && m.event===event){clearTimeout(timer);ws.removeEventListener('message',listen);m.event==='error'?reject(Error(JSON.stringify(m))):resolve(m)}}
 ws.addEventListener('message',listen);ws.send(JSON.stringify({event,ticket,...fields}));
})}
try {
 const identity=await call('game.status');
 if(identity.game?.id!=='NPUH10126')throw Error('Wrong game '+JSON.stringify(identity));
 const action=process.argv[2]||'status';
 if(['memory-layout','model-memory','disasm','dump-inflater-code'].includes(action)){
  const state=await call('cpu.status');
  if(state.paused&&!state.stepping)throw Error('Core paused/error: memory API can deadlock; collect regs first');
 }
 let result;
 if(action==='status')result={identity,cpu:await call('cpu.status'),version:await call('version')};
 else if(action==='press')result=await call('input.buttons.press',{button:process.argv[3],duration:4});
 else if(action==='capture'){
  const before=await call('cpu.status');
  if(before.stepping || before.paused)throw Error('Already paused; no state takeover');
  try { await call('cpu.stepping',{},true); result=await call('gpu.buffer.screenshot'); }
  finally { const after=await call('cpu.status'); if(after.stepping)await call('cpu.resume',{},true); }
  if(!result.uri?.startsWith('data:image/png'))throw Error('No PNG capture');
  fs.mkdirSync(path.join(root,'captures'),{recursive:true});
  const filename=path.join(root,'captures',(process.argv[3]||'current')+'.png');
  fs.writeFileSync(filename,Buffer.from(result.uri.split(',')[1],'base64'));
  delete result.uri;result.path=filename;
 } else if(action==='memory-layout'){
  const read=async(address,size)=>Buffer.from((await call('memory.read',{address,size})).base64,'base64');
  const main=await read(0x08997fbc,68);
  const arena=(await read(0x08977b00,4)).readUInt32LE();
  const hp=(await read(0x089751b0,4)).readUInt32LE();
  const heap=hp?await read(hp,68):null;
  result={arena:'0x'+arena.toString(16),main:{base:'0x'+main.readUInt32LE(4).toString(16),size:main.readUInt32LE(8)},model_heap:heap?{address:'0x'+hp.toString(16),base:'0x'+heap.readUInt32LE(4).toString(16),size:heap.readUInt32LE(8)}:null};
  fs.writeFileSync(path.join(root,'captures/memory-layout.json'),JSON.stringify(result,null,2));
 } else if(action==='model-memory'){
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'build-manifest.json'),'utf8').replace(/^\uFEFF/,''));
  const memory=Buffer.alloc((manifest.requires_64mb_memory?64:32)*1024*1024);
  for(let start=0;start<memory.length;start+=1024*1024){const r=await call('memory.read',{address:0x08000000+start,size:1024*1024});Buffer.from(r.base64,'base64').copy(memory,start)}
  const found=[];let at=-1;while((at=memory.indexOf('INSM',at+1))!==-1)found.push({address:0x08000000+at,header:memory.subarray(at,at+80).toString('hex')});
  fs.mkdirSync(path.join(root,'captures'),{recursive:true});
  const captureName='model-ram-'+launch.pid+'-'+Date.now();
  fs.writeFileSync(path.join(root,'captures',captureName+'.bin'),memory);
  fs.writeFileSync(path.join(root,'captures/current-model-ram.bin'),memory);
  const candidate=zlib.gunzipSync(fs.readFileSync('P:/AI/Codex/projects/black-rock-shooter-hd-retexture/workspace/model_port/candidate_v1/FCHR_P_BRS02_pgr_candidate.BIN'));
  const insm=candidate.subarray(candidate.readUInt32LE(8)+16,candidate.readUInt32LE(12));
  const candidateMatches=[];at=-1;
  while((at=memory.indexOf(insm.subarray(0,56),at+1))!==-1)candidateMatches.push({address:'0x'+(0x08000000+at).toString(16),full_exact:memory.subarray(at,at+insm.length).equals(insm)});
  const records=[];at=-1;
  while((at=memory.indexOf('FCHR_P_BRS02.BIN',at+1))!==-1 && at+60<=memory.length)records.push({address:'0x'+(0x08000000+at).toString(16),sha1:memory.subarray(at+32,at+52).toString('hex'),size:memory.readUInt32LE(at+52),offset:memory.readUInt32LE(at+56)});
  const proof={pid:launch.pid,iso:launch.iso,ram:path.join(root,'captures',captureName+'.bin'),found,candidateMatches,records};
  fs.writeFileSync(path.join(root,'captures',captureName+'.json'),JSON.stringify(proof,null,2));
  fs.writeFileSync(path.join(root,'captures/current-model-ram.json'),JSON.stringify(proof,null,2));
  result={candidateMatches,records,insm_count:found.length,proof:path.join(root,'captures',captureName+'.json')};
 } else if(action==='disasm'){
  const raw=await call('memory.disasm',{address:Number(process.argv[3]),count:Number(process.argv[4]||64),displaySymbols:true});
  fs.mkdirSync(path.join(root,'captures'),{recursive:true});
  fs.writeFileSync(path.join(root,'captures','disasm-'+process.argv[3]+'.json'),JSON.stringify(raw));
  result=raw.lines.map(x=>x.address.toString(16)+' '+x.name+' '+x.params);
 }
 else if(action==='dump-inflater-code'){
  const raw=await call('memory.disasm',{address:0x08959000,count:9216,displaySymbols:false});
  const dest=path.join(root,'captures/inflater-instructions.json');
  fs.writeFileSync(dest,JSON.stringify(raw));
  result={path:dest,lines:raw.lines.length,range:raw.range};
 }
 else if(action==='regs'){
  result=await call('cpu.getAllRegs');
  fs.writeFileSync(path.join(root,'captures','regs-'+launch.pid+'.json'),JSON.stringify(result,null,2));
 }
 else if(action==='eval')result=await call('cpu.evaluate',{expression:process.argv[3]});
 else if(action==='threads')result=await call('hle.thread.list');
 else if(action==='trace-load' || action==='trace-reselect'){
  const address=0x08960b18;
  const before=await call('cpu.status');
  if(before.stepping || before.paused)throw Error('Already paused');
  const existing=await call('cpu.breakpoint.list');
  if((existing.breakpoints||[]).some(x=>x.address===address))throw Error('Existing breakpoint');
  const source=fs.readFileSync('P:/AI/Codex/projects/black-rock-shooter-hd-retexture/workspace/model_port/candidate_v1/FCHR_P_BRS02_pgr_candidate.BIN');
  let caught=false;result={attempts:[]};
  try {
   await call('cpu.breakpoint.add',{address,enabled:true});
   console.log('Armed model loader trace.');
   const auto=action==='trace-reselect';let downSent=false;const downAt=Date.now()+1700;
   if(auto)await call('input.buttons.press',{button:'up',duration:4});
   const until=Date.now()+(auto?12000:90000);
   while(Date.now()<until){
    const state=await call('cpu.status');
    if(state.stepping && state.pc===address){
     const regs=await call('cpu.getAllRegs');
     const values=regs.categories[0].uintValues;
     const a0=values[4],a1=values[5],a2=values[6],a3=values[7];
     const prefix=Buffer.from((await call('memory.read',{address:a2,size:32})).base64,'base64');
     const match=prefix.equals(source.subarray(0,32));
     const bytes=match?Buffer.from((await call('memory.read',{address:a2,size:source.length})).base64,'base64'):prefix;
     result.attempts.push({a0,a1,a2,a3,first32:bytes.subarray(0,32).toString('hex'),candidate_prefix_match:match,full_compressed_match:bytes.equals(source)});
     if(match){
      fs.mkdirSync(path.join(root,'captures'),{recursive:true});
      fs.writeFileSync(path.join(root,'captures/booster-loader-regs.json'),JSON.stringify(regs));
      fs.writeFileSync(path.join(root,'captures/booster-loader-input.bin'),bytes);
      const manifest=JSON.parse(fs.readFileSync(path.join(root,'build-manifest.json'),'utf8').replace(/^\uFEFF/,''));
      const memory=Buffer.alloc((manifest.requires_64mb_memory?64:32)*1024*1024);
      for(let offset=0;offset<memory.length;offset+=1024*1024){const m=await call('memory.read',{address:0x08000000+offset,size:1024*1024});Buffer.from(m.base64,'base64').copy(memory,offset);}
      fs.writeFileSync(path.join(root,'captures/booster-loader-before-ram.bin'),memory);
      caught=true;break;
     }
     await call('cpu.resume',{},true);
    }
    if(auto && !downSent && !state.stepping && Date.now()>=downAt){await call('input.buttons.press',{button:'down',duration:4});downSent=true;}
    await new Promise(r=>setTimeout(r,150));
   }
  } finally {
   await call('cpu.breakpoint.remove',{address});
   const end=await call('cpu.status');
   if(end.stepping && end.pc===address)await call('cpu.resume',{},true);
  }
  result.caught=caught;
  fs.writeFileSync(path.join(root,'captures/booster-loader-trace.json'),JSON.stringify(result,null,2));
 }
 else throw Error('Unexpected action');
 if(action==='status')fs.writeFileSync(path.join(root,'runtime-status.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
}finally{ws.close()}
