import fs from 'node:fs';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
const activePath=path.join(root,'workspace/runtime/active_session.json');
const active=fs.existsSync(activePath)?JSON.parse(fs.readFileSync(activePath,'utf8').replace(/^\uFEFF/,'')):{path:path.join(root,'workspace/sessions/S002-v101-xxh64-gles')};
const session=path.resolve(active.path);
if(!session.startsWith(path.join(root,'workspace/sessions')+path.sep))throw new Error('Session outside project');
const [action = 'status', arg = '', delay = '1200'] = process.argv.slice(2);
if((action==='capture'||action==='snapshot')&&!/^[a-zA-Z0-9_-]+$/.test(arg))throw new Error('Use a safe snapshot label');
const ws = new WebSocket('ws://127.0.0.1:49213/debugger');
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;setTimeout(()=>reject(new Error('connect timeout')),8000).unref();});
let ticket=0;
function call(event, fields={}) {if(event==='cpu.stepping'||event==='cpu.resume'){ws.send(JSON.stringify({event}));return new Promise(r=>setTimeout(r,150));}return new Promise((resolve,reject)=>{
 const id=String(++ticket), timer=setTimeout(()=>{ws.removeEventListener('message',listener);reject(new Error('timeout '+event));},15000);
 const listener=e=>{let r=JSON.parse(e.data);if(r.ticket===id){clearTimeout(timer);ws.removeEventListener('message',listener);r.event==='error'?reject(new Error(JSON.stringify(r))):resolve(r)}};
 ws.addEventListener('message',listener);ws.send(JSON.stringify({event,ticket:id,...fields}));
});}
const log=(row)=>fs.appendFileSync(path.join(session,'actions.jsonl'),JSON.stringify({time:new Date().toISOString(),...row})+'\n');
try {
 const gameIdentity=await call('game.status');
 if(gameIdentity.game?.id!=='NPUH10126')throw new Error('Unexpected game on project debugger port');
 if(action==='snapshot'){
  const files=fs.readdirSync(path.join(session,'memstick/PSP/TEXTURES/NPUH10126/new')).filter(x=>x.endsWith('.png'));
  const r={time:new Date().toISOString(),files,scene_verified:false};fs.writeFileSync(path.join(session,'captures',arg+'.textures.json'),JSON.stringify(r,null,2));log({action,label:arg,dump_count:files.length});console.log(JSON.stringify({dump_count:files.length}));
 }
 else if(action==='status'){const r=await call('game.status');const v=await call('version');log({action,r,v});console.log(JSON.stringify({r,v}));}
 else if(action==='capture'){
  await call('cpu.stepping'); const status=await call('cpu.status'); if(!status.stepping) throw new Error('CPU did not pause: '+JSON.stringify(status));
  let capture_event='gpu.buffer.screenshot'; let r; try{r=await call(capture_event);}catch(e){if(!e.message.includes('Could not download output'))throw e;capture_event='gpu.buffer.renderColor';r=await call(capture_event);}
  const png=Buffer.from(r.uri.split(',')[1],'base64');
  const dest=path.join(session,'captures',arg+'.png');fs.writeFileSync(dest,png);
  const files=fs.readdirSync(path.join(session,'memstick/PSP/TEXTURES/NPUH10126/new')).filter(x=>x.endsWith('.png'));
  fs.writeFileSync(path.join(session,'captures',arg+'.textures.json'),JSON.stringify({time:new Date().toISOString(),files},null,2));
  log({action,capture_event,label:arg,width:r.width,height:r.height,dump_count:files.length});console.log(JSON.stringify({path:dest,width:r.width,height:r.height,dump_count:files.length}));
 }
 else if(action==='press') {await call('cpu.resume');for(const button of arg.split(',')){await call('input.buttons.press',{button,duration:3});await new Promise(r=>setTimeout(r,Number(delay)));}log({action,buttons:arg,delay_ms:Number(delay)});console.log('pressed');}
 else if(action==='resume'){await call('cpu.resume');log({action});console.log('resumed');}
 else if(action==='reset'){await call('game.reset');log({action});console.log('reset');}
 else throw new Error('Unknown action');
} catch(e) {
 log({action,label:arg,error:e.message});
 if(action==='capture'){
  const files=fs.readdirSync(path.join(session,'memstick/PSP/TEXTURES/NPUH10126/new')).filter(x=>x.endsWith('.png'));
  fs.writeFileSync(path.join(session,'captures',arg+'.failed.json'),JSON.stringify({time:new Date().toISOString(),files,capture_error:e.message,scene_verified:false},null,2));
 }
 throw e;
} finally {ws.close();}



