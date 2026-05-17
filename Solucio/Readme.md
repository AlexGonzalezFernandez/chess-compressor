# Practica CDI 2025-2026 - compressor PGN

Compressor sense perdues per a fitxers PGN (partides d'escacs).


## Que es necessita

Nomes Python 3. No uso cap paquet extern, nomes la llibreria estandard
(`sys`, `os`, `struct`, `array`). En particular no faig servir `zlib`,
`bz2`, `lzma` ni cap altra llibreria de compressio feta.


## Fitxers

    compress.src      codi font
    compress.cdi      executable (script que crida python3 compress.src)
    Readme.md         aquest fitxer
    Document.md       explicacio del metode i del format comprimit

Aquests altres fitxers son notes i eines auxiliars:

    DECISIONS.md      decisions de disseny i evolucio per fases
    TODO.md           estat de les fases
    test_lossless.py  script que verifica i mesura


## Compilacio i execucio

No cal compilar res. Nomes cal que `compress.cdi` tingui permis
d'execucio:

    chmod +x compress.cdi

I despres:

    ./compress.cdi entrada sortida

El mateix programa comprimeix o descomprimeix segons el contingut del
fitxer d'entrada: si comenca pels bytes `CDI1`, el descomprimeix; si no,
el comprimeix.

    ./compress.cdi partida.pgn partida.cdi
    ./compress.cdi partida.cdi partida2.pgn
    diff partida.pgn partida2.pgn

El `diff` hauria de sortir buit.


## Verificacio

He deixat `test_lossless.py` per passar tots els fitxers del directori
`SetPartidesTests`, comprimir-los, descomprimir-los i comparar SHA-256
amb l'original. Tambe mesura kB/s.

Des del directori `Solucio`:

    python3 test_lossless.py


## Resum del metode

La versio actual usa per defecte `MODE_CHESS`.

El fitxer PGN es divideix en partides. Per cada partida se separen:

- capcaleres PGN (`[Event "..."]`, `[White "..."]`, etc.)
- movetext en SAN (`1. e4 c5 2. Nf3 ...`)

Les capcaleres es codifiquen semanticament: dates, hores, ELOs, resultats,
ECO, time controls, URLs de Lichess, jugadors i obertures es transformen
a una representacio binaria mes compacta.

El movetext usa un motor d'escacs simple:

- representacio de posicio amb mailbox 0x88
- generacio de moviments pseudo-legals
- comprovacio de legalitat del moviment seleccionat
- suport d'enroc, en passant i promocions
- parser SAN per tokens com `e4`, `Nf3`, `Nbd7`, `R1e1`, `exd8=Q+`,
  `O-O` i `O-O-O`

Els moviments SAN es codifiquen com un index dins de la llista
pseudo-legal de la posicio. Per reconstruir exactament el text original,
es guarda metadata compacta per la desambiguacio SAN i pels sufixos
`+`, `#`, `!`, `?`. Els numeros de jugada, espais, resultats i comentaris
es conserven literalment.

Finalment, els streams resultants es passen per un range coder de 32 bits
amb model adaptatiu d'ordre 2 i arbres Fenwick.


## Resultats

Mesurat sobre els 7 fitxers publics de `SetPartidesTests` en aquesta
maquina:

    fitxer                   ratio    c kB/s    d kB/s
    SetPartides1.pgn         4.797     254.3     345.1
    SetPartides2.pgn         5.167     269.6     328.8
    SetPartides3.pgn         5.049     273.3     342.0
    SetPartides4.pgn         4.799     259.6     336.3
    SetPartides5.pgn         5.240     284.2     335.4
    SetPartides6.pgn         5.181     275.1     332.5
    SetPartides7.pgn         5.288     255.1     331.5
    TOTAL                    5.122     269.8     334.8

El pitjor cas de compressio queda a 254.3 kB/s, per sobre del minim de
250 kB/s. La descompressio queda sempre per sobre del minim.

La comprovacio lossless dona sortida identica byte a byte als originals.
