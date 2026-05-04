import re
from collections import Counter

# Patterns comuns de Event i Site
sites = Counter()
events = Counter()
for i in range(1, 8):
    with open(f'../SetPartidesTests/SetPartides{i}.pgn', 'rb') as f:
        data = f.read()
    for m in re.finditer(rb'\[Site "([^"]*)"\]', data):
        sites[m.group(1)] += 1
    for m in re.finditer(rb'\[Event "([^"]*)"\]', data):
        events[m.group(1)] += 1

print('=== Site pattern ===')
# Tots comencen amb https://lichess.org/?
prefixes = Counter()
for s in sites:
    pre = s[:22]  # https://lichess.org/ = 20 + 2 per aprox
    prefixes[pre] += 1
print(f'mostres sites ({len(sites)} unics): ')
for s, _ in sites.most_common(3):
    print('  ', s)

# Les 8 xifres finals son base 62?
lens = Counter()
chars = Counter()
for s in sites:
    # Si comença per https://lichess.org/
    if s.startswith(b'https://lichess.org/'):
        suffix = s[len(b'https://lichess.org/'):]
        lens[len(suffix)] += 1
        for c in suffix:
            chars[chr(c)] += 1
print(f'longituds de sufix:', dict(lens))
print('alfabet sufix:', ''.join(sorted(chars)))

print()
print('=== Event pattern ===')
print(f'event unics: {len(events)}')
for e, n in events.most_common(10):
    print(n, e)

# Events que son "tournament" tenen URL despres
tourn = [e for e in events if b'tournament' in e or b'swiss' in e]
print(f'tournament/swiss events: {len(tourn)}')
for t in tourn[:3]:
    print('  ', t)
