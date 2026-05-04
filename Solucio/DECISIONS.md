# Notes i decisions - practica CDI (compressio PGN)

Apunts que em deixo per quan hi torni. Mes en pla llibreta que document oficial.


## Que demana la practica

Maximitzar R = suma_mides_originals / (suma_mides_comprimit + max(0, mida_exe - 250KB))
sobre els 7 fitxers publics i un set privat similar.

Puntuacio:
- R <= 3 -> nota 1
- R >= 6 -> nota 7.5
- entre mig, interpolacio lineal
- el 25% restant depen del ranking de la classe

Velocitat minima: 250 kB/s tant comprimint com descomprimint.

Llenguatge obligat: Python. No es poden fer servir llibreries de compressio
ja fetes (zlib, bz2, lzma...). La llibreria estandard normal (sys, os,
struct, array) si que es pot.


## Com ho he plantejat

Anar per fases, verificant lossless a cada pas. Aixi, si em quedo a mig
cami, el que hi ha ja funciona.

- Fase 1: parser PGN minim i executable "identity" (copia literal amb magic
  number). Nomes per tenir la infraestructura muntada.
- Fase 2: codificador d'entropia generic, sense entendre res del PGN.
- Fase 3: explotar que son partides d'escacs (capçaleres estructurades,
  moviments en SAN). Pendent.
- Fase 4: motor d'escacs i codificar per index de moviment legal.
  Nomes si em queda temps.


## L'executable

L'enunciat diu:

    compress.cdi infile outfile

No hi ha flag per descomprimir. L'he deixat de manera que detecta sol
si li passen un fitxer ja comprimit (mirant els 4 bytes inicials: si son
"CDI1", descomprimeix; si no, comprimeix). Aixi la mateixa comanda
serveix per les dues coses.

`compress.src` conte tot el codi Python. `compress.cdi` es un shell script
d'una linia que fa `python3 compress.src "$@"`. Vaig triar deixar-ho tot
en un sol fitxer per simplificar l'entrega.


## Que fa el codi actualment (fase 2)

Compressor generic amb dos components:

1. Un model estadistic adaptatiu d'ordre 2. El context es el parell dels
   dos bytes anteriors (0..65535 possibles). Per a cada context tenim un
   arbre Fenwick amb les frequencies dels 256 simbols. Inicialitzacio a 1
   per tot (Laplace). Quan el total d'un context arriba a 2^24 es divideix
   a la meitat per evitar desbordament.

   Els contextos es creen nomes quan apareixen (dict). En els PGN reals
   surten uns pocs milers dels 65k possibles.

