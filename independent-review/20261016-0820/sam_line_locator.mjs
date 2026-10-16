import assert from 'node:assert/strict';
import test from 'node:test';
import {mkdtemp,mkdir,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
const {searchWorkBuddyKnowledge}=await import(pathToFileURL(join(process.env.REVIEW_SAM_ROOT,'dist/workbuddy.js')));
async function fixture(line){
 const root=await mkdtemp(join(tmpdir(),'qa-locator-'));const raw=join(root,'raw');await mkdir(raw);
 await writeFile(join(raw,'valid.txt'),'ACTUAL-PUBLIC-NEEDLE\n');
 const script=join(root,'backend.mjs');const response={count:1,raw_blocks:1,hits:[{path:'valid.txt',line,score:-1,branch:'default',lines:[[1,'ACTUAL-PUBLIC-NEEDLE']]}]};
 await writeFile(script,'console.log('+JSON.stringify(JSON.stringify(response))+');');
 const entry=(id,path)=>({id,path,kind:'reference',authority:'supporting',content_mode:'readonly',navigation:'test',notes:''});
 return {registry:{schema_version:1,updated:'2026-10-16',approved_roots:[root],sources:[entry('workbuddy-python-runtime',process.execPath),entry('workbuddy-search-entry',script),entry('workbuddy-raw-corpus',raw)]},dataDir:join(root,'data')};
}
test('valid FTS locator and byte-checked excerpt remain usable',async()=>{
 const r=await searchWorkBuddyKnowledge(await fixture(1),{query:'PUBLIC-NEEDLE',verifyCounts:false});
 assert.equal(r.returned_hits,1);assert.equal(r.hits[0].line,1);
});
test('backend cannot attach nonexistent line999 to verified line1 text',async()=>{
 const r=await searchWorkBuddyKnowledge(await fixture(999),{query:'PUBLIC-NEEDLE',verifyCounts:false});
 assert.ok(!r.hits.some(h=>h.line===999),'untrusted line anchor999 is returned for a one-line canonical file');
});
