# Tesi RL Traffic Lights Management

## Supervisori: Giuseppe Vizzari

## Partecipanti: Francesco Refolli

## Tema:

- Sperimentazione approcci RL per Traffic Lights Management
- Sviluppo framework per studio, sperimentazione tecniche di RL in un contesto applicativo

## Materiali:

- Sumo: [https://eclipse.dev/sumo/](https://eclipse.dev/sumo/)
- Sumo RL: [https://github.com/LucasAlegre/sumo-rl/](https://github.com/LucasAlegre/sumo-rl/)
- Tesi Romain Michelucci: [https://drive.google.com/file/d/1GsV1NYO7UQdpb6_y8AlnHOwUFQ3V1pox/view?usp=sharing](https://drive.google.com/file/d/1GsV1NYO7UQdpb6_y8AlnHOwUFQ3V1pox/view?usp=sharing)
- Repo github Michelucci: [https://github.com/GameDisplayer/Deep-QLearning-Multi-Agent-Perspective-for-Traffic-Signal-Control](https://github.com/GameDisplayer/Deep-QLearning-Multi-Agent-Perspective-for-Traffic-Signal-Control)
- Gruppo Zotero con riferimenti utili: [https://www.zotero.org/groups/4948401/rl-traffic-lights](https://www.zotero.org/groups/4948401/rl-traffic-lights)

## To Do:

- [ ] Controlla la sezione su “code artificiali” nella tesi di Michelucci (cap. 4.2), eventualmente ipotizza un meccanismo alternativo
- [ ] Stabilizza l’ambiente di esempio, stabilisci degli scenari di test standard (e.g. traffico feriale di punta periferia —> centro, traffico feriale di punta centro —> periferia, traffico festivo, traffico anomalo (sciopero dei mezzi)
- [ ] Implementare PPO
- [ ] Implementa la creazione semi-automatica della collezione di esempi
- [ ] Stabilisci quali sono scenari di addestramento e quali di valutazione
- [ ] Esegui un'ondata di addestramento e valutazione sui modelli:
   - [ ] Fixed Long Cycle (fixed agent)
   - [ ] Fixed Medium Cycle (fixed agent) (Baseline)
   - [ ] Fixed Rapid Cycle (fixed agent)
   - [ ] Q Learning (ql agent)
   - [ ] Deep Q Learning (dqn agent)
   - [ ] Proximal Policy Optimization (ppo agent)
- [ ] Implementa funzioni di osservazione diverse
   - [ ] Adiacent states
   - [ ] Adiacent phases
   - [ ] Adiacent densities
   - [ ] Adiacent queues

# Note su SUMO:

Si usano le seguenti opzioni:

- `junction-taz=true`: SUMO di base non permette di creare "flussi" tra "junctions" (incroci), a meno di non specificare questa opzione, che provoca la creazione di "TAZ" (punti di interesse) implicite per supportare la creazione delle rotte.
- `max-depart-delay=5`: Quando un veicolo viene generato (per un flusso) appare al di fuori della mappa e puo' dover attendere prima di entrare a causa del traffico che si trova all'interno di essa. Quindi puo' succedere che venga generata una quantita' enorme di veicoli in attesa che richiedono di entrare e che non possono essere fatti sparire per magia quando si vuole cambiare "fase" di traffico. Questo puo' essere evitato mettendo una tagliola di $$x$$ secondi ("max-depart-delay") oltre i quali il veicolo sparisce nel nulla prima ancora di intrare in scena. Questo puo' essere desiderabile quando si vogliono simulare i mutamenti del traffico per semplificare la creazione di scenari. E' chiaro che se invece si volesse simulare in modo realistico l'intero carico di veicoli che devono passare in un insieme di incroci ad una certa ora, questa opzione potrebbe compromettere i risultati (a meno di non fissare comunque un valore alto, es 60 sec, per simulare la possibilita' di un automobilista di cambiare strada e passare da un'altra parte).

Sto valutando le seguenti opzioni:

- `lanechange.duration=3` : Cambiare lane durante la simulazione non e' istantaneo ma richiede il numero selezionato di step. Si usa per incrementare il grado di realismo.
- `lateral-resolution=5`: Opzione alternativa a `lanechange.duration` per rendere piu' "complessi" i cambi di corsia, ma e' implementata dividendo la corsia in `5` parti parallele e a livello visuale si vedono i veicoli che si compenetrano.

# Code artificiali

Creare delle code artificali in uscita dalla mappa e' un meccanismo utile per migliare il realismo degli scenari, visto che rispecchia il caso di un sistema di semafori intelligenti che controlla e vede solo un quartiere di una grande citta' trafficata.

## Svolta a destra

Si potrebbe creare in uscita un mini incrocio con molte macchine che svoltano a destra verso il dead end per poter simulare la coda.

## Stop time artificiale

Michelucci creava singolarmente i veicoli per la simulazione (io genero i flows), quindi poteva definire una quantita' di tempo che un veicolo doveva rimanere fermo all'estremita' della lane in uscita.

## Velocita' di arrivo impostata a 0

Se si imposta il parametro `arrivalSpeed="0.00"` nella dichiarazione di un flusso, SUMO produrra' un rallentamento artificiale che impedisce ai veicoli in uscita di defluire al massimo della velocita' e produrra' delle code artificali.

## Segmentazione delle lane in uscita

Si potrebbero creare dei segmenti in uscita verso i dead ends dove la velocita' massima e' molto bassa in modo che siano costretti a rallentare. E' piu' realistico di avere un periodo di stop in uscita secondo me, perche' di base con il traffico rallenti ma non devi per forza stare fermo tot secondi. Devo solo stare attento a come calcolo la capacita' del sistema, perche' questa definisce poi la quantita' di veicoli che butto nelle intersezioni, ma in teoria dovrebbe dipendere solo dalle lanes (quante sono, la velocita' … etc) in ingresso e non da quelle in uscita.

# Scenari

## "Breda"

Uno scenario lineare a due incroci con l'asse principale con 2 corsie per lato sul piano orizzontale e due assi secondari con 1 corsia per lato in verticale. Gli incroci supportano la svolta in tutte le direzioni (tranne l'inversione di marcia) e non hanno una fase separata per la svolta a sinistra.

![](https://res.craft.do/user/full/d7b7d2cb-207e-82b6-9963-2eada2eeca31/doc/28711EF5-4446-475D-8A23-FBEC32918F27/c3ed0caf-9c7f-4b9e-83a5-2d3500b98625)

Assi principali:

- J0 ←> J3

Assi secondari:

- J4 ←> J5
- J6 <→ J7

# Generazione di traffico

## Tipologie base di traffico generabile

- Casual: traffico casuale in tutte le direzioni. Viene implementato lottizzando il tempo della simulazione in slot dove ogni direzione ha la possibilita' di apparire con una probabilita' binomiale (p=0.7).
   - Specifiche: SA, DI
- Stable: traffico stabile
   - Specifiche: SA, AD, DI
- Unstable: traffico instabile con frequente interruzione dagli assi secondari tramite lottizzazione del tempo gestita da una variabile binomiale (p=0.7).
   - Specifiche: SA, AD, DI
- Transition: traffico che inizia come C1  e finisce come C2. E' ottenuto tramite una partizione del tempo in $$[0, \frac {N} {2})$$ e $$[\frac {N} {2}, N)$$. Quindi ci saranno le tipologie "C1→C2", "C2→C1" … etc.

### Sottocategorie

- SA: Indica se la direzione e la sua opposta possono ricevere lo stesso carico di traffico
   - Simmetrico: una direzione e quella sua opposta possono ricevere lo stesso carico di traffico
   - Asimmetrico: una direzione riceve circa il doppio del carico della sua opposta
- AD: Indica in quali direzioni generare traffico
   - Assiale: genera traffico solo lungo gli assi principali e secondari dichiarati. (es Breda: J0<→J3 ma non J0←>J4 … etc)
   - Denso: genera traffico in tutte le direzioni
- DI: Stabilisce quale dei due versi avra' piu' traffico nel caso Asimmetrico
   - Diretto: $$X.ID> Y.ID \rightarrow traffic(X) \geq 2 * traffic(Y)$$
   - Inverso: $$X.ID <Y.ID \rightarrow traffic(X)  \geq 2 * traffic(Y)$$
- Livello di traffico: espresso come numero in virgola mobile $$[0.0, 1.0]$$, e' la percentuale di veicoli rispetto alla capacita' ideale della strada da generare come traffico
   - Zero (0.0)
   - Basso (0.05)
   - Medio (0.2)
   - Alto (0.5)
   - Molto Alto (0.8)
   - Ridicolo (1.0)

   Se la categoria DA e' disponibile, allora i livelli di traffico sono espressi come moduli direzionali:

   - Main to Main
   - Main to Side
   - Side to Main
   - Side to Side

   dove Main e Side si riferiscono a se il nodo di partenza/destinazione fa parte di un asse principale o secondario.

## Lottizzazione del traffico

### Normalita'

Tutto in ordine: chi prende il treno prende il treno, chi prende i mezzi prende i mezzi, chi prende la macchina prende la macchina. Non sono previsti scossoni. Il traffico feriale ha una maggior impronta di pendolarismo per studio/lavoro, quindi sono maggiormente interessati gli assi principali. Al contrario nel traffico festivo le persone che non si recano per "dovere" ma per "piacere" si sposteranno anche in destinazioni minori. In particolare nel traffico festivo di solito il traffico pendolare e' ridotto al minimo ed eventualmente i fuorisede (specie quelli sulle medie distanze, es Mi <-> PC) sono tornati a casa nei giorni precedenti (di solito il venerdi' sera).

| ID    | Descrizione                                            | Inquadramento                                                 |
| ----- | ------------------------------------------------------ | ------------------------------------------------------------- |
| N1    | Traffico feriale/festivo in ore di morbida             | Casuale Simmetrico Basso                                      |
| N2    | Traffico feriale in ore di punta (centro <- periferia) | Stabile Asimmetrico Diretto Denso <Medio,Basso,Basso,Basso>   |
| N3    | Traffico feriale in ore di punta (centro -> periferia) | Stabile Asimmetrico Inverso Denso <Medio,Basso,Basso,Basso>   |
| N4    | Traffico festivo in ore di punta (centro <- periferia) | Instabile Asimmetrico Diretto Denso <Medio,Basso,Basso,Basso> |
| N5    | Traffico festivo in ore di punta (centro -> periferia) | Instabile Asimmetrico Inverso Denso <Medio,Basso,Basso,Basso> |
| N1-N2 | Traffico feriale mattiniero andante                    | Transizione >N1>>N2>                                          |
| N1-N3 | Traffico feriale serale andante                        | Transizione >N1>>N3>                                          |
| N2-N1 | Traffico feriale mattiniero calante                    | Transizione >N2>>N1>                                          |
| N3-N1 | Traffico feriale serale calante                        | Transizione >N3>>N1>                                          |
| N1-N4 | Traffico festivo mattiniero andante                    | Transizione >N1>>N4>                                          |
| N1-N5 | Traffico festivo serale andante                        | Transizione >N1>>N5>                                          |
| N4-N1 | Traffico festivo mattiniero calante                    | Transizione >N4>>N1>                                          |
| N5-N1 | Traffico festivo serale calante                        | Transizione >N5>>N1>                                          |

### Sciopero treni

Le persone che normalmente prendono il mezzo di trasporto migliore per spostarsi sulle medie-lunghe distanze, oggi si sposteranno in macchina. Si determina un aumento del traffico sull'asse principale a tutte le ore e un aumento degli spostamenti nelle ore di morbida per tentare di sfuggire alla congestione prevista. Allo stesso modo anche gli automobilisti pendolari proveranno itinerari o orari differenti, avendo piu' traffico in tutte le direzioni anche nelle ore di morbida. Questo tipo di sciopero di solito non impatta in modo rilevante sul traffico festivo in quanto i fuorisede o i turisti preferiscono anticipare/posticipare la partenza o affidarsi al caso sperando che il loro treno non sia cancellato.

| ID      | Descrizione                                                                             | Inquadramento                                              |
| ------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| ST1     | Traffico feriale in ore di morbida nei giorni di sciopero dei treni                     | Casuale Simmetrico Medio                                   |
| ST2     | Traffico feriale in ore di punta (centro <- periferia) nei giorni di sciopero dei treni | Stabile Asimmetrico Diretto Denso <Alto,Basso,Basso,Basso> |
| ST3     | Traffico feriale in ore di punta (centro -> periferia) nei giorni di sciopero dei treni | Stabile Asimmetrico Inverso Denso <Alto,Basso,Basso,Basso> |
| ST1-ST2 | Traffico feriale mattiniero andante nei giorni di sciopero dei treni                    | Transizione >ST1>>ST2>                                     |
| ST1-ST3 | Traffico feriale serale andante nei giorni di sciopero dei treni                        | Transizione >ST1>>ST3>                                     |
| ST2-ST1 | Traffico feriale mattiniero calante nei giorni di sciopero dei treni                    | Transizione >ST2>>ST1>                                     |
| ST3-ST1 | Traffico feriale serale calante nei giorni di sciopero dei treni                        | Transizione >ST3>>ST1>                                     |

### Sciopero TPL

Valgono le considerazioni sullo sciopero dei treni, con alcune differenze. Le persone che normalmente prendono i mezzi del trasporto pubblico locale, oggi si sposteranno in macchina. Questo comprende non solo chi viene in treno, ma anche chi risiede gia' in provincia o in citta'. Quindi si avra' molto piu' traffico da e per direzioni minori.

| ID          | Descrizione                                                                                                 | Inquadramento                                              |
| ----------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| STPL1       | Traffico feriale in ore di morbida nei giorni di sciopero del trasporto pubblico locale                     | Casuale Simmetrico Medio                                   |
| STPL2       | Traffico feriale in ore di punta (centro <- periferia) nei giorni di sciopero del trasporto pubblico locale | Stabile Asimmetrico Diretto Denso <Alto,Medio,Medio,Medio> |
| STPL3       | Traffico feriale in ore di punta (centro -> periferia) nei giorni di sciopero del trasporto pubblico locale | Stabile Asimmetrico Inverso Denso <Alto,Medio,Medio,Medio> |
| STPL1-STPL2 | Traffico feriale mattiniero andante nei giorni di sciopero del trasporto pubblico locale                    | Transizione >STPL1>>STPL2>                                 |
| STPL1-STPL3 | Traffico feriale serale andante nei giorni di sciopero del trasporto pubblico locale                        | Transizione >STPL1>>STPL3>                                 |
| STPL2-STPL1 | Traffico feriale mattiniero calante nei giorni di sciopero del trasporto pubblico locale                    | Transizione >STPL2>>STPL1>                                 |
| STPL3-STPL1 | Traffico feriale serale calante nei giorni di sciopero del trasporto pubblico locale                        | Transizione >STPL3>>STPL1>                                 |

### Cantiere del Tram

La viabilita' sulle strade principali (interessate dai lavori per la messa a terra del progetto tramviario) e' modificata in modo da ridurre drasticamente la quantita' di veicoli che possono percorrerle. Di conseguenza un numero importante di automobilisti e' costretto a prendere deviazioni (sulle vie secondarie) per scavalcare i cantieri. I cantieri, al contrario degli scioperi, impattano la viabilita' anche nei giorni festivi (specie quando ci sono grossi eventi come concerti e competizioni sportive).

| ID      | Descrizione                                                                             | Inquadramento                                                 |
| ------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| CT1     | Traffico feriale/festivo in ore di morbida nei giorni col cantiere del tram             | Instabile Simmetrico Denso <Basso,Basso,Basso,Basso>          |
| CT2     | Traffico feriale in ore di punta (centro <- periferia) nei giorni col cantiere del tram | Stabile Asimmetrico Diretto Denso <Basso,Medio,Medio,Basso>   |
| CT3     | Traffico feriale in ore di punta (centro -> periferia) nei giorni col cantiere del tram | Stabile Asimmetrico Inverso Denso <Basso,Medio,Medio,Basso>   |
| CT4     | Traffico festivo in ore di punta (centro <- periferia) nei giorni col cantiere del tram | Instabile Asimmetrico Diretto Denso <Basso,Medio,Medio,Basso> |
| CT5     | Traffico festivo in ore di punta (centro -> periferia) nei giorni col cantiere del tram | Instabile Asimmetrico Inverso Denso <Basso,Medio,Medio,Basso> |
| CT1-CT2 | Traffico feriale mattiniero andante nei giorni col cantiere del tram                    | Transizione >CT1>>CT2>                                        |
| CT1-CT3 | Traffico feriale serale andante nei giorni col cantiere del tram                        | Transizione >CT1>>CT3>                                        |
| CT2-CT1 | Traffico feriale mattiniero calante nei giorni col cantiere del tram                    | Transizione >CT2>>CT1>                                        |
| CT3-CT1 | Traffico feriale serale calante nei giorni col cantiere del tram                        | Transizione >CT3>>CT1>                                        |
| CT1-CT4 | Traffico festivo mattiniero andante nei giorni col cantiere del tram                    | Transizione >CT1>>CT4>                                        |
| CT1-CT5 | Traffico festivo serale andante nei giorni col cantiere del tram                        | Transizione >CT1>>CT5>                                        |
| CT4-CT1 | Traffico festivo mattiniero calante nei giorni col cantiere del tram                    | Transizione >CT4>>CT1>                                        |
| CT5-CT1 | Traffico festivo serale calante nei giorni col cantiere del tram                        | Transizione >CT5>>CT1>                                        |

## Datasets

### 0

Prospetto:
- Training: Normalita'
- Evaluation: 80% Normalita' + 10% Anormale + 10% Intenso

Realizzazione:
```bash
mkdir -p datasets/0
rm -rf datasets/0/*
rm -rf training evaluation
python -m tools.mengele -r traffic-registry.yml -o training \
  1,£,N1,N2,N1,N3,N1 \
  1,£,N1,N4,N1,N5,N1
python -m tools.mengele -r traffic-registry.yml -o evaluation \
  1,£,N1,N2,N1,N3,N1 \
  1,£,N1,N4,N1,N5,N1 \
  1,£,N1,STPL2,N1,STPL3,N1 \
  1,£,N1,CT2,N1,CT3,N1
mv training evaluation datasets/0
```

### 1

Prospetto:
- Training: Normalita' + 10% Anormale
- Evaluation: 80% Normalita' + 10% Anormale + 10% Intenso

Realizzazione:
```bash
mkdir -p datasets/1
rm -rf datasets/1/*
rm -rf training evaluation
python -m tools.mengele -r traffic-registry.yml -o training \
  1,£,N1,N2,N1,N3,N1 \
  1,£,N1,N4,N1,N5,N1 \
  1,£,N1,ST2,N1,ST3,N1 \
  1,£,N1,CT4,N1,CT5,N1
python -m tools.mengele -r traffic-registry.yml -o evaluation \
  1,£,N1,N2,N1,N3,N1 \
  1,£,N1,N4,N1,N5,N1 \
  1,£,N1,STPL2,N1,STPL3,N1 \
  1,£,N1,CT2,N1,CT3,N1
mv training evaluation datasets/1
```

### 2

Prospetto:
- Training: Frankestein con tutto dentro
- Evaluation: 80% Normalita' + 10% Anormale + 10% Intenso

Realizzazione:
```bash
mkdir -p datasets/2
rm -rf datasets/2/*
rm -rf training evaluation
python -m tools.mengele -r traffic-registry.yml -o training \
  1,400000,£,*,~
python -m tools.mengele -r traffic-registry.yml -o evaluation \
  1,£,N1,N2,N1,N3,N1 \
  1,£,N1,N4,N1,N5,N1 \
  1,£,N1,STPL2,N1,STPL3,N1 \
  1,£,N1,CT2,N1,CT3,N1
mv training evaluation datasets/2
```

## Funzioni di osservazione

- default: vedo
  - la mia fase
  - se ho tenuto il verde per molto tempo
  - la lunghezza delle code in ingresso
  - la densita' delle corsie in ingresso
- sv: vedo
  - Il mio `default`
  - Il `default` dei miei vicini
- svp: vedo
  - Il mio `default`
  - La fase dei miei vicini
- svd: vedo
  - Il mio `default`
  - la densita' delle corsie in ingresso ai miei vicini
- svq: vedo
  - Il mio `default`
  - la lunghezza delle code in ingresso ai miei vicini

## Funzioni di reward

- dwt: Diff Waiting Times
- as: Average Speeds
- ql: Average Queue Lengths
- p: Pressure
- svdwt: Diff Waiting Times (mia + quella dei vicini)
- svas: Average Speeds (mia + quella dei vicini)
- svql: Average Queue Lengths (mia + quella dei vicini)
- svp: Pressure (mia + quella dei vicini)

## Sistemi self adaptive

### 0

Il training fornisce la baseline delle metriche (`mean_waiting_time`, `mean_speed`) di cui ci si segna media e la deviazione standard.
Ogni tot secondi (i.e. 10000), calcolo la media degli ultimi tot secondi (i.e. 10000) rispetto alle metriche e verifico se e' necessario un riaddestramento.
Il riaddestramento e' necessario se la media campionaria si discosta di piu' del 5 percento dalla media consolidata.
A quel punto gli agenti vengono riaddestrati per tot secondi (i.e. 10000) e quando l'addestramento e' terminato blocco il controllo per tot secondi (i.e. 30000).

## Domande di Ricerca

### 1) Curriculum learning vs Monolitico

### 2) C'e' veramente bisogno di usare reti neurali per il RL?

### 3) Sistema self-adaptive per potenziare i semafori

### 4) Sistema ad agenti isolati vs sistema multi-agente in cui si condividono risorse e premi
