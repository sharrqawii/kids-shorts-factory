# Pip — character bible v1

Pip is a curious baby capybara. He has a caramel coat, cream-colored broad
rectangular muzzle, small round ears, dark eyes, rosy cheeks, and four stubby
feet. He has no visible tail. His mint neckerchief and yellow flower pin are
the distinctive details to preserve between episodes.

The modeling units are arbitrary meters. The fixed palette and principal
scales live in `assets/pip.json`; the rest of his geometry lives in one reusable
`make_pip` function. The root is named `pip-capybara-v1`. Child names begin with
`Pip`. The head is a separate pivot. Eyes, feet, and root can be animated without
changing the character's mesh construction.

Motion should be gentle: small alternating foot swings, a light bounce, slow
head tilts, occasional short blinks, and tiny happy hops. Keep interactions
friendly and easy to understand without speech. Do not add sudden flashes or
loud surprises. The strawberry episode uses a slow discovery, one soft boop,
two hops, and a floating heart.

For a second episode, reuse `make_pip` unchanged, create a new prop and story,
and preserve the character specification. If proportions change intentionally,
introduce a new explicit asset version. The current CLI implements one episode;
it is not a general story-writing or automatic episode-selection system yet.
