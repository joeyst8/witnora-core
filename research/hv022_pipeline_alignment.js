#!/usr/bin/env node
'use strict';
// HV-022. Run: node research/hv022_pipeline_alignment.js path/to/processed_hl_arr_access_32_arr.btor2
// Uses the verbatim frozen BTOR2 mirror and exact bit-vector semantics, never edits the circuit.
// Sample tests are control checks; the accompanying algebraic proof is in the results document.
const fs = require('fs');
const crypto = require('crypto');
const path = process.argv[2];
if (!path) throw Error('usage: node hv022_pipeline_alignment.js SOURCE.btor2');
const bytes = fs.readFileSync(path);
const sha = crypto.createHash('sha256').update(bytes).digest('hex');
const EXPECTED = 'cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc';
if (sha !== EXPECTED) throw Error('Source SHA mismatch: ' + sha);
const rows = bytes.toString('utf8').split('\n').map(x => x.split(';')[0].trim()).filter(Boolean).map(x => x.split(/\s+/));
const node = new Map(rows.map(r => [+r[0], {op:r[1],p:r.slice(2)}]));
if (rows.length!==406)throw Error('Unexpected node count');
const expected = {
  6:['sort','bitvec','8'], 81:['sort','bitvec','3'], 318:['sort','array','81','6'],
  153:['and','1','112','65'],316:['ite','6','153','315','164'],
  321:['ite','6','197','320','165'],317:['next','6','164','316'],
  322:['next','6','165','321'], 405:['next','318','319','404','mem_V_U.top_mem_V_ram_U.ram'], 406:['bad','48']
};
for(const [k,r] of Object.entries(expected)){
 const x=node.get(+k),p=[x.op,...x.p]; if(r.length!==p.length||r.some((v,i)=>v!==p[i]))
  throw Error('Structural pin mismatch: '+k);
}
const sorts=new Map(rows.filter(r=>r[1]==='sort').map(r=>[+r[0],r[2]==='bitvec'?{kind:'bv',w:+r[3]}:{kind:'array',i:+r[3],e:+r[4]}]));
let seed=0x20261116;function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;}
const mask=w=>(1n<<BigInt(w))-1n;
const selectedReg=[188,181,182,183,184,185,186,187];

function evaluate(index,mode) {
 const RAM=Array.from({length:8},()=>BigInt(rand()&255));
 const val=new Map(), states=new Map(), inputs=new Map();
 for(const r of rows){
  const id=+r[0],op=r[1],p=r.slice(3);
  if(['sort','init','next','output','bad'].includes(op))continue;
  const t=sorts.get(+r[2]),w=t.kind==='bv'?t.w:0,a=k=>val.get(+k);
  let out;
  if(op==='state'||op==='input'){
    out=t.kind==='array'?RAM:(BigInt(rand())&mask(w));
    if(id===14)out=16n; // FSM state 4, legal one-hot
    if(id===112)out=mode==='hold'?0n:1n;
    if(id===60)out=BigInt(index);
    if(id===33)out=0n;  // no interfering pp0 read
    if(id===164||id===165)out=BigInt(rand()&255);
    if(selectedReg[index]===id&&mode!=='hold')
      out=mode==='match'?RAM[index]:(RAM[index]+1n)&255n;
    if(id===310&&index===8&&mode!=='hold')
      out=mode==='match'?RAM[0]:(RAM[0]+1n)&255n;
    (op==='state'?states:inputs).set(id,out);
  } else if(['const','constd','consth'].includes(op))
    out=op==='const'?BigInt('0b'+p[0]):op==='constd'?BigInt(p[0]):BigInt('0x'+p[0]);
  else if(op==='and')out=a(p[0])&a(p[1]);
  else if(op==='or')out=a(p[0])|a(p[1]);
  else if(op==='add')out=(a(p[0])+a(p[1]))&mask(w);
  else if(op==='not')out=mask(w)^a(p[0]);
  else if(op==='eq')out=BigInt(a(p[0])===a(p[1]));
  else if(op==='ite')out=a(p[0])===1n?a(p[1]):a(p[2]);
  else if(op==='uext')out=a(p[0]);
  else if(op==='slice')out=(a(p[0])>>BigInt(+p[2]))&mask(w);
  else if(op==='redor')out=BigInt(a(p[0])!==0n);
  else if(op==='concat'){
    const w2=sorts.get(+node.get(+p[1]).p[0]).w;
    out=(a(p[0])<<BigInt(w2))|a(p[1]);
  }
  else if(op==='read')out=a(p[0])[Number(a(p[1]))];
  else if(op==='write'){
    out=a(p[0]).slice();out[Number(a(p[1]))]=a(p[2]);
  } else throw Error('Unhandled opcode '+op+' node '+id);
  val.set(id,out);
 }
 return {
  en:val.get(153),ce:val.get(197),addr:val.get(194),qnext:val.get(321),
  phinext:val.get(316),oldq:states.get(165),oldphi:states.get(164),
  ramIndex:RAM[index&7],selected:val.get(315),input310:inputs.get(310),
  terminal:val.get(114)
 };
}

const counts={matched:0,mismatched:0,held:0,errors:0},perIndex=[];
let sentinelCounterexample=null;
for(let index=0;index<=8;index++){
 const c={index,matched:0,mismatched:0,held:0};
 for(let i=0;i<64;i++){
  for(const mode of ['match','mismatch','hold']){
   const v=evaluate(index,mode);
   const ok=mode==='hold'
     ? v.en===0n&&v.ce===0n&&v.qnext===v.oldq&&v.phinext===v.oldphi
     : v.en===1n&&v.ce===1n&&v.addr===BigInt(index&7)&&v.qnext===v.ramIndex&&
       (mode==='match'?v.qnext===v.phinext:v.qnext!==v.phinext);
   if(!ok){counts.errors++;throw Error('Assertion failed index='+index+' mode='+mode+' iteration='+i);}
   const k=mode==='match'?'matched':mode==='mismatch'?'mismatched':'held';
   counts[k]++;c[k]++;
   if(index===8&&mode==='mismatch'&&!sentinelCounterexample)
    sentinelCounterexample={counter:8,ramAddress:0,ramRead:Number(v.qnext),freeInput310:Number(v.input310),nextPhi:Number(v.phinext)};
  }
 }
 perIndex.push(c);
}
if(!sentinelCounterexample)throw Error('Negative control never rejected the invalid terminal equality');
console.log(JSON.stringify({
 experiment:'HV-022',mirror_sha256:sha,
 addressed_entries:8, data_width_bits:8,
 tests:counts,perIndex,terminal_unreachable_not_asserted:true,
 terminal_counterexample_is_arbitrary_predecessor:true,
 terminal_counterexample:sentinelCounterexample,
 complete_chip_safety_proved:false, new_algorithm_demonstrated:false,
 proof_scope:'Local conditional next-state identity; NOT a reachable-state invariant or an inductive certificate'
},null,2));
