#!/usr/bin/env node
'use strict';
// HV-022B. Usage: node research/hv022_terminal_gating.js SOURCE.btor2
// Exhaustive finite-state control-subcone audit, NOT unbounded chip-safety proof.
const fs=require('fs'), crypto=require('crypto');
if(!process.argv[2])throw Error('usage: node hv022_terminal_gating.js SOURCE.btor2');
const src=fs.readFileSync(process.argv[2]);
const sha=crypto.createHash('sha256').update(src).digest('hex');
const PIN='cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc';
if(sha!==PIN)throw Error('Mirror SHA mismatch: '+sha);
const rows=src.toString('utf8').split('\n').map(l=>l.split(';')[0].trim()).filter(Boolean).map(l=>l.split(/\s+/));
const nodes=new Map(rows.map(r=>[+r[0],{op:r[1],p:r.slice(2)}]));
const sorts=new Map(rows.filter(r=>r[1]==='sort').map(r=>[+r[0],r[2]==='bitvec'?{w:+r[3]}:{array:true}]));
const pins={114:['eq','1','60','85'],308:['ite','1','3','9','307'],
  309:['next','1','159','308'],328:['ite','1','65','114','176'],
  329:['next','1','176','328'],262:['and','1','260','261']};
for(const [key,want] of Object.entries(pins)){
 const r=nodes.get(+key),got=[r.op,...r.p];
 if(got.length!==want.length||want.some((x,i)=>got[i]!==x))
  throw Error('Source structural pin mismatch: '+key);
}
function evalNode(id,env,cache=new Map()){
 if(cache.has(id))return cache.get(id);
 const r=nodes.get(+id),p=r.p,width=sorts.get(+p[0])?.w;
 const a=n=>evalNode(+n,env,cache);
 let x;
 if(r.op==='state'||r.op==='input')x=env[id]??0n;
 else if(r.op==='const')x=BigInt('0b'+p[1]);
 else if(r.op==='and')x=a(p[1])&a(p[2]);
 else if(r.op==='or')x=a(p[1])|a(p[2]);
 else if(r.op==='not')x=((1n<<BigInt(width))-1n)^a(p[1]);
 else if(r.op==='eq')x=BigInt(a(p[1])===a(p[2]));
 else if(r.op==='ite')x=a(p[1])===1n?a(p[2]):a(p[3]);
 else if(r.op==='uext')x=a(p[1]);
 else if(r.op==='slice')x=(a(p[1])>>BigInt(+p[3]))&((1n<<BigInt(width))-1n);
 else if(r.op==='redor')x=BigInt(a(p[1])!==0n);
 else throw Error('Unexpected operator in audited control cone: '+r.op+' node='+id);
 cache.set(id,x);return x;
}
const stats={cases:0,B1_pass:0,B2_pass:0,comparison_implication_pass:0,
  comparison_enabled_cases:0,incorrect_mutant_rejected_cases:0};
for(let c=0;c<16;c++)for(let reset=0;reset<2;reset++)for(let e0=0;e0<2;e0++)
for(let oldCmp=0;oldCmp<2;oldCmp++)for(let prevFSM=0;prevFSM<2;prevFSM++)for(let nextFSM=0;nextFSM<2;nextFSM++){
 const env={3:BigInt(reset),60:BigInt(c),112:BigInt(e0),176:BigInt(oldCmp),14:prevFSM?16n:1n};
 const e1=evalNode(308,env),term=evalNode(328,env);
 const predicted=BigInt(!reset&&e0&&c!==8),predictedTerm=BigInt(prevFSM?c===8:oldCmp);
 const nextEnv={14:nextFSM?16n:1n,159:e1,176:term};
 const comparison=evalNode(262,nextEnv);
 stats.cases++;
 if(e1!==predicted)throw Error('B1 failed c='+c);
 stats.B1_pass++;
 if(term!==predictedTerm)throw Error('B2 failed c='+c);
 stats.B2_pass++;
 if(comparison===1n)stats.comparison_enabled_cases++;
 if(comparison===1n&&(c===8||reset!==0||e0!==1))throw Error('Invalid comparison predecessor c='+c);
 stats.comparison_implication_pass++;
 if(BigInt(!reset&&e0)!==e1)stats.incorrect_mutant_rejected_cases++;
}
if(stats.incorrect_mutant_rejected_cases===0)throw Error('Negative control failed');
console.log(JSON.stringify({
 experiment:'HV-022B',source_sha256:sha,
 ...stats,complete_chip_safety_proved:false,novel_algorithm_demonstrated:false,
 proof_scope:'Exhaustive local two-register control implication, for arbitrary predecessor values, not a full inductive safety certificate'
},null,2));
