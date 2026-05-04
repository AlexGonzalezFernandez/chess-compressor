# Practica CDI 2025-2026 - compressor PGN

Compressor sense perdues per a fitxers PGN (partides d'escacs).


## Que es necessita

Nomes Python 3. No uso cap paquet extern, nomes la llibreria estandard
(sys, os, struct, array). En particular no faig servir zlib ni cap
altra llibreria de compressio, que estan prohibides per l'enunciat.

Al Linux dels laboratoris de la FIB ja ve instal·lat Python 3, aixi
que no cal fer res.


## Fitxers

    compress.src      codi font
    compress.cdi      executable (script que crida python3 compress.src)
    Readme.md         aixo
    Document.pdf      explicacio del metode i del format comprimit

Aquests altres els deixo al directori pero no son part estricta de
l'entrega, son notes meves i eines auxiliars:

    DECISIONS.md      decisions de disseny, en pla llibreta
    TODO.md           fases pendents
    test_lossless.py  script que verifica i mesura


## Compilacio i execucio

No cal compilar res. Nomes cal que compress.cdi tingui permis
d'execucio:

    chmod +x compress.cdi

I despres:

    ./compress.cdi entrada sortida

El mateix programa comprimeix o descomprimeix segons el contingut del
fitxer d'entrada: si comença pels bytes "CDI1" (el magic number que jo
poso als fitxers comprimits), el descomprimeix; si no, el comprimeix.
Aixi la mateixa comanda serveix per les dues coses:

    ./compress.cdi partida.pgn partida.cdi      # comprimir
    ./compress.cdi partida.cdi partida2.pgn     # descomprimir
    diff partida.pgn partida2.pgn               # hauria de sortir buit


## Verificacio

He deixat test_lossless.py per passar tots els fitxers del directori
SetPartidesTests, comprimir-los, descomprimir-los i comparar sha256
amb l'original. Tambe mesura kB/s. Es corre aixi (des del directori
Solucio):

    python3 test_lossless.py

Sortida aproximada:

    fitxer                   original  comprimit   ratio    c kB/s    d kB/s  ok
    SetPartides1.pgn           1.6 MB   455.2 KB   3.665     374.4     385.7  ok
    SetPartides2.pgn           3.7 MB   969.7 KB   3.916     411.9     387.1  ok
    ...
    TOTAL                     23.9 MB     6.2 MB   3.893

    R = 3.893
    lossless: tot identic


## Resum del metode

Codificador d'entropia (range coder de 32 bits) amb un model estadistic
adaptatiu d'ordre 2 (context = parell dels dos bytes anteriors). Les
frequencies per context es guarden en arbres Fenwick per poder
actualitzar-les i consultar-les en O(log 256).

Explicat amb mes detall al Document.pdf.
