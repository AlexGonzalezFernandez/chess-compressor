# Notes i decisions - practica CDI

Aquest fitxer resumeix les decisions de disseny del compressor PGN.


## Requisits

La practica demana maximitzar:

    R = suma_mides_originals / (suma_mides_comprimit + max(0, mida_exe - 250KB))

Restriccions importants:

- Python obligatori.
- Sense llibreries de compressio ja fetes (`zlib`, `bz2`, `lzma`, etc.).
- Velocitat minima de 250 kB/s comprimint i descomprimint.
- Compressio sense perdues: el fitxer descomprimit ha de ser identic byte
  a byte a l'original.


## Estrategia per fases

Vaig plantejar el projecte per fases, sempre mantenint una versio lossless:

- Fase 1: infraestructura, executable `compress.cdi` i mode identity.
- Fase 2: compressor generic d'entropia.
- Fase 3: codificacio semantica de capcaleres PGN.
- Fase 4: motor d'escacs per codificar moviments SAN.

Aixo permetia aturar-se en qualsevol fase amb una solucio funcional.


## Executable

L'enunciat nomes dona:

    compress.cdi infile outfile

No hi ha flag separat per descomprimir. Per aixo el programa detecta el
format mirant els primers bytes:

- si comenca per `CDI1`, descomprimeix
- si no, comprimeix

`compress.cdi` es un shell script petit que crida `python3 compress.src`.
Tot el codi esta a `compress.src` per simplificar l'entrega.


## Modes de compressio

El format guarda un byte de mode despres del magic `CDI1`.

Modes actuals:

    0 = identity
    1 = compressor generic ordre 2
    2 = split capcaleres/movetext
    3 = semantic tags + movetext literal
    4 = semantic tags + moviments SAN amb motor d'escacs

El mode per defecte actual es:

    MODE_CHESS = 4


## Fase 2 - compressor generic

La base es un range coder de 32 bits amb model adaptatiu d'ordre 2.

Decisions:

- Context = parell dels dos bytes anteriors.
- Frequencies inicials a 1 per evitar probabilitats zero.
- Contextos creats lazy en un `dict`.
- Frequencies guardades en Fenwick trees sobre `array.array('i')`.
- Reescalat quan el total d'un context es fa massa gran.

Vaig provar un codificador aritmetic bit a bit, pero era massa lent en
Python. El range coder byte-oriented va ser molt mes rapid i va permetre
passar el limit de velocitat.

Resultat de fase 2:

    R = 3.893


## Fase 3 - capcaleres semantiques

Els PGN de Lichess tenen capcaleres molt regulars. Es va separar cada
partida en:

- bloc de tags
- movetext

Les capcaleres es codifiquen per tipus:

- `Result`, `Termination`, `Title`: codis petits
- `UTCDate`: data empaquetada
- `UTCTime`: segons del dia
- ELOs: enters de 16 bits
- `ECO`: lletra i numero empaquetats
- `TimeControl`: varints
- `Site`: prefix Lichess implicit
- `Event`: casos comuns i tornejos/swiss
- jugadors i obertures: diccionaris intra-fitxer

Si algun camp no encaixa, es guarda literal. Aixi el mode continua sent
lossless.

Tambe es va provar codificar els comentaris `{ [%eval X] }` en binari,
pero empitjorava la ratio: el range coder ja aprenia molt be el patro de
text i els valors binaris eren menys predictibles.

Resultat de fase 3:

    R = 4.828


## Fase 4 - motor d'escacs

Objectiu: substituir moviments SAN com `Nf3`, `cxd4` o `O-O` per un index
de moviment en la posicio actual.

Implementacio:

- Representacio de posicio amb mailbox 0x88.
- Generacio de moviments pseudo-legals per peca.
- Suport d'en passant, enroc i promocions.
- Parser SAN per peca, desti, promocio, captura i desambiguacio.
- Comprovacio de legalitat fent make-move i comprovant si el rei queda
  atacat.

La primera versio indexava contra la llista legal completa i generava SAN
per tots els candidats. Funcionava i comprimia mes, pero era massa lenta:

    ratio 5.214, compressio 44.3 kB/s, descompressio 107.6 kB/s

Despres es van provar optimitzacions:

- Guardar `+` i `#` com a sufix en comptes de recalcular jaque/mat per
  cada candidat: pujava a uns 75 kB/s.
- Fer make/unmake en lloc de clonar el tauler: guany petit.
- Parsejar el SAN directament per evitar generar SAN de tots els
  candidats: millorava molt, pero encara no era suficient.

La versio final indexa contra la llista pseudo-legal i nomes comprova la
legalitat del moviment seleccionat. Per poder reconstruir exactament el
SAN original, guarda metadata compacta:

- desambiguacio de fitxer/rang
- sufix `+` o `#`
- anotacions `!`, `?`, `!?`, `?!`

Els numeros de jugada, espais, resultats i comentaris es guarden literal.


## Resultat final

Resultats del mode final `MODE_CHESS` sobre els 7 fitxers publics:

    fitxer                   ratio    c kB/s    d kB/s
    SetPartides1.pgn         4.797     254.3     345.1
    SetPartides2.pgn         5.167     269.6     328.8
    SetPartides3.pgn         5.049     273.3     342.0
    SetPartides4.pgn         4.799     259.6     336.3
    SetPartides5.pgn         5.240     284.2     335.4
    SetPartides6.pgn         5.181     275.1     332.5
    SetPartides7.pgn         5.288     255.1     331.5
    TOTAL                    5.122     269.8     334.8

Comparacio:

    MODE_SEMANTIC: R = 4.925
    MODE_CHESS:   R = 5.122

`MODE_CHESS` es queda com a mode per defecte perque millora la ratio i
encara passa el minim de 250 kB/s. El pitjor fitxer queda a 254.3 kB/s
comprimint.


## Punts pendents

- Verificar en un Linux de la FIB, que es l'entorn real de correccio.
- Netejar codi antic no usat si sobra temps.
- Convertir `Document.md` a PDF si l'entrega ho exigeix.
