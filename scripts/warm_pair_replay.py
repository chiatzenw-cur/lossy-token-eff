#!/usr/bin/env python3
"""One warm server for ONE arm, for running a baseline/force-commit pair on two servers.

Same run layout, request path and grading inputs as fresh_server_replay.py's warm mode, but:
- only its own server is stopped (no global stop_server.sh, which kills every vLLM process);
- writes a --ready-file once its server is healthy, so a partner can start after this server's
  EngineCore has already read the shared /tmp knob files (they are read once, at import);
- no campaign manifest write (two processes would race on fresh_server_replay.json); run.json is
  the record.

Usage: warm_pair_replay.py --ready-file F [fresh_server_replay args ...] --port P
"""

import os
import pathlib
import signal
import sys
import time
import datetime as dt

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import fresh_server_replay as fsr  # noqa: E402


def main() -> int:
    argv = sys.argv[1:]
    ready = None
    if "--ready-file" in argv:
        i = argv.index("--ready-file")
        ready = pathlib.Path(argv[i + 1])
        del argv[i : i + 2]
    sys.argv = [sys.argv[0]] + argv
    args = fsr.parse_args()
    if len(args.arms) != 1:
        raise SystemExit("warm_pair_replay: exactly one arm per process")
    arm = args.arms[0]
    bench = args.prompt_root.name
    runs_root = REPO / args.runs_root / bench
    method, params = fsr.method_and_params_for(args, arm)
    tag = fsr.tag_for(args, arm)
    todo = [c for c in args.cases if not (runs_root / method / params / c / "seed_0" / "run.json").is_file()]
    print(f"{len(todo)} run(s) for {method}/{params} on port {args.port}", flush=True)
    if not todo:
        if ready:
            ready.write_text("skipped\n")
        return 0
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = REPO / args.log_root / f"{tag}_pair_port{args.port}_{stamp}.log"
    fsr.set_trace_destination(None)
    fsr.set_hidden_state_destination(None)
    process = fsr.start_server(args, arm, log_path)
    if ready:
        ready.write_text("ready\n")
    failures = 0
    try:
        for case in todo:
            started = time.perf_counter()
            done = fsr.request_once(args, arm, case, 0, tag, method, params, runs_root, log_path, assert_fresh=False)
            failures += done.returncode != 0
            print(f"{case} rc={done.returncode} {time.perf_counter() - started:.0f}s", flush=True)
    finally:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=120)
        print(f"server on port {args.port} stopped", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
