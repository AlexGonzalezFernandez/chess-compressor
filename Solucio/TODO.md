# TODO

Estat actual: fases 1, 2, 3 i 4 fetes. El mode per defecte es
`MODE_CHESS`. Resultat sobre els 7 fitxers publics: R=5.122, compressio
agregada 269.8 kB/s, descompressio agregada 334.8 kB/s i round-trip
lossless verificat.


## Fase 1 - baseline

- [x] Parser PGN minim
- [x] Mode identity amb capcalera `CDI1`
- [x] Wrapper executable `compress.cdi`
- [x] `test_lossless.py` amb round-trip


## Fase 2 - codificador generic

- [x] Codificador aritmetic binari inicial, descartat per lent
- [x] Range coder byte-oriented
- [x] Model ordre 2 amb Fenwick tree per context
- [x] Optimitzacio del loop de descompressio
- [x] Benchmark sobre els 7 tests: R=3.893


## Fase 3 - parsing semantic

- [x] Separar capcaleres i movetext en dos streams
- [x] Parser de tags `[Key "Value"]`
- [x] Codificacio especifica per `Result`, `UTCDate`, `UTCTime`, ELOs,
      `ECO`, `Site`, `Event`, `Termination`, rating diffs, titles i
      `TimeControl`
- [x] Diccionari intra-fitxer per jugadors
- [x] Diccionari intra-fitxer per obertures
- [x] Benchmark final fase 3: R=4.828

Experiment descartat: codificar `{ [%eval X] }` en binari. Empitjorava la
ratio perque el range coder ja comprimia molt be el patro textual.


## Fase 4 - motor d'escacs

- [x] Representacio de posicio amb mailbox 0x88
- [x] Generacio de moviments pseudo-legals per peca
- [x] Filtre d'escac fent make-move i comprovant si el rei queda atacat
- [x] En passant, enroc i promocions
- [x] Parser SAN
- [x] Codificar moviments com index de moviment pseudo-legal
- [x] Guardar metadata SAN compacta per reconstruir exactament
- [x] Optimitzar velocitat abans d'activar-ho per defecte
- [x] Verificar velocitat sobre els 7 fitxers publics

Resultat final de `MODE_CHESS`:

    R = 5.122
    compressio agregada = 269.8 kB/s
    descompressio agregada = 334.8 kB/s
    pitjor compressio = 254.3 kB/s
    pitjor descompressio = 328.8 kB/s


## Fase 5 - entregables

- [x] Redactar `Document.md` amb el metode final
- [x] Revisar `Readme.md` amb les xifres finals
- [x] Actualitzar `DECISIONS.md`
- [ ] Netejar imports i funcions no utilitzades del `compress.src`
- [ ] Verificar que tot funciona en un Linux de la FIB
- [ ] Convertir `Document.md` a PDF si l'entrega ho exigeix
