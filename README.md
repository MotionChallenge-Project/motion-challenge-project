# Motion Challenge website

[Website & leaderboard](https://motion-challenge-project.github.io/motion-challenge-project/) · [Evaluation core](https://github.com/motion-challenge-project/motion-challenge)

```sh
python3 build.py
python3 -m http.server 8768 --directory docs
```

GitHub Pages serves `website:/docs`. Build with `SITE_BASE_PATH=''` for a root-level local preview.

`content/` contains published model records, result summaries and trace receipts. Full traces, weights and datasets remain outside Git. Each checkpoint version has a separate entry; scores never transfer between versions. The evaluation kernel and model adapters remain independent repositories.