2. Un range coder de 32 bits, byte-oriented. Inicialment vaig provar un
   codificador aritmetic binari (bit a bit) com el dels qüestionaris,
   pero en Python pur no passava dels 100 kB/s perque la renormalitzacio
   bit a bit fa milions d'iteracions per MB. El range coder renormalitza
   emetent bytes sencers, i amb aixo ja vaig per sobre de 350 kB/s.

   Detall: la variant canonica de Subbotin te un cas especial pel primer
   byte (si no hi ha carry no l'emet). Ho vaig simplificar perque sempre
   emeti el primer byte (encara que sigui 0), i el decoder el descarta.
   Gasta 1 byte per fitxer pero la inicialitzacio queda trivial.

3. El Fenwick tree esta sobre `array.array('i', ...)` i al loop de
   descompressio tot esta "inline", sense crides a metodes, perque aixi
   passo de 245 kB/s a ~385 kB/s. Menys llegible pero necessari per
   complir el requisit de velocitat.

L'ArithEncoder/ArithDecoder bit a bit el vaig deixar al fitxer encara que
ja no es fa servir. No molesta, es curt, i pot servir com a referencia
o per si algun sub-model de la fase 4 l'acaba necessitant.


## Format del fitxer comprimit

    bytes 0..3   : "CDI1"   (magic number)
    byte  4      : versio del format (1)
    byte  5      : mode de compressio
                      0 = identity (copia literal, usat nomes per debug)
                      1 = range coder + model ordre-2 (el que fem servir ara)
    bytes 6..9   : mida original del fitxer en big-endian
    bytes 10..   : payload (el stream que treu el range coder)

Tenir byte de versio i de mode em sembla barat i permet afegir mes modes
a les fases seguents sense trencar els fitxers que ja hi hagi.


## Resultats (maig 2026)

```
fitxer                   original  comprimit   ratio    c kB/s    d kB/s  ok
SetPartides1.pgn           1.6 MB   455.2 KB   3.665     374.4     385.7  ok
SetPartides2.pgn           3.7 MB   969.7 KB   3.916     411.9     387.1  ok
SetPartides3.pgn           3.0 MB   779.8 KB   3.885     403.2     387.8  ok
SetPartides4.pgn           2.4 MB   651.7 KB   3.765     395.3     385.1  ok
SetPartides5.pgn           5.4 MB     1.3 MB   3.998     421.8     386.4  ok
SetPartides6.pgn           4.4 MB     1.1 MB   4.001     413.1     382.6  ok
SetPartides7.pgn           3.4 MB   931.5 KB   3.791     422.7     386.0  ok
TOTAL                     23.9 MB     6.2 MB   3.893
```

Executable (compress.cdi + compress.src): ~26 kB, per sota dels 250 KB,
o sigui sense penalitzacio.

R = 3.89. Amb Rmin=3 i Rmax=6 (el cas mes probable) surt nota ~2.9/7.5
en el 75% que depen de la ratio. Justet. Fer la fase 3 deuria portar
R cap a 4.5-5.


## Que queda per fer

- Fase 3: parser semantic de capçaleres i tokenitzar el movetext.
  Els tags [Key "Value"] son gairebe la meitat del fitxer i tenen
  molta estructura que el model ordre-2 no aprofita prou:
    - Dates en format YYYY.MM.DD, podrien anar a 3 enters.
    - Hores HH:MM:SS, idem.
    - ELOs de 3-4 xifres, 12 bits n'hi ha de sobra.
    - Result nomes te 4 valors possibles, 2 bits.
    - ECO es una lletra A-E i dos digits, un byte.
    - URLs de lichess tenen un prefix comu molt llarg.
    - Els jugadors i obertures es repeteixen dins d'un mateix fitxer,
      val la pena un diccionari intra-fitxer.
  I el movetext es comprimeix millor tokenitzant (Nf3, e4, O-O) que
  byte a byte.

- Fase 4: motor d'escacs. Generar moviments legals a cada posicio
  i codificar l'index. Es el que dona ratios altes de veritat (6+),
  pero es molta feina: pins, claus, en passant, enroc, promocions,
  escac... En Python pur i amb el limit de velocitat es complicat.
  Potser fer-ho parcial, nomes per algunes pieces?

- Fase 5: escriure el Document.pdf de veritat (ara hi ha un Document.md
  d'esborrany), netejar el codi, afegir exemples al Readme.


## Coses que no fare

- No fer-ho mes sofisticat que ordre 2 en el model generic. Mixing de
  contextos tipus PAQ seria massa lent en Python.
- No suportar comentaris ni variacions PGN ({...} (...) $n). Els fitxers
  de test no en tenen, ho he comprovat. Si apareguessin, el parser no
  es trenca: el codi actual tracta tot el fitxer com a bytes opacs.
- No implementar cap comanda separada de descompressio. La deteccio
  automatica em sembla mes elegant que afegir un flag.


## Com tornar-hi

1. Llegir aixo.
2. Mirar TODO.md per veure on estava.
3. Correr `python3 test_lossless.py` per confirmar que tot encara funciona.
4. Si es la fase 3: ja tinc la infraestructura per afegir un mode nou al
   MODE_REGISTRY. Decidir si separo headers i movetext en dos streams
   dins del mateix fitxer (probablement si).


---

## Fase 3 (feta)

Plantejament per sub-fases, cadascuna amb verificacio lossless abans de
continuar.

### 3a - Separar streams de capçaleres i movetext

Els tags son ~40% del fitxer i tenen una distribucio de bytes molt
diferent dels moviments SAN. Separar-los en dos streams que es comprimeixen
cada un pel seu compte permet que el model ordre-2 s'especialitzi millor
en cada distribucio.

Format del payload en mode SPLIT:

    byte  0         : flag (0x00 = fallback generic, 0x01 = split)
    bytes 1..4      : longitud del stream de capçaleres comprimit
    bytes 5..       : stream capçaleres comprimit + stream movetext comprimit

El parser aprofita que el format PGN de Lichess es molt regular: separador
\n\n entre tags i movetext d'una mateixa partida i entre partides, i el
fitxer acaba amb "resultat\n". Els 7 fitxers de test segueixen aquesta
convencio. Si trobem un fitxer no canonic (per exemple amb \r\n) fem
fallback al mode generic.

Guany: R 3.893 -> 4.041.

### 3b - Codificacio semantica dels tags

Els fitxers nomes tenen 17 tags diferents, en un ordre canonic (amb
variants per opcionals). Per cada partida emeto:
  1. Un byte de flags amb 4 bits que diuen quins tags opcionals
     (WhiteRatingDiff, BlackRatingDiff, WhiteTitle, BlackTitle) hi son.
  2. Els valors dels tags en ordre canonic, cadascun amb una codificacio
     especifica al seu tipus:
       - Result, Termination, Title: 1 byte marker
       - UTCDate: 3 bytes packed (year-1900 | month | day)
       - UTCTime: 3 bytes com segons del dia
       - ELOs: 2 bytes uint16
       - ECO: 2 bytes packed (A-E × 100 + 0-99)
       - TimeControl: 2 varints
       - Site: prefix "https://lichess.org/" + 8 chars base62
       - Event: 3 valors curts comuns (Blitz/Classical/Bullet game) + 2
         variants tournament/swiss amb id de 8 chars
       - RatingDiffs: zigzag varint (signed)
       - White/Black/Opening: strings per resoldre a la 3c

Cada tag te un marker per si el valor no encaixa al format esperat, en
aquest cas faig fallback a string pla. Aixi el lossless no trenca mai.

Guany acumulat: R 4.041 -> 4.566.

### 3c - Diccionari intra-fitxer per jugadors i obertures

Dins d'un mateix fitxer els jugadors i les obertures es repeteixen
bastant (factor ~3-6x). Al emet un string, si ja l'hem vist emetem
\x00 + index varint; si es nou, \x01 + longitud varint + bytes, i
l'afegim al diccionari. White i Black comparteixen diccionari perque un
mateix usuari juga amb les dues pieces. Opening te el seu propi.

Guany acumulat: R 4.566 -> 4.828.

### 3d - Movetext: eval binari (descartat)

Pensava que comprimir els ~15% de bytes dels comentaris
`{ [%eval X] }` a representacio binaria (1 byte de marker + valor
packed) seria un guany gran. Els vaig implementar, pero el resultat va
ser sorprenent: empitjorava lleugerament la ratio.

Motius:
  - El range coder aprenia perfectament el patro literal `{ [%eval `
    (10 bytes repetits milers de cops) i el comprimia quasi a res. Els
    bytes del valor decimal (0.36, 1.25, etc.) tambe son prou regulars
    per un model ordre-2.
  - Canviar-ho per bytes binaris feia que els bytes fossin mes
    arbitraris i menys compresibles.
  - A mes, els bytes del valor binari podien coincidir amb el byte
    sentinella entre movetexts, que em forçava a framing amb varints de
    longitud, que afegia overhead.

Conclusio: deixo els evals com a text i confio en el RC.


## Estat actual (fase 3 acabada)

R agregat: 4.828
Velocitats: ~500 kB/s compressio, ~550 kB/s descompressio.
Lossless: verificat amb sha256 sobre els 7 fitxers.
Executable: 36.6 KB (cap penalitzacio per mida).

Nota estimada: amb Rmin=3 Rmax=6 (cas probable), nota ~4.96/7.5 sobre
el 75% de la practica. Sobre 10, uns 5.0 nomes amb la ratio (falta el
25% del ranking).

### Que queda

- Fase 4 (motor d'escacs, index de moviments legals). Es la unica via
  per pujar R cap a 6+. Molta feina i risc de no passar el limit de
  velocitat en Python pur.
- Fase 5: Document.pdf final, netejar codi, verificar a la FIB.
