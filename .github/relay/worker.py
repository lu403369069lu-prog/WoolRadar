#!/usr/bin/env python3
"""Bounded read-only tests + replay-safe durable checkpoints. Never auto-accept."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from checkpoint_store import save, persist_lock, recover_history, verify_replay

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def queue_digest(queue):
    """Cross-platform canonical hash; Git checkout CRLF/LF must not change identity."""
    canonical = json.dumps(queue, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_sha(path):
    s = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", s):
        raise ValueError("invalid commit SHA")
    return s

def enforce_source_pin(queue, actual):
    ref = queue.get('source_ref')
    if isinstance(ref, str) and re.fullmatch(r'[a-f0-9]{40}', ref) and actual != ref:
        raise ValueError('pinned source SHA mismatch')


def safe(argv):
    if not isinstance(argv, list) or len(argv) < 3 or not all(isinstance(a, str) for a in argv):
        return False
    if any(len(a) > 230 or re.search(r"[\x00-\x1f;$|&<>\x60]", a) for a in argv):
        return False
    if argv[:5] == ["python", "-m", "unittest", "discover", "-s"]:
        # Pin reviewed (discovery root, filename pattern) pairs; no arbitrary -s.
        allowed = {
            ("independent-quality/public-corpus-blind-dedup-20261016", "test_*.py"),
            ("tests", "test_apply_evidence_transaction.py"),
            ("tests", "test_developer_grant_negations.py"),
            ("tests", "test_developer_grant_project_scope.py"),
            ("tests", "test_notifications.py"),
            ("tests", "test_official_trace_stale_event.py"),
            ("tests", "test_official_trace.py"),
            ("tests", "test_public_corpus_dns_label_boundary_20261018.py"),
            ("tests", "test_public_corpus_identity.py"),
            ("tests", "test_public_corpus_timestamp.py"),
            ("tests", "test_public_corpus*.py"),
            ("tests", "test_public_sample*.py"),
            ("tests", "test_reindex_notification_collision.py"),
            ("tests", "test_reindex_snapshot.py"),
            ("tests", "test_reindex_upsert_serialization.py"),
        }
        return len(argv) == 8 and argv[6] == "-p" and (argv[5], argv[7]) in allowed
    if argv[:4] == ["node", "--import", "tsx", "--test"]:
        return len(argv) >= 5 and all(a.startswith("test/") and a.endswith(".test.ts") and ".." not in a for a in argv[4:])
    if argv[:2] == ["node", "--test"]:
        # WoolRadar historical families contain no approved Node fixtures.
        # Never allow arbitrary relative .test.mjs from a future queue edit.
        return False
    return False

def choose_recheck(state, families, regular_ids):
    """Prefer oldest independently failed subset, at most once per two revisions."""
    candidates = []
    for item in families:
        family_id = item["id"]
        prev = state.get("families", {}).get(family_id, {})
        if (family_id in regular_ids or not item["checks"]
                or item["disposition"] == "EXTERNAL_OR_POLICY_GATED"
                or prev.get("status") != "FORMAL_CHECK_FAILED_OR_BLOCKED"):
            continue
        last = prev.get("last_recheck_revision", -1000)
        if not isinstance(last, int) or state["revision"] - last < 2:
            continue
        candidates.append((last, family_id, item))
    return min(candidates)[2] if candidates else None


def parse_test_summary(output, exit_code):
    """An all-skipped or TODO-only test run is NOT formal evidence."""
    node_totals = re.findall(r"(?m)^# tests (\d+)\s*$", output)
    python_totals = re.findall(r"(?m)^Ran (\d+) tests?", output)
    if node_totals:
        total = int(node_totals[-1])
        def node_count(key):
            matches = re.findall(r"(?m)^# " + key + r" (\d+)\s*$", output)
            return int(matches[-1]) if matches else None
        passed = node_count("pass")
        failed = node_count("fail")
        skipped = node_count("skipped")
        todo = node_count("todo")
        cancelled = node_count("cancelled")
        # Node 22 reports each category. Missing/truncated summaries fail closed.
        complete = all(type(x) is int for x in (passed, failed, skipped, todo, cancelled))
        ok = (exit_code == 0 and total > 0 and complete and passed == total
              and failed == 0 and skipped == 0 and todo == 0 and cancelled == 0)
    elif python_totals:
        total = int(python_totals[-1])
        skipped_matches = re.findall(r"\bskipped=(\d+)\b", output)
        skipped = int(skipped_matches[-1]) if skipped_matches else 0
        # unittest can exit 0 for @expectedFailure, whose terminal summary
        # is "OK (expected failures=1)". A test run without any genuine OK
        # marker can also exit 0. Neither is accepted as formal evidence.
        # Ambiguous multiple summaries fail closed instead of selecting one.
        ok_markers = [
            line.strip() for line in output.splitlines()
            if re.fullmatch(r"OK(?: [(].*[)])?", line.strip())
        ]
        complete = (
            len(python_totals) == 1 and len(ok_markers) == 1
            and ok_markers[0] in ("OK", "OK (skipped=0)")
        )
        ok = exit_code == 0 and total > 0 and skipped == 0 and complete
        passed = total if ok else None
        failed = None
        todo = cancelled = 0
    else:
        total = passed = failed = skipped = todo = cancelled = None
        ok = False
    return {"status": "PASS" if ok else "FAIL", "exit_code": exit_code,
            "total": total, "passed": passed, "failed": failed,
            "skipped": skipped, "todo": todo, "cancelled": cancelled}


def test(argv, cwd, src):
    paths = [argv[5]] if argv[:5] == ["python", "-m", "unittest", "discover", "-s"] else [a for a in argv if a.endswith((".test.ts", ".test.mjs"))]
    if any(not (cwd / a).resolve().is_relative_to(src) for a in paths):
        raise ValueError("test path escapes candidate")
    cmd = [sys.executable] + argv[1:] if argv[0] == "python" else argv
    env = dict(os.environ)
    for k in ("GITHUB_TOKEN", "GH_TOKEN", "COPILOT_GITHUB_TOKEN", "OPENAI_API_KEY"):
        env.pop(k, None)
  6×m¢G§²ÚîÆ­yÖÖ–Æ–W5²‡5²&7W'6÷"%Ò²’’RÆVâ†fÖ–Æ–W2•Òf÷"’–â&ævR†â•ĞĞ¢&–÷&—G’Ò6†ö÷6U÷&V6†V6²‡2ÂfÖ–Æ–W2Â·…²&–B%Òf÷"‚–â&VwVÆ'Ò’–bâÂ2VÇ6RæöæPĞ¢&–÷&—G•ö–BÒ&–÷&—G•²&–B%Ò–b&–÷&—G’VÇ6RæöæPĞ¢–b&V6V—BævWB‚'&–÷&—G•÷&V6†V6²"’Ò&–÷&—G•ö–C Ğ¢&—6RfÇVTW'&÷"‚&–çfÆ–Bf–ÆVBÖfÖ–Ç’&–÷&—G’"Ğ¢W‡V7FVBÒ…·&–÷&—G•Ò–b&–÷&—G’VÇ6RµÒ’²&VwVÆ Ğ¢–bÆVâ†W‡V7FVB’ÒÆVâ‡&V6V—E²'&W7VÇG2%Ò“ Ğ¢&—6RfÇVTW'&÷"‚'&–÷&—G’&W7VÇBÆVæwF‚Ö—6ÖF6‚"Ğ¢–b&V6V—BævWB‚&æW‡Eö7W'6÷""’Ò‡5²&7W'6÷"%Ò²â’RÆVâ†fÖ–Æ–W2“ Ğ¢&—6RfÇVTW'&÷"‚&–æ6÷'&V7BæW‡B7W'6÷""Ğ¢f÷"&W7VÇBÂVçG'’–â¦—‡&V6V—E²'&W7VÇG2%ÒÂW‡V7FVB“ Ğ¢–b&W7VÇBævWB‚&–B"’ÒVçG'•²&–B%Ò÷"&W7VÇBævWB‚&vöÂ"’ÒVçG'•²&vöÂ%Ó Ğ¢&—6RfÇVTW'&÷"‚'&V6V—BF6²”Bö÷&FW"Ö—6ÖF6‚"Ğ¢6öÖÖæG2ÒVçG'•²&6†V6·2%ĞĞ¢6†V6·2Ò&W7VÇBævWB‚&6†V6·2"Ğ¢–bæ÷B—6–ç7Fæ6R†6†V6·2ÂÆ—7B“ Ğ¢&—6RfÇVTW'&÷"‚&Ö—76–ær6†V6²Wf–FVæ6R"Ğ¢–bVçG'•²&F—7÷6—F–öâ%ÒÓÒ$U…DU$äÅôõ%õôÄ”5•ôtDTB# Ğ¢W‡V7FVE÷7FGW2Ò$U…DU$äÅôtDUôäõEôU„T5UDTB Ğ¢–b6†V6·3 Ğ¢&—6RfÇVTW'&÷"‚&W‡FW&æÂÖvFRF6²W†V7WFVB"Ğ¢VÆ–bæ÷B6öÖÖæG3 Ğ¢W‡V7FVE÷7FGW2Ò$äõôdõ$ÔÅôÔ”äuôäõEôU„T5UDTB Ğ¢–b6†V6·3 Ğ¢&—6RfÇVTW'&÷"‚'VæÖVBF6²W†V7WFVB"Ğ¢VÇ6S Ğ¢–b·‚ævWB‚&&wb"’f÷"‚–â6†V6·5ÒÒ6öÖÖæG3 Ğ¢&—6RfÇVTW'&÷"‚'FW7BÖ–ærÖ—6ÖF6‚"Ğ¢ÆÅ÷72ÒÆÂ‡‚ævWB‚'7FGW2"’ÓÒ%52"æBG—R‡‚ævWB‚&W†—Eö6öFR"’’—2–çBæB…²&W†—Eö6öFR%ÒÓÒ Ğ¢æBG—R‡‚ævWB‚'F÷FÂ"’’—2–çBæB…²'F÷FÂ%Òâ Ğ¢æBG—R‡‚ævWB‚'76VB"’’—2–çBæB…²'76VB%ÒÓÒ…²'F÷FÂ%ĞĞ¢æB&f–ÆVB"–â‚æB‡…²&f–ÆVB%Ò—2æöæR÷ Ğ¢G—R‡…²&f–ÆVB%Ò’—2–çBæB…²&f–ÆVB%ÒÓÒĞ¢æBÆÂ‡G—R‡‚ævWB†f–VÆB’’—2–çBæB…¶f–VÆEÒÓÒ Ğ¢f÷"f–VÆB–â‚'6¶—VB"Â'FöFò"Â&6æ6VÆÆVB"’Ğ¢f÷"‚–â6†V6·2Ğ¢W‡V7FVE÷7FGW2Ò‚$dõ$ÔÅõ5T%4UEõ55ôäD•dUõTäD”är"–bÆÅ÷70Ğ¢VÇ6R$dõ$ÔÅô4„T4µôd”ÄTEôõ%ô$Äô4´TB"Ğ¢–b&W7VÇBævWB‚'7FGW2"’ÒW‡V7FVE÷7FGW3 Ğ¢&—6RfÇVTW'&÷"‚&–æ6÷'&V7BF6²F—7÷6—F–öâ"Ğ¢–bç’‡‚ævWB‚'7G&–7FÇ•ö6ö×ÆWFR"’—2æ÷BfÇ6R÷"‚ævWB‚&'W6–æW75ö66WFVB"’—2æ÷BfÇ6Rf÷"‚–â&V6V—E²'&W7VÇG2%Ò“ Ğ¢&—6RfÇVTW'&÷"‚&æWfW"WFòÖ66WBfÖ–Ç’"Ğ¢2GF6‚F†R–æFWVæFVçBv†öÆR×6÷W&6R&Vw&W76–öâWf–FVæ6RFòF†RGW&&ÆPĞ¢2†—7F÷'’âF†—2—2äõB'W6–æW72öæF—fR66WFæ6RvFRàĞ¢–çFVw&F–öâÒÆöB…F‚†ç&V6V—B’çv—F…öæÖR‚&–çFVw&F–öâæ§6öâ"’Ğ¢W‡V7FVEö–çFVw&F–öâÒ…·7—2æW†V7WF&ÆRÂ"ÖÒ"Â'Væ—GFW7B"Â&F—66÷fW""Â"×2"Â'FW7G2"Â"×"Â'FW7Eò¢ç’%ĞĞ¢–bç&WòÓÒ%vööÅ&F""VÇ6R²&çÒ"Â'FW7B%ÒĞ¢2F†R'VææW"w2'6öÇWFR—F†öâW†V7WF&ÆRf&–W2'’†÷7BâfÆ–FFR&wb7G'V7GW&RàĞ¢–çFVw&F–öåö6öÖÖæBÒ–çFVw&F–öâævWB‚&6öÖÖæB"Ğ¢fÆ–Eö6ÖBÒ†—6–ç7Fæ6R†–çFVw&F–öåö6öÖÖæBÂÆ—7B’æ@Ğ¢‚†ç&WòÓÒ%vööÅ&F""æBÆVâ†–çFVw&F–öåö6öÖÖæB’ÓÒ€Ğ¢æB–çFVw&F–öåö6öÖÖæE³¥ÒÓÒW‡V7FVEö–çFVw&F–öå³¥ÒĞ¢÷"†ç&WòÓÒ%––å–T¦’"æB–çFVw&F–öåö6öÖÖæBÓÒW‡V7FVEö–çFVw&F–öâ’’Ğ¢–b†–çFVw&F–öâævWB‚'66†VÖ÷fW'6–öâ"’Ò÷"–çFVw&F–öâævWB‚'&Wò"’Òç&WğĞ¢÷"æ÷BfÆ–Eö6ÖB÷"–çFVw&F–öâævWB‚'fW&–f–VEö'W6–æW75ö6ö×ÆWFR"’—2æ÷BfÇ6PĞ¢÷"–çFVw&F–öâævWB‚'7FGW2"’æ÷B–â‚%52"Â$d”Â"Â$$Äô4´TB"Ğ¢÷"G—R†–çFVw&F–öâævWB‚'6÷W&6Uö6öÖÖ—B"’’—2æ÷B7G Ğ¢÷"æ÷B&RægVÆÆÖF6‚‡"%¶ÖcÓ•×³CÒ"Â–çFVw&F–öå²'6÷W&6Uö6öÖÖ—B%ÒĞ¢÷"–çFVw&F–öå²'6÷W&6Uö6öÖÖ—B%ÒÒ&V6V—E²'6÷W&6Uö6öÖÖ—B%ĞĞ¢÷"G—R†–çFVw&F–öâævWB‚''Våö¶W’"’’—2æ÷B7G Ğ¢÷"æ÷B&RægVÆÆÖF6‚‡"%ÆB²õÆB²"Â–çFVw&F–öå²''Våö¶W’%ÒĞ¢÷"–çFVw&F–öå²''Våö¶W’%ÒÒ¶W’“ Ğ¢&—6RfÇVTW'&÷"‚&–çfÆ–B–æFWVæFVçB–çFVw&F–öâ&W÷'B"Ğ¢–b–çFVw&F–öå²'7FGW2%ÒÓÒ%52"æB€Ğ¢G—R†–çFVw&F–öâævWB‚&W†—Eö6öFR"’’—2æ÷B–çB÷"–çFVw&F–öå²&W†—Eö6öFR%ÒÒ÷ Ğ¢G—R†–çFVw&F–öâævWB‚'F÷FÂ"’’—2æ÷B–çB÷"–çFVw&F–öå²'F÷FÂ%ÒÃÒ÷ Ğ¢G—R†–çFVw&F–öâævWB‚'76VB"’’—2æ÷B–çB÷ Ğ¢–çFVw&F–öå²'76VB%ÒÒ–çFVw&F–öå²'F÷FÂ%Ò÷ Ğ¢&f–ÆVB"æ÷B–â–çFVw&F–öâ÷ Ğ¢æ÷B†–çFVw&F–öå²&f–ÆVB%Ò—2æöæR÷ Ğ¢G—R†–çFVw&F–öå²&f–ÆVB%Ò’—2–çBæB–çFVw&F–öå²&f–ÆVB%ÒÓÒ’÷ Ğ¢ç’‡G—R†–çFVw&F–öâævWB†¶W’’’—2æ÷B–çB÷"–çFVw&F–öå¶¶W•ÒÒ Ğ¢f÷"¶W’–â‚'6¶—VB"Â'FöFò"Â&6æ6VÆÆVB"’’“ Ğ¢&—6RfÇVTW'&÷"‚&f÷&vVB–çFVw&F–öâ7V66W72"Ğ¢&V6V—E²&–çFVw&F–öâ%ÒÒ–çFVw&F–öàĞ¢5²&–çFVw&F–öâ%ÒÒ²'7FGW2#¢–çFVw&F–öå²'7FGW2%ÒÀĞ¢'6÷W&6Uö6öÖÖ—B#¢&V6V—E²'6÷W&6Uö6öÖÖ—B%ÒÀĞ¢''Våö¶W’#¢¶W’Â'F÷FÂ#¢–çFVw&F–öâævWB‚'F÷FÂ"’ÀĞ¢'76VB#¢–çFVw&F–öâævWB‚'76VB"’ÀĞ¢&f–ÆVB#¢–çFVw&F–öâævWB‚&f–ÆVB"—ĞĞ¢5²&7W'6÷"%ÒÒ&V6V—E²&æW‡Eö7W'6÷"%ĞĞ¢5²'&Wf—6–öâ%ÒÒ2ævWB‚'&Wf—6–öâ"Â’²Ğ¢5²&Æ7E÷6÷W&6Uö6öÖÖ—B%ÒÒ&V6V—E²'6÷W&6Uö6öÖÖ—B%ĞĞ¢5²&Æ7E÷'Våö¶W’%ÒÒ¶WĞ¢5²&Æ7E÷WF2%ÒÒ&V6V—E²&vVæW&FVE÷WF2%ĞĞ¢2ç6WFFVfVÇB‚'&ö6W76VE÷'Våö¶W—2"ÂµÒ’æVæB†¶W’Ğ¢5²'&ö6W76VE÷'Våö¶W—2%ÒÒ5²'&ö6W76VE÷'Våö¶W—2%Õ²Ó#S¥ĞĞ¢2ç6WFFVfVÇB‚&fÖ–Æ–W2"Â·ÒĞ¢f÷"‚–â&V6V—E²'&W7VÇG2%Ó Ğ¢öÆBÒ5²&fÖ–Æ–W2%ÒævWB‡…²&–B%ÒÂ·ÒĞ¢&V6÷&BÒ²'7FGW2#¢…²'7FGW2%ÒÂ'6÷W&6Uö6öÖÖ—B#¢&V6V—E²'6÷W&6Uö6öÖÖ—B%ÒÀĞ¢''Våö¶W’#¢¶W’Â'7G&–7FÇ•ö6ö×ÆWFR#¢fÇ6WĞĞ¢–b…²&–B%ÒÓÒ&–÷&—G•ö–C Ğ¢&V6÷&E²&Æ7E÷&V6†V6µ÷&Wf—6–öâ%ÒÒ5²'&Wf—6–öâ%ĞĞ¢VÆ–b…²'7FGW2%ÒÓÒ$dõ$ÔÅô4„T4µôd”ÄTEôõ%ô$Äô4´TB"æB&Æ7E÷&V6†V6µ÷&Wf—6–öâ"–âöÆC Ğ¢&V6÷&E²&Æ7E÷&V6†V6µ÷&Wf—6–öâ%ÒÒöÆE²&Æ7E÷&V6†V6µ÷&Wf—6–öâ%ĞĞ¢5²&fÖ–Æ–W2%Õ·…²&–B%ÕÒÒ&V6÷&@Ğ¢5²wVæF–æuö†—7F÷'•÷&V6V—BuÒÒ&V6V—@Ğ¢5²vÆ7E÷&V6V—E÷6†#SbuÒÒVWVUöF–vW7B‡&V6V—BĞ¢6fR‡7FFU÷F‚Â2Ğ¢&V6÷fW%ö†—7F÷'’‡&ö÷BÂ2Â6fRĞ¢&–çB†§6öâæGV×2‡²'W'6—7FVEöÆö6ÆÇ’#¢G'VRÂ'&Wf—6–öâ#¢5²'&Wf—6–öâ%ÒÂ&7W'6÷"#¢5²&7W'6÷"%ÒÂ''Våö¶W’#¢¶W—Ò’Ğ Ğ¦–bõöæÖUõòÓÒ%õöÖ–åõò# Ğ¢Ò&w'6Rä&wVÖVçE'6W"‚Ğ¢æFEö&wVÖVçB‚&ÖöFR"Â6†ö–6W3Õ²&WfÇVFR"Â'W'6—7B%ÒĞ¢æFEö&wVÖVçB‚"Ò×&Wò"Â&WV—&VCÕG'VRÂ6†ö–6W3Õ²%vööÅ&F""Â%––å–T¦’%ÒĞ¢æFEö&wVÖVçB‚"Ò×VWVR"ÂFVfVÇCÒ"æv—F‡V"÷&VÆ’÷VWVRæ§6öâ"Ğ¢æFEö&wVÖVçB‚"Ò×6÷W&6R"ÂFVfVÇCÒ&6æF–FFR"Ğ¢æFEö&wVÖVçB‚"Ò×7FFR"Â&WV—&VCÕG'VRĞ¢æFEö&wVÖVçB‚"ÒÖ÷WGWB"ÂFVfVÇCÒ"ç&VÆ’×&W÷'B÷&V6V—Bæ§6öâ"Ğ¢æFEö&wVÖVçB‚"Ò×&V6V—B"ÂFVfVÇCÒ"ç&VÆ’×&W÷'B÷&V6V—Bæ§6öâ"Ğ¢æFEö&wVÖVçB‚"ÒÖÆ–Ö—B"ÂG—SÖ–çBÂFVfVÇCÓ"Ğ¢÷BÒç'6Uö&w2‚Ğ¢–bæ÷BÃÒ÷BæÆ–Ö—BÃÒ3 Ğ¢æW'&÷"‚&Æ–Ö—B×W7B&RÓ2"Ğ¢†WfÇVFR–b÷BæÖöFRÓÒ&WfÇVFR"VÇ6RW'6—7B’†÷BĞ