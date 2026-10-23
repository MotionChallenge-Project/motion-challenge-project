# Motion Challenge website

[Website & leaderboard](https://motion-challenge-project.github.io/motion-challenge-project/) · [Evaluation core](https://github.com/motion-challenge-project/motion-challenge)

```sh
SITE_BASE_PATH='' python3 build.py
python3 -m http.server 8768 --directory docs
```

GitHub Pages serves `website:/docs`. Run `python3 build.py` before publishing to restore the GitHub Pages URL prefix.

`content/` contains published model records, result summaries and trace receipts. Full traces, weights and datasets remain outside Git. Each checkpoint version has a separate entry; scores never transfer between versions. The evaluation kernel and model adapters remain independent repositories.
