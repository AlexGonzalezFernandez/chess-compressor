# Practica CDI 2025-2026 - compressor PGN

Autor: (posar nom)
Curs: CDI 2025-2026


## Plantejament

La practica demana comprimir sense perdues fitxers PGN (partides
d'escacs) maximitzant la ratio

    R = mida total original / (mida total comprimit + penalitzacio executable)

amb una velocitat minima de 250 kB/s tant comprimint com descomprimint.

Vaig considerar dues aproximacions molt diferents:

La primera, generica: tractar el PGN com una seqüencia de bytes
qualsevol i aplicar-hi compressio d'entropia. Es facil i rapida
d'implementar, i aprofita que el PGN te molta redundancia local (tags
repetits com "[Event ", "Result ", caracters d'espais, digits dels
moviments...) pero no explota que son partides d'escacs.

La segona, especifica: fer un motor d'escacs, generar els moviments
legals a cada posicio i codificar l'index del moviment triat en comptes
del seu text. Com que a cada posicio hi ha 20-40 moviments legals, cada
moviment cap en 5-6 bits, i amb un model adaptatiu al voltant de 3-4
bits, molt per sota dels ~30 bits que ocupa en text. Dona ratios molt
mes altes, pero l'implementacio es llarga (pins, claus, en passant,
enroc, promocions, escac) i en Python pur hi ha dubte sobre si
passaria els 250 kB/s.

Vaig triar implementar primer l'aproximacio generica. Amb aixo ja
compleixo requisits i tinc una base sobre la qual afegir millores
progressivament. El que entrego es aixo: compressor generic, ratio
agregada 3.89 sobre els 7 fitxers publics, velocitats ~390 kB/s.


## Com esta organitzat el codi

Tot esta en un sol fitxer, compress.src. L'enunciat no especifica cap
estructura concreta i un sol fitxer simplifica l'execucio i
l'entrega.

Dins del fitxer les seccions son, per ordre:

- Constants del format (magic number, versio, modes).
- Mode identity: una funcio trivial que retorna el que rep. La vaig fer
  servir durant el desenvolupament per verificar que l'I/O i el
  wrapper funcionessin abans d'afegir compressio real. La deixo al codi
  perque ocupa tres linies i no fa mal.
- Range coder (classes RangeEncoder i RangeDecoder).
- Codificador aritmetic binari bit a bit (ArithEncoder, ArithDecoder).
  Aquest no s'utilitza a la versio final - es la primera versio que
  vaig escriure seguint els apunts i els qüestionaris, abans d'adonar-me
  que en Python pur era massa lent. El deixo al fitxer com a referencia
  i per si en fases futures algun sub-model petit el fa servir.
- Fenwick tree (classe Fenwick) amb les tres operacions que necessito.
- El compressor i descompressor "de veritat", que combinen el range
  coder amb un model d'ordre 2 i els arbres Fenwick.
- L'embolcall que afegeix la capçalera CDI1 i el dispatching per
  mode.
- main(): llegeix el fitxer, mira els primers bytes per decidir si
  comprimir o descomprimir, i escriu la sortida.


## Format del fitxer comprimit

    bytes 0..3   : "CDI1"  (magic number)
    byte  4      : versio del format, ara 1
    byte  5      : mode de compressio
                     0 = identity (copia literal; nomes per debugar)
                     1 = range coder + model ordre-2  <-- l'util
    bytes 6..9   : mida original del fitxer, big-endian
    bytes 10..   : payload, sortida del range coder

El byte de mode i el byte de versio son pensats per si en una fase
posterior afegeixo un altre mode (per exemple, amb parser semantic de
capçaleres) - podria coexistir amb aquest sense canviar el format de
capçalera.

Vaig considerar afegir un simbol EOF dins del stream en comptes dels 4
bytes de mida. Amb EOF caldria ampliar l'alfabet a 257, i aleshores els
arbres Fenwick serien una mica mes cars per simbol (9 iteracions en
comptes de 8) i tot el loop intern mes lent. Gastar 4 bytes al
principi del fitxer surt mes a compte.


## Model estadistic: ordre 2 adaptatiu

Per cada parell de bytes anteriors (b_prev_2, b_prev_1) mantinc un
vector de frequencies dels 256 possibles valors del byte seguent. El
context es el parell, empaquetat en un enter de 16 bits - aixi
m'estalvio fer tuples.

Inicialitzo a 1 les frequencies de tots els simbols (smoothing de
Laplace). Si no ho fes, un simbol que no hagi aparegut encara al
context tindria probabilitat 0, que el range coder no pot codificar.

Despres de cada simbol codificat, n'incremento la frequencia al
context corresponent, i per estalviar memoria els contextos es creen
nomes quan apareixen per primer cop (dict). En els fitxers PGN de test
apareixen uns quants milers de contextos diferents, no els 65k
teorics, aixi que la memoria va bastant be.

Quan el total d'un context passa de 2^24 divideixo totes les
frequencies per 2 (amb minim 1 per mantenir la propietat de
smoothing). El proposit es evitar que el producte `rng * total` del
range coder desbordi els 32 bits.

Vaig provar tambe ordre 1 (context = byte anterior). La ratio baixa a
2.4, perque PGN te molta estructura visible a distancia 2 (tags com
"][", "1.", " e", "Nf",...) que l'ordre 1 no captura. Ordre 3 no
l'he provat: l'espai de contextos ja puja a 16M i segur que no
compensa perque el model necessita molta mes feina per aprendre
frequencies en contextos que poques vegades es repeteixen.


## Fenwick tree

Per cada simbol que codifico necessito fer, dins del context actual,
tres coses:

