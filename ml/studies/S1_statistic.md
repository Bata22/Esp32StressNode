# S1 – Statistička analiza bez ML-a

Skripta: `ml/s1_statistics.py` · rezultati: `ml/results/s1/`

## Pitanje
Šta signali pilota pokazuju sami po sebi, bez modela, i kako se taj odziv
poredi sa odzivom 15 ispitanika iz WESAD-a?

## Hipoteze
Zapisane 22.10.2026, pre pokretanja skripte. Nisu slepe: formulisane su
posle prve analize pilota (19.10.), u kojoj je rezultat nosila temperatura.

- **H1.1** Temperatura u pilotu ima veliki pad pod stresom (|d| > 0,8), ali
  se efekat bitno smanjuje kad se ukloni trend iz baseline faze (deo je drift).
- **H1.2** EDA (GSR) u pilotu ima mali efekat (|d| < 0,5) i nalazi se ispod
  raspona WESAD ispitanika.
- **H1.3** HR sa čvora nema smislen efekat (|d| < 0,5).
- **H1.4** Jednostavan prag na temperaturi, bez ML-a, daje AUC u granicama
  ±0,05 od najboljeg modela (XGBoost 0,834).
- **H1.5** p-vrednosti na nivou prozora od 5 s su višestruko manje od
  p-vrednosti na nivou minutnih proseka (prozori nisu nezavisni).

## Šta bi oborilo hipoteze
- H1.1: temperaturni efekat ostaje isti ili veći posle uklanjanja trenda.
- H1.2: EDA u pilotu ima |d| u rasponu WESAD ispitanika.
- H1.4: prag na temperaturi daje AUC znatno niži od modela, što bi značilo
  da modeli koriste i druge signale.

## Metod
Faze po oznakama: baseline 10 min 1 s, stres 5 min 35 s, oporavak 10 min 33 s.
Cohen's d i Mann–Whitney porede celu baseline fazu sa stresom. AUC i detektori
koriste baseline bez prve 2 min (kalibracija), isti skup na kom se ocenjuju modeli.

| Metod | Zašto baš ovaj |
|---|---|
| Srednja vrednost, SD, medijana, IQR | Opis faza. Medijana i IQR zbog ekstremnih vrednosti HR-a. |
| Cohen's d = (stres − baseline) / zajednička SD | Veličina promene u jedinicama normalnog kolebanja. Ne zavisi od broja prozora, pa se poredi sa WESAD-om. |
| d posle uklanjanja trenda (stres i oporavak) | Linearni trend baseline faze produži se kroz stres i oporavak; meri se odstupanje od njega u SD reziduala. Ako je promena samo drift, odstupanje je blizu 0 u obe faze. Linearni trend je gruba pretpostavka, pa je ovo analiza osetljivosti. |
| Minutni proseci | Vremenski tok temperature i GSR-a, da se vidi kad promena počinje i kad prolazi. |
| Mann–Whitney na prozorima i na minutnim prosecima | Pokazuje koliko nepoštovanje nezavisnosti prozora umanjuje p-vrednosti. Za zaključke važi minutni nivo. |
| AUC jednog signala | Detektor bez ML-a. Smer je zadat unapred iz fiziologije (HR↑, EDA↑, temperatura↓), ne izabran po rezultatu. |
| Detektor sa pragom z < −2 na temperaturi | Konvencionalni prag od 2 SD, isto pravilo alarma (3 uzastopna prozora) kao kod modela. |
| Spearman korelacija | Da li signali menjaju zajedno, kao kod simpatičke aktivacije. Računa se na baseline + stres, isto kao na WESAD-u. |
| Cohen's d po WESAD ispitaniku | Raspon odziva kod 15 ljudi i koliko je smer odziva dosledan. |

GSR je sirovi ADC. Smer u odnosu na provodljivost kože nije potvrđen. U tabeli i u
`pilot_effects.csv` d je za sirovi ADC (pozitivno = ADC raste), a AUC je u konvenciji
proizvođača (manji ADC = veća provodljivost). Na slici puni romb za GSR je u
konvenciji proizvođača, a prazan u obrnutom smeru.

## Rezultat
Izvor: `pilot_effects.csv`, `pilot_minute_means.csv`, `pilot_correlations.csv`,
`wesad_effects_per_subject.csv`, `detectors_pilot.csv`, slika `s1_effect_sizes.png`.

| Signal | d pilot | d posle trenda: stres / oporavak | WESAD d (min / medijana / max) | WESAD: raste kod | AUC jednog signala |
|---|---|---|---|---|---|
| HR | 0,03 | 0,23 / 0,80 | 0,28 / 1,45 / 3,95 | 15 od 15 | 0,53 |
| GSR nivo (sirovi ADC) | +1,23 | 3,49 / 6,13 | −1,55 / 5,45 / 14,37 | 14 od 15 | 0,13 (0,87 ako veći ADC = stres) |
| GSR varijabilnost | 0,28 | −0,47 / −1,91 | 0,23 / 1,57 / 2,20 | 15 od 15 | 0,50 |
| Temperatura | −1,82 | 0,25 / 7,49 | −8,15 / −2,95 / 5,83 | 3 od 15 | 0,84 |
| Nagib temperature | 0,39 | 0,60 / 0,63 | −0,99 / −0,43 / 0,10 | 2 od 15 | 0,41 |

