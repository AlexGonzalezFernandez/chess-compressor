# TODO

Estat actual: feta la fase 2. Ratio 3.89, velocitat OK, lossless verificat.

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
- [x] Benchmark sobre els 7 tests

## Fase 3 - parsing semantic (pendent)
- [ ] Separar capçaleres i movetext en dos streams
- [ ] Parser de tags [Key "Value"]
- [ ] Codificacio especifica per:
    - [ ] Result (2 bits)
    - [ ] UTCDate (delta respecte anterior + 3 enters)
    - [ ] UTCTime (3 enters compactats)
    - [ ] WhiteElo / BlackElo (12 bits)
    - [ ] ECO (1 byte)
    - [ ] Site (treure prefix lichess.org)
- [ ] Diccionari intra-fitxer per jugadors i obertures
- [ ] Tokenitzar movetext (un "simbol" per moviment, no per byte)
- [ ] Benchmark comparatiu amb la fase 2

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