- prefix(i): suma freq[0..i-1]. El range coder la fa servir per saber
  la posicio del simbol dins del rang acumulat.
- update(i, +1): incrementar freq[i] despres de codificar el simbol.
- find(t): donat un valor t dins del rang total, trobar a quin simbol
  correspon. Aquesta operacio nomes la necessita el descompressor.

Amb una llista normal, update seria O(n) perque caldria actualitzar
tots els prefixos acumulats. Amb un Fenwick tree (arbre indexat binari)
les tres operacions son O(log n), i amb n = 256 surten uns 8 passos.

Ho guardo en un array.array('i', ...) perque es bastant mes rapid que
una list de Python i perque els valors que hi guardo son enters
petits que caben en 32 bits.


## Range coder

El codificador aritmetic clasic (tipus Moffat-Neal-Witten, que es el
que vaig fer servir als qüestionaris) renormalitza bit a bit. La
primera versio que vaig escriure feia servir aquesta aproximacio i no
passava dels 100 kB/s: el while-loop intern s'executava moltissimes
vegades per MB de dades, i cada iteracio te l'overhead tipic d'un
bucle Python.

El range coder es conceptualment equivalent pero renormalitza byte a
byte en comptes de bit a bit. Aixi l'iteracio es executa uns 8 cops
menys i la velocitat passa de 100 kB/s a uns 400 kB/s. La perdua de
compressio respecte al bit-per-bit es inapreciable en la practica
(ordre 0.01%).

Hi ha una complicacio: quan emets un byte, un increment posterior el
pot fer "pujar" en 1 (carry). Per resoldre-ho faig servir un buffer de
bytes pendents: si el byte de mes pes es 0xFF, en comptes de fixar-lo
ajorno l'escriptura i espero a veure si ve el carry. Si ve, els
pendents passen de 0xFF a 0x00 i al byte anterior se li suma 1; si no
ve, els pendents s'escriuen tal qual i el byte anterior queda com
estava.

Un detall practic: la versio canonica (Subbotin) te un cas especial
pel primer byte - si no hi ha carry el primer cop, no s'emet. Vaig
trobar que aquesta optimitzacio em donava bugs subtils d'asimetria
entre encoder i decoder, i la vaig simplificar: l'encoder sempre emet
aquest primer byte (encara que sigui 0x00), i el decoder
incondicionalment el descarta quan s'inicialitza. El cost es un byte
per fitxer, pero la implementacio queda molt mes simple i segura.


## Optimitzacio del loop de descompressio

Amb el codi "net" (amb metodes del Fenwick i del RangeDecoder), la
compressio anava be (~400 kB/s) pero la descompressio es quedava a
uns 245 kB/s, just per sota del llindar de 250.

El motiu: la descompressio fa mes feina per simbol (un find i dos
prefix, contra un sol prefix a la compressio), i cada una d'aquestes
operacions es una crida a metode Python amb el seu cost d'attribute
lookup, creacio de frame, etc.

La solucio va ser "inline" tot el loop intern - copiar el codi dels
metodes directament dins del bucle i extreure els atributs del decoder
a variables locals abans d'entrar-hi. Amb aixo Python fa molts menys
lookups per iteracio i la descompressio pasa a ~385 kB/s. El codi
resultant es una mica mes dens i per aixo esta comentat amb un
pseudocodi equivalent al principi de la funcio.


## Resultats

Mesurat en un MacBook amb Python 3.9:

    fitxer                   original  comprimit   ratio    c kB/s    d kB/s
    SetPartides1.pgn           1.6 MB   455.2 KB   3.665     374.4     385.7
    SetPartides2.pgn           3.7 MB   969.7 KB   3.916     411.9     387.1
    SetPartides3.pgn           3.0 MB   779.8 KB   3.885     403.2     387.8
    SetPartides4.pgn           2.4 MB   651.7 KB   3.765     395.3     385.1
    SetPartides5.pgn           5.4 MB     1.3 MB   3.998     421.8     386.4
    SetPartides6.pgn           4.4 MB     1.1 MB   4.001     413.1     382.6
    SetPartides7.pgn           3.4 MB   931.5 KB   3.791     422.7     386.0
    TOTAL                     23.9 MB     6.2 MB   3.893

L'executable (compress.cdi + compress.src) fa uns 16-26 kB, molt per
sota dels 250 kB, aixi que no hi ha penalitzacio.

R = 3.893. Velocitat sempre per sobre del minim de 250 kB/s.
Verificat amb sha256 que tots els fitxers descomprimits son identics
byte a byte als originals.


## Coses que no he fet pero seria util afegir

No les tinc implementades en aquesta entrega pero les tinc pensades
per si tinc temps abans del lliurament final:

Aprofitar que el fitxer es PGN. Els tags [Key "Value"] tenen molta
estructura fixa: dates en YYYY.MM.DD, hores HH:MM:SS, ELOs de 3-4
digits, Result amb nomes 4 valors ("1-0", "0-1", "1/2-1/2", "*"),
ECO amb una lletra A-E i dos digits, URLs de Lichess amb un prefix
llarg i repetit. Un parser semantic que els codifiqui amb un camp
propi hauria de guanyar bastant sobre la part de capçaleres, que es
gairebe la meitat del fitxer.

Codificar els moviments per index legal. Un motor d'escacs que generi
els moviments legals permetria codificar cada moviment com un index de
5-6 bits, o menys amb un model adaptatiu sobre els indexos. Seria la
via cap a ratios de 6+. L'inconvenient es el volum de codi a escriure
i verificar la velocitat en Python.
