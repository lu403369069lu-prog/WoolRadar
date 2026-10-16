import {validateTeacherEvaluations} from '../../_work/sam-delivery-4b-qa/SAM/snapshot/dist/eval-contract.js';
import {inspectHoldoutIdentities} from '../../_work/qa2-yinqieji-9/SAM/independent-review/20261016-0904-audit-coverage/holdout_identity_check.mjs';
const rows=Array.from({length:65},(_,i)=>({qid:`SYNTHETIC-${i}`,answer_status:i<61?'answered':'insufficient_evidence'}));
const duplicate=structuredClone(rows);duplicate[4].qid=duplicate[0].qid;
const accepted=validateTeacherEvaluations(duplicate);
const foldsPass=[0,1,2,3].every(f=>{const training=new Set(accepted.filter((_,i)=>i%4!==f).map(r=>r.qid));return accepted.filter((_,i)=>i%4===f).every(r=>!training.has(r.qid));});
let reviewRejects=false;try{inspectHoldoutIdentities(duplicate)}catch{reviewRejects=true}
const ambiguous=structuredClone(rows);ambiguous[64].answer_status='ambiguous';
const result={source_sha:'4b68619686350cbb1fe2f64753a72a654558e6ec',review_sha:'a033f86387855c0f206f67980c3c82f67ba895e5',synthetic_only:true,formal_validator_accepts_same_fold_duplicate:accepted.length===65,existing_four_fold_overlap_assertions_pass:foldsPass,independent_review_rejects_duplicate:reviewRejects,formal_positive_denominator:ambiguous.filter(r=>r.answer_status==='answered').length,formal_loop_positive_or_ambiguous:ambiguous.filter(r=>!['insufficient_evidence','stale_source'].includes(r.answer_status)).length,full_formal_evaluator_executed:false,real_61_questions_read:false};
console.log(JSON.stringify(result,null,2));
if(!result.formal_validator_accepts_same_fold_duplicate||!foldsPass||!reviewRejects)process.exitCode=1;
