"""Public protocol highlights; detailed definitions live in Core docs."""


def render(page, intro, github):
    body = intro('EVALUATION PROTOCOL', 'Evaluation protocol',
                 'Conditions, failure thresholds and scoring.')
    body += '''<div class="policy-content docs">
<section><h2>Benchmark and controller</h2>
<div class="rule-cards responsibility-cards">
<article><span class="card-symbol" aria-hidden="true">≡</span><h3>Benchmark</h3><p>Data · robot · physics · reset · failure conditions · scoring.</p></article>
<article id="inference"><span class="card-symbol" aria-hidden="true">↔</span><h3>Controller</h3><p>Author-native observations · history · policy clock · action processing.</p></article>
</div></section>
<section id="contract"><h2>LAFAN40 · G1</h2>
<div class="protocol-tags"><span>40 complete motions</span><span>MuJoCo 3.17.0 batch</span><span>No noise / randomization</span><span>Friction 1</span></div>
<p>Start at the first reference pose and velocity. Continue to the final frame, without resetting after failure.</p>
<table class="rules-table"><thead><tr><th scope="col">Failure condition</th><th scope="col">Threshold</th></tr></thead><tbody>
<tr><td>Absolute torso height error</td><td>&gt; 0.25 m</td></tr>
<tr><td>Absolute projected-gravity Z difference: actual vs reference torso</td><td>&gt; 0.8</td></tr>
<tr><td>Maximum wrist or ankle world-height error</td><td>&gt; 0.25 m</td></tr>
</tbody></table>
<p class="small">Any condition records the first failure. No XY or yaw threshold. <a href="/benchmarks/lafan40/#failure-conditions">Exact definitions ↗</a></p>
</section>
<section id="alignment"><h2>Metrics</h2>
<div class="rule-cards metric-cards">
<article><span class="card-symbol" aria-hidden="true">%</span><h3>Success ↑</h3><p>Motions completed without failure.</p></article>
<article><span class="card-symbol" aria-hidden="true">→</span><h3>Completion ↑</h3><p>Fraction of duration reached before first failure.</p></article>
<article><span class="card-symbol" aria-hidden="true">mm</span><h3>MPBPE ↓</h3><p>Mean position error over 14 body origins.</p></article>
</div>
<table class="rules-table"><thead><tr><th scope="col">Alignment</th><th scope="col">Removed before measuring error</th></tr></thead><tbody>
<tr><td>XY + yaw</td><td>Per-frame horizontal root translation and heading difference</td></tr>
<tr><td>XY only</td><td>Per-frame horizontal root translation</td></tr>
<tr><td>None</td><td>Nothing; compare world positions directly</td></tr>
</tbody></table>
<div class="metric-ranges"><div><strong>Early termination</strong><span>Through the first failure, including that frame.</span></div><div><strong>No termination</strong><span>Entire motion, including post-failure states.</span></div></div>
<p class="small">3 alignments × 2 time ranges = 6 error views. Average frames within each motion, then weight motions equally. Alignment does not affect success or completion.</p>
</section>
<section id="evidence"><h2>Verification</h2>
<div class="verification-flow"><span>Pinned weights &amp; code</span><span aria-hidden="true">→</span><span>Inference check</span><span aria-hidden="true">→</span><span>Full-suite traces</span><span aria-hidden="true">→</span><span>Independent verification &amp; repeat</span></div>
<div class="actions"><a class="button" href="/admission/">Policy admission ↗</a>'''
    body += ('<a class="text-link" href="' + github +
             '/MotionChallenge-Core/blob/main/docs/PROTOCOL.md">Full protocol &amp; formulas ↗</a>')
    body += '</div></section></div>'
    page('/protocol/', 'Evaluation protocol', body, 'Protocol')
