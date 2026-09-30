#!/usr/bin/env python3
"""Addendum step 0.2 (campaign/addendum/README.md): the consolidated V2
rejection sampler that Qwen3-8B needs (cascade/DIRECTIONS.md D8).

  python3 scripts/addendum_v2_install.py prepare [--file ~/Downloads/rejection_sampler_utils.py]
      verify the file is the final consolidated state (sha256 68d0a904..., patches/HASHES.txt
      label mentored-dec), diff it against pristine vLLM 0.26.0 (fetched from a Nibi venv,
      sha256 bfaec14e...) into patches/vllm-0.26.0-v2-consolidated.patch, check the patch
      reproduces the file exactly, and note it in patches/HASHES.txt (as a comment: the hash
      line itself is already there, and a second line would give apply.sh two labels)
  python3 scripts/addendum_v2_install.py install
      apply the patch to every lane venv (only if its V2 file is pristine) and verify the hash;
      safe while GPT-OSS jobs run -- GPT-OSS-20B never uses the V2 runner
  python3 scripts/addendum_v2_install.py smoke
      queue the two Qwen3 smoke cases (gsm8k_qwen3 case_001, seed 7: strict and mentored_dec
      0.75) at the front of lane A's work list, into runs/addendum/smoke_qwen3 (deleted after
      the check); the lane runs them between two arms, never concurrently with another job
  python3 scripts/addendum_v2_install.py check
      read the two smoke runs + server logs back: ok status, and the patch's alpha line
      printed by the mentored_dec server; on success, unblock the Qwen3 manifest rows
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import addendum_campaign as ac  # noqa: E402

EXPECTED = "68d0a904230a82d7aa90916e9ed60297e3c725eeb0188b633893e03fb5b9f938"
PRISTINE = "bfaec14e220cf669ddfd2b3ef6d2c556dc8fae60ef71e65a2e7ae068fb386a2a"
SUPERSEDED = {  # earlier states of the same file, recorded in patches/HASHES.txt -- all known-buggy
    "f0772ebb0122d48d02a423564aeeea2e9ce15346484d8e0c8d9952f615384193": "pre-hsr-guard (2026-08-22)",
    "0992ab58e3e413e1e82d11e09ee18c2cff755cd7c0b54f064a405c90c7b39846": "hsr-guard alpha-gate bug",
    "8233a02a75f1ed2e5fced01b575e144055b1e38e063f088db6f5a8ba7359b90c": "alpha-gate fix + debug prints, mask bug",
    "c62c6a4a220e4d805d70882c0b0e72d289b9277f516509a43bf247d5943b0caf": "mask bug still present",
}
REL = "vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py"
PATCH = REPO / "patches" / "vllm-0.26.0-v2-consolidated.patch"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def site_packages(lane: str) -> str:
    return f"{ac.LANES[lane]['repo']}/.venv-vllm/lib/python3.12/site-packages"


def cmd_prepare(args) -> int:
    new = pathlib.Path(args.file).expanduser().read_bytes()
    h = sha(new)
    if h != EXPECTED:
        print(f"refusing: sha256 {h} is not the final consolidated state {EXPECTED}"
              + (f" (it is the superseded '{SUPERSEDED[h]}' state)" if h in SUPERSEDED else ""), file=sys.stderr)
        return 1
    pristine = ac.ssh(f"cat {site_packages('A')}/{REL}").stdout
    if sha(pristine) != PRISTINE:
        print(f"lane A's V2 file is not pristine (sha256 {sha(pristine)}); fetch pristine elsewhere", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        a, b = pathlib.Path(tmp) / "a", pathlib.Path(tmp) / "b"
        a.write_bytes(pristine)
        b.write_bytes(new)
        diff = subprocess.run(["diff", "-u", "--label", f"a/{REL}", "--label", f"b/{REL}", str(a), str(b)],
                              capture_output=True).stdout
        work = pathlib.Path(tmp) / "work"
        (work / REL).parent.mkdir(parents=True)
        (work / REL).write_bytes(pristine)
        subprocess.run(["patch", "-p1", "-d", str(work)], input=diff, check=True, capture_output=True)
        if sha((work / REL).read_bytes()) != EXPECTED:
            print("patch does not reproduce the file exactly -- not written", file=sys.stderr)
            return 1
    PATCH.write_bytes(diff)
    hashes = REPO / "patches" / "HASHES.txt"
    text = hashes.read_text(encoding="utf-8")
    marker = "# vllm-0.26.0-v2-consolidated.patch"
    if marker not in text:
        text = text.replace(
            f"{EXPECTED}  mentored-dec\n",
            f"{EXPECTED}  mentored-dec\n"
            f"{marker} (added 2026-09-29, NAACL addendum step 0.2): pristine ({PRISTINE[:12]}...)\n"
            f"# -> this state, recovered from the old H100 box; apply with `patch -p1 -d <site-packages>`.\n", 1)
        hashes.write_text(text, encoding="utf-8")
    ac.progress(f"Step 0.2: wrote patches/vllm-0.26.0-v2-consolidated.patch ({len(diff.splitlines())} lines; "
                f"pristine {PRISTINE[:12]} -> {EXPECTED[:12]}, round-trip verified)")
    print(f"wrote {PATCH} ({len(diff.splitlines())} lines), verified round trip")
    return 0


def cmd_install(args) -> int:
    ac.cmd_push(argparse.Namespace())  # ships patches/*.patch? no -- send the patch explicitly below
    for lane in ac.LANES:
        sp = site_packages(lane)
        cur = ac.ssh(f"sha256sum {sp}/{REL}").stdout.decode().split()[0]
        if cur == EXPECTED:
            print(f"lane {lane}: already installed")
            continue
        if cur != PRISTINE:
            print(f"lane {lane}: V2 file is neither pristine nor the consolidated state ({cur}) -- skipped", file=sys.stderr)
            continue
        ac.ssh(f"patch -p1 -d {sp}", input_bytes=PATCH.read_bytes())
        after = ac.ssh(f"sha256sum {sp}/{REL}").stdout.decode().split()[0]
        ok = after == EXPECTED
        ac.progress(f"Step 0.2: lane {lane} venv V2 file {'installed' if ok else 'INSTALL FAILED'} (sha256 {after[:12]})")
        print(f"lane {lane}: {'ok' if ok else 'FAILED'} {after}")
    return 0


def smoke_items() -> list[dict]:
    items = []
    for method, alpha in (("strict", "strict"), ("mentored_dec", "0.75")):
        row = ac.make_row("0.2", "smoke_qwen3", "gsm8k_qwen3", method, alpha, 7)
        item = ac.work_item(row, ["case_001"])
        item["id"] = f"smoke|{method}"
        items.append(item)
    return items


def cmd_smoke(args) -> int:
    state = ac.load_state()
    state.setdefault("extra_items", {})["A"] = smoke_items()
    ac.save_state(state)
    ac.cmd_plan(argparse.Namespace(quiet=True))
    ac.cmd_push(argparse.Namespace())
    ac.progress("Step 0.2: queued the two Qwen3 smoke cases at the front of lane A (runs/addendum/smoke_qwen3)")
    print("queued; they run on lane A between two arms")
    return 0


def cmd_check(args) -> int:
    root = ac.LANES["A"]["root"]
    out = {}
    for method, params in (("strict", "strict"), ("mentored_dec", "alpha0.75")):
        run = ac.ssh(f"cat {root}/runs/addendum/smoke_qwen3/gsm8k_qwen3/{method}/{params}/case_001/seed_7/run.json",
                     check=False).stdout.decode()
        out[method] = json.loads(run) if run else None
    log = ac.ssh(f"grep -h -E 'MENTORED-DEC|alpha=' {root}/logs/runs/addendum/smoke_qwen3/gsm8k_qwen3/mentoredDec0.75*.log | head -5",
                 check=False).stdout.decode()
    ok = all(v and v.get("status") == "ok" for v in out.values()) and "0.75" in log
    for method, v in out.items():
        print(method, None if v is None else {k: v.get(k) for k in ("status", "output_tokens", "l_bar", "finish_reason")})
    print("mentored_dec server log alpha lines:\n" + log)
    ac.progress(f"Step 0.2 Qwen3 smoke: {'PASSED' if ok else 'NOT PASSED'} -- strict {out['strict'] and out['strict'].get('status')}, "
                f"mentored_dec 0.75 {out['mentored_dec'] and out['mentored_dec'].get('status')}; log: {log.strip()[:200]!r}")
    if ok:
        state = ac.load_state()
        state["blocked_qwen3"] = False
        state.get("extra_items", {}).pop("A", None)
        ac.save_state(state)
        ac.ssh(f"rm -rf {root}/runs/addendum/smoke_qwen3", check=False)
        print("Qwen3 unblocked: next `addendum_campaign.py cycle` assigns the Qwen3 rows to the lanes")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--file", default="~/Downloads/rejection_sampler_utils.py")
    p.set_defaults(fn=cmd_prepare)
    sub.add_parser("install").set_defaults(fn=cmd_install)
    sub.add_parser("smoke").set_defaults(fn=cmd_smoke)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
