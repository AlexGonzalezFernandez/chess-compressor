# Practica CDI 2025-2026 - compressor PGN

Autor: (posar nom)
Curs: CDI 2025-2026


## Objectiu

La practica demana comprimir sense perdues fitxers PGN de partides
d'escacs. La puntuacio depen de la ratio:

    R = mida total original / (mida total comprimit + penalitzacio executable)

Tambe cal mantenir una velocitat minima de 250 kB/s tant comprimint com
descomprimint.

La solucio final combina tres idees:

1. Un compressor generic d'entropia: range coder de 32 bits amb model
   adaptatiu d'ordre 2.
2. Codificacio semantica de les capcaleres PGN.
3. Codificacio dels moviments SAN amb un motor d'escacs simple.


## Organitzacio del codi

Tot el codi esta a `compress.src`, en un sol fitxer per simplificar
l'entrega. Les seccions principals son:

- constants del format i modes de compressio
- mode identity, nomes per debug
- range coder byte-oriented
- codificador aritmetic bit a bit antic, deixat com a referencia
- Fenwick tree per al model estadistic
- compressor generic d'ordre 2
- split de PGN en capcaleres i movetext
- codificacio semantica de tags
- motor d'escacs i codificacio SAN
- embolcall `CDI1`, dispatch de modes i `main()`

El mode per defecte es:

    MODE_CHESS = 4


## Format del fitxer comprimit

Tots els fitxers comprimits comencen amb:

    bytes 0..3   : "CDI1"
    byte  4      : versio del format, ara 1
    byte  5      : mode de compressio

Modes implementats:

    0 = identity
    1 = range coder + model ordre 2 sobre tot el fitxer
    2 = split capcaleres/movetext
    3 = semantic tags + movetext literal comprimit
    4 = semantic tags + moviments SAN amb motor d'escacs

En `MODE_CHESS`, el payload conte:

    byte          : flag intern del mode
    byte          : tipus de final de linia original (LF o CRLF)
    varint        : nombre de partides
    varint        : mida del stream de capcaleres comprimit
    bytes         : stream de capcaleres comprimit
    bytes         : stream de movetext comprimit

Guardar el tipus de final de linia permet acceptar fitxers amb `LF` i
amb `CRLF` i reconstruir-los byte a byte.


## Range coder i model generic

La base de compressio es un range coder de 32 bits que renormalitza byte
a byte. Aixo es mes rapid en Python que un codificador aritmetic bit a bit,
perque redueix molt les iteracions del bucle intern.

El model estadistic es adaptatiu d'ordre 2:

    context = dos bytes anteriors

Per cada context hi ha frequencies dels 256 bytes possibles. Les
frequencies es guarden en arbres Fenwick, que permeten:

- consultar prefixos
- actualitzar frequencies
- trobar el simbol corresponent a una frequencia acumulada

Els contextos es creen nomes quan apareixen. Les frequencies comencen a 1
per evitar probabilitats zero, i es reescalen quan el total es fa massa
gran.


## Codificacio semantica de capcaleres

Els PGN de test tenen tags molt regulars, per exemple:

    [Event "Rated Blitz game"]
    [Site "https://lichess.org/UO0u69dn"]
    [White "Rorionbrasil"]
    [Black "ceesar"]
    [Result "1-0"]
    [UTCDate "2014.09.29"]
    [UTCTime "23:05:30"]
    [WhiteElo "1399"]
    [BlackElo "1193"]
    [ECO "B12"]
    [Opening "Caro-Kann Defense: Advance Variation"]
    [TimeControl "300+1"]

En comptes de comprimir aquest text directament, es codifiquen camps
segons el seu tipus:

- `Result`, `Termination`, `Title`: codis petits
- `UTCDate`: data empaquetada en 3 bytes
- `UTCTime`: segons del dia en 3 bytes
- ELOs: enters de 16 bits
- `ECO`: lletra A-E i numero empaquetats
- `TimeControl`: dos varints
- `Site`: prefix de Lichess implicit i id final
- `Event`: casos comuns i tornejos/swiss amb id
- `White`, `Black`, `Opening`: diccionaris intra-fitxer

Si algun valor no encaixa en el format esperat, es guarda com a string
literal. Aixi el compressor continua sent sense perdues.


## Codificacio dels moviments

El movetext PGN conte moviments en SAN:

    1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6

La idea de la fase 4 es no guardar `Nf3` o `cxd4` com a text, sino com
un index de moviment en la posicio actual.

La posicio d'escacs es representa amb mailbox 0x88. El motor guarda:

- tauler
- torn
- drets d'enroc
- casella d'en passant
- posicio dels reis

Es generen moviments pseudo-legals per totes les peces. Per velocitat, la
versio final no genera la llista legal completa per indexar. Fa aixo:

1. Parseja el token SAN per obtenir peca, desti, promocio i desambiguacio.
2. Genera la llista pseudo-legal.
3. Busca el moviment pseudo-legal compatible amb el SAN.
4. Comprova nomes aquest moviment fent make-move i mirant si el rei queda
   atacat.
5. Guarda l'index dins de la llista pseudo-legal.

Aquesta decisio va ser clau per passar el minim de 250 kB/s.

Per reconstruir exactament el SAN original, el stream tambe guarda metadata:

- si calia desambiguacio per fitxer/rang (`Nbd7`, `R1e1`, etc.)
- sufix de jaque o mat (`+`, `#`)
- anotacions (`!`, `?`, `!?`, `?!`)

Els numeros de jugada, espais, resultats i comentaris `{ ... }` es guarden
literalment. Aixo evita perdre format i mante el round-trip byte a byte.


## Optimitzacions provades

La primera versio de `MODE_CHESS` indexava contra la llista de moviments
legals i generava SAN per tots els candidats. Funcionava i millorava la
ratio, pero era massa lenta:

    ratio 5.214, compressio 44.3 kB/s, descompressio 107.6 kB/s

Despres es van treure `+` i `#` del calcul del SAN i es van guardar com a
sufix literal. La compressio va pujar a uns 75 kB/s, encara insuficient.

També es va provar fer make/unmake en lloc de clonar el tauler per cada
moviment candidat. El guany va ser petit: el cost principal era generar
SAN i llistes legals massa sovint.

La versio final indexa contra pseudo-legals i valida nomes el moviment
seleccionat. Aixo redueix molt el cost i encara conserva la reconstruccio
exacta.


## Resultats

Resultats sobre els 7 fitxers publics:

    fitxer                   ratio    c kB/s    d kB/s
    SetPartides1.pgn         4.797     254.3     345.1
    SetPartides2.pgn         5.167     269.6     328.8
    SetPartides3.pgn         5.049     273.3     342.0
    SetPartides4.pgn         4.799     259.6     336.3
    SetPartides5.pgn         5.240     284.2     335.4
    SetPartides6.pgn         5.181     275.1     332.5
    SetPartides7.pgn         5.288     255.1     331.5
    TOTAL                    5.122     269.8     334.8

Comparacio amb el mode semantic anterior:

    MODE_SEMANTIC: R = 4.925, compressio 668.4 kB/s, descompressio 650.7 kB/s
    MODE_CHESS:   R = 5.122, compressio 269.8 kB/s, descompressio 334.8 kB/s

`MODE_CHESS` es mes lent, pero queda per sobre del minim de 250 kB/s i
comprimeix millor. Per aixo es el mode per defecte.

La verificacio lossless comprimeix, descomprimeix i compara SHA-256 amb
l'original. Tots els fitxers publics tornen identics byte a byte.