Temperatura, minutni proseci (`pilot_minute_means.csv`, minut 0 = početak baseline-a, stres počinje u minutu 10,0):
- baseline: 31,66 °C u minutu 3, pad na 31,14 °C u minutu 6 (spontani pad ~0,5 °C bez stresora), zatim 31,29 °C u minutu 8;
- pad počinje u poslednjem minutu baseline-a (minut 9: 31,04 °C) i najniži je u prva dva minuta stresa (minuti 10 i 11: 30,64 i 30,54 °C);
- još tokom stresa temperatura raste (minut 14: 31,19 °C; minut 15, prelaz u oporavak: 31,32 °C), blizu proseka baseline-a (31,37 °C); u oporavku je 31,40 °C.
- Lažni alarmi RF i XGBoost u baseline-u padaju u minute 4–7 i 9, upravo kad temperatura padne (prozori iz `analyze_pilot.py`).

Ostalo:
- Prosečan pad temperature u stresu je 0,46 °C (WESAD medijana −0,88 °C), oko 7 koraka DS18B20, pa rezolucija senzora nije ograničenje.
- GSR je u stresu u proseku 25,5 ADC viši nego u baseline-u, uz šum unutar prozora 8,6 ADC. Porast počinje posle oko 2 minuta stresa (minut 12: 2356 ADC, prema 2317 i 2311 u minutima 10 i 11), a u oporavku je nivo još viši i jako varira (d = 1,39).
- p-vrednosti: temperatura 9·10⁻¹⁸ na prozorima, a 0,022 na minutnim prosecima; GSR 1·10⁻¹² prema 0,022.
- Korelacija temperatura–GSR: 0,04 u pilotu. Na WESAD-u medijana −0,69, ali je kod 10 od 15 ispitanika ispod −0,5, a kod 4 pozitivna.
- Detektori na istom test skupu:

| Detektor | AUC | F1 | Alarm baseline | Alarm stres | Alarm oporavak |
|---|---|---|---|---|---|
| Logistička regresija | 0,645 | 0,43 | 3% | 11% | 3% |
| Random Forest | 0,820 | 0,69 | 28% | 77% | 3% |
| XGBoost | 0,834 | 0,67 | 22% | 65% | 0% |
| Prag temperature z < −2 | 0,647* | 0,67 | 68% | 100% | 47% |

\* binarni detektor; rangiranje samom temperaturom daje AUC 0,844.

Provera hipoteza:
- **H1.1 delimično potvrđena:** pad je velik (d = −1,82) i u stresu nestaje posle uklanjanja trenda (0,25), kako je predviđeno. Ali oporavak je 7,49 SD iznad produženog trenda, pa linearni drift ne objašnjava tok temperature; deo hipoteze „deo je drift" nije potvrđen.
- **H1.2 oborena:** GSR ima |d| = 1,23, u rasponu WESAD-a, u donjoj četvrtini. Smer u odnosu na provodljivost nije poznat.
- H1.3 potvrđena: d = 0,03, ispod svih 15 WESAD ispitanika.
- H1.4 potvrđena: temperatura sama 0,844, XGBoost 0,834.
- H1.5 potvrđena.

## Zaključak i šta znači za sistem
1. **HR sa čvora ne nosi informaciju o stresu** (d ispod svih 15 WESAD ispitanika, a HR raste kod svih 15). U skladu sa greškom frekvencije uzorkovanja.
2. **Temperatura ima pad oko početka stresa, ali iz jedne sesije se ne može odvojiti od spontanih kolebanja.** Pad je počeo u poslednjem minutu baseline-a, najniži je u prva dva minuta stresa, a temperatura se vratila još tokom stresa. Spontani pad od ~0,5 °C postoji i u mirovanju (minuti 3–6), i upravo tada nastaju lažni alarmi modela u baseline-u. Linearni drift ne objašnjava tok. Početak pre oznake je u skladu sa iščekivanjem stresora (ispitanik je znao kad počinje), pa protokol mora da sakrije trenutak početka.
3. **Temperatura je najmanje dosledan marker:** u WESAD-u pada kod 12 od 15 ispitanika, dok HR i EDA rastu kod 15 i 14 od 15. Modeli na pilotu se oslanjaju baš na nju.
4. **GSR je jedini signal sa promenom koju trend ne objašnjava, ali to nije čist obrazac odziva i oporavka:** porast počinje posle oko 2 minuta stresa, a u oporavku je nivo još viši i jako varira. To je u skladu i sa sporim povratkom provodljivosti i sa promenom kontakta elektroda. Smer u odnosu na provodljivost nije potvrđen; test smera je sada najvažniji eksperiment.
5. **ML na pilotu ne nadmašuje jedan signal:** temperatura sama rangira prozore jednako dobro kao XGBoost. Fiksni prag iz kalibracije daje 68% lažnih alarma u baseline-u, jer je SD kalibracije mala (0,08 °C) u odnosu na spontana kolebanja.
6. Korelacija temperatura–GSR u pilotu je 0,04. Kod većine WESAD ispitanika je jasno negativna, ali ne kod svih, pa ovo nije jak argument.
7. Za zaključke se koriste veličine efekta i minutni nivo; p-vrednosti na prozorima su za više redova veličine previše optimistične.

