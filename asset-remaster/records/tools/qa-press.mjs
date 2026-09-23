import {spawnSync} from 'node:child_process';
const [session,button,label]=process.argv.slice(2);
if(!['start','cross','circle','up','down','left','right'].includes(button))throw new Error('Unknown button');
const out=spawnSync(process.execPath,['P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts/tools/runtime-qa.mjs',session,'input.buttons.press',JSON.stringify({button,duration:2}),label],{stdio:'inherit'});
process.exit(out.status??1);
