// PPSSPP v1.20.4 GPU/Debugger/RecordFormat.h, versions 5/6.
import fs from 'node:fs';
import path from 'node:path';
import {zstdDecompressSync} from 'node:zlib';
import {createHash} from 'node:crypto';
const input=path.resolve(process.argv[2]),dest=path.resolve(process.argv[3]);
const b=fs.readFileSync(input);if(b.subarray(0,8).toString()!=='PPSSPPGE')throw new Error('Not a GE dump');
const version=b.readUInt32LE(8);if(![5,6].includes(version))throw new Error('Unsupported GE format');
const game=b.subarray(12,21).toString().replace(/\0/g,'');if(game!=='NPUH10126')throw new Error('Foreign game');
const count=b.readUInt32LE(24),size=b.readUInt32LE(28);let p=32;
function block(){const n=b.readUInt32LE(p);p+=4;const d=zstdDecompressSync(b.subarray(p,p+n));p+=n;return d;}
const commands=block(),payload=block();if(commands.length!==count*9||payload.length!==size||p!==b.length)throw new Error('Invalid lengths');
const records=[];for(let i=0;i<count;i++){const q=i*9;const type=commands[q],sz=commands.readUInt32LE(q+1),ptr=commands.readUInt32LE(q+5);if(ptr+sz>payload.length)throw new Error('Out of range');records.push({type,sz,ptr});}
fs.mkdirSync(dest,{recursive:true});fs.writeFileSync(path.join(dest,'pushbuf.bin'),payload);
const meta={source:input,source_sha256:createHash('sha256').update(b).digest('hex'),version,game,count,size,commands:records};fs.writeFileSync(path.join(dest,'commands.json'),JSON.stringify(meta,null,2));
console.log(JSON.stringify({version,game,count,size,types:records.reduce((a,c)=>(a[c.type]=(a[c.type]||0)+1,a),{})}));
