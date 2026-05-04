# TODO

Estat actual: fases 2 i 3 fetes. R=4.828, velocitat comoda per sobre del
llindar, lossless verificat.

## Fase 1 - baseline
- [x] Parser PGN minim
- [x] Mode identity (copia literal amb capçalera CDI1)
- [x] Wrapper executable compress.cdi
- [x] test_lossless.py amb round-trip

## Fase 2 - codificador generic
- [x] Codificador aritmetic binari (descartat: lent)
- [x] Range coder byte-oriented
- [x] Model ordre-2 amb Fenwick tree per context
- [x] Inline del loop de descompressio per arribar als 385 kB/s
- [x] Benchmark sobre els 7 tests  (R=3.893)

## Fase 3 - parsing semantic
- [x] Separar capçaleres i movetext en dos streams (R=4.041)
- [x] Parser de tags [Key "Value"]
- [x] Codificacio especifica per:
    - [x] Result (2 bits via byte marker)
    - [x] UTCDate (3 bytes packed)
    - [x] UTCTime (3 bytes com segons del dia)
    - [x] WhiteElo / BlackElo (2 bytes uint16)
    - [x] ECO (2 bytes packed A00..E99)
    - [x] Site (prefix lichess.org + 8 chars)
    - [x] Event (3 categories curtes + tournament/swiss amb id)
    - [x] Termination (2 bits via byte marker)
    - [x] WhiteRatingDiff / BlackRatingDiff (zigzag varint)
    - [x] WhiteTitle / BlackTitle (2 bits via byte marker)
    - [x] TimeControl (<secs>+<incr> -> 2 varints)
- [x] Diccionari intra-fitxer per jugadors (White + Black comparteixen)
- [x] Diccionari intra-fitxer per obertures
- [x] Benchmark final Fase 3:  R=4.828

### Experiments fallats a la Fase 3 (per record)
- [!] Codificar els comentaris { [%eval X] } com a binari (marker + valor
      packed). Pensava que seria gran perque son ~15% del fitxer, pero el
      RC ja els comprimia molt be al patro de text. Canviar-los per
      binari feia que els bytes fossin menys predictibles pel RC i la
      ratio baixava lleugerament. Va costar descobrir tambe un bug
      colateral: el byte sentinella entre movetexts podia coincidir amb
      un byte del valor binari. Ho vaig deixar com esta.

## Fase 4 - motor d'escacs (stretch)
- [ ] Representacio de posicio (mailbox 0x88 o array 8x8)
- [ ] Generacio de moviments pseudo-legals per peça
- [ ] Filtre d'escac (pins, claus)
- [ ] En passant, enroc, promocions
- [ ] Parser SAN -> moviment
- [ ] Codificar index del moviment en la llista legal
- [ ] Verificar velocitat, potser calgui limitar-ho nomes a alguns tipus
      de peça

## Fase 5 - entregables
- [ ] Redactar Document.pdf (ara hi ha un Document.md d'esborrany)
- [ ] Revisar Readme.md amb les xifres finals
- [ ] Netejar imports i funcions no utilitzades del compress.src
- [ ] Verificar que tot funciona en un Linux de la FIB
