# MotionChallenge website

An open, reproducible benchmark for humanoid motion tracking.

[Website & leaderboard](https://motionchallenge-project.github.io/motionchallenge/) · [Evaluation core](https://github.com/MotionChallenge-Project/MotionChallenge-Core)

```sh
SITE_BASE_PATH='' python3 build.py
python3 -m http.server 8768 --directory docs
```

GitHub Pages serves `website:/docs`. Run `python3 build.py` before publishing.

`content/` contains published model records, result summaries and trace receipts. Full traces, weights and datasets remain outside Git. Each checkpoint version has a separate entry; scores never transfer between versions. The evaluation kernel and model adapters remain independent repositories.

Benchmark pages are data-driven: add an entry to `content/benchmarks.json`, its dataset document, and a robot/protocol entry in `content/tracks.json`. Each track points to its documentation and frozen protocol JSON. The common renderer resolves threshold bindings from that protocol; it does not contain dataset names or failure rules. Additional robots appear in the selectors without changing page templates. Scoring support in the core is a separate requirement.

Model cards (`/models/<id>/`) describe checkpoint identity and inference. Scores, protocol versions, reproduction commands and receipts live in `/evaluations/<track>/<model>/`; the leaderboard links names to model cards and metric values to evaluation records.
