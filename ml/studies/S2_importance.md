# S2 – Važnost atributa i konfiguracije modela

Skripta: `ml/s2_importance.py` · rezultati: `ml/results/s2/`

## Pitanje
Koji atributi nose odluku modela na WESAD-u, a koji na pilotu? Da li neka
konfiguracija atributa, izabrana unapred, prenosi bolje na naš hardver?

## Pravilo
Odluke se donose na WESAD-u (LOSO), a na pilotu se svaka unapred zapisana
konfiguracija proverava jednom. Prijavljuju se sve konfiguracije, i neuspešne.

## Konfiguracije (zapisane pre pokretanja)
| Oznaka | Atributi | Obrazloženje nezavisno od pilota |
|---|---|---|
| C0 | svih 5 | referenca, trenutni modeli |
| C1 | bez HR | HR sa čvora je nevalidan (25 Hz pretpostavljeno, ~20 Hz stvarno) |
| C2 | bez temperature | da li ostali signali sami nose stres |
| C3 | samo EDA | EDA je u literaturi glavni marker simpatičke aktivacije |
| C4 | samo temperatura | koliko nosi temperatura sama |
| C5 | bez HR, sa monotonim ograničenjima (RF, XGB) | fiziologija: EDA↑, temperatura↓ pod stresom |

## Hipoteze
Zapisane 22.10.2026, pre pokretanja; nisu slepe (posle prve analize pilota).

- **H2.1** Na WESAD-u je najvažniji atribut EDA (eda_mean), ne temperatura.
- **H2.2** Na pilotu konfiguracije bez temperature (C2, C3) daju AUC blizu 0,5.
- **H2.3** Izbacivanje HR-a (C1) ne pogoršava rezultat na pilotu.
- **H2.4** Monotona ograničenja (C5) ne kvare LOSO na WESAD-u za više od 0,02 AUC.

## Šta bi oborilo hipoteze
- H2.1: temperatura je na WESAD-u važnija od EDA.
- H2.2: C2 ili C3 na pilotu daju AUC > 0,7.

## Metod
- **Permutaciona važnost:** u test foldu se izmeša jedan atribut i meri pad AUC (10 ponavljanja na WESAD-u, 30 na pilotu). Izabrana je umesto ugrađene važnosti stabala jer meri isto za sva tri modela i meri je na podacima koje model nije video.
- **Konfiguracije:** svaka se oceni LOSO-om na WESAD-u (isti test skup kao eksperiment kalibracije), zatim istrenira na svih 15 ispitanika i proveri na pilotu jednom, za oba smera GSR-a.
- **Monotona ograničenja (C5)** umesto ručnih težina: kod stabala se težine ne zadaju, a ograničenje direktno kodira fiziologiju (EDA nivo i varijabilnost ↑, temperatura ↓, nagib slobodan). Logistička regresija je izostavljena jer je već linearna.
- **Provera ponovljivosti:** C0 daje isti WESAD F1 kao eksperiment kalibracije (0,886 / 0,924 / 0,911) i isti AUC na pilotu kao `analyze_pilot.py`.

## Rezultat
Izvor: `importance_wesad_vs_pilot.csv`, `summary_by_config.csv`, `wesad_loso_per_subject.csv`.

Permutaciona važnost (pad AUC), C0:

| Atribut | WESAD (LR / RF / XGB) | Pilot (LR / RF / XGB) |
|---|---|---|
| EDA nivo | 0,175 / 0,172 / 0,150 | −0,089 / 0,053 / 0,029 |
| Temperatura | 0,071 / 0,128 / 0,121 | 0,214 / 0,285 / 0,276 |
| HR | 0,030 / 0,006 / 0,011 | 0,025 / 0,012 / 0,008 |
| EDA varijabilnost, nagib | ≤ 0,006 | ≤ 0,03 |

Konfiguracije, AUC (WESAD LOSO | pilot GSR po formuli | pilot GSR obrnut):

| Konfiguracija | LR | RF | XGB |
|---|---|---|---|
| C0 svih 5 | 0,977 · 0,645 · 0,824 | 0,989 · 0,820 · 0,711 | 0,989 · 0,834 · 0,731 |
| C1 bez HR | 0,955 · 0,638 · **0,862** | 0,978 · 0,823 · 0,701 | 0,973 · 0,823 · 0,682 |
| C2 bez temperature | 0,970 · 0,463 · 0,623 | 0,940 · 0,689 · 0,489 | 0,921 · 0,759 · 0,313 |
| C3 samo EDA | 0,932 · 0,383 · 0,646 | 0,887 · 0,623 · 0,414 | 0,874 · 0,668 · 0,342 |
| C4 samo temperatura | 0,822 · 0,680 · 0,680 | 0,710 · 0,770 · 0,770 | 0,715 · 0,793 · 0,793 |
| C5 bez HR, monotono | – | 0,987 · 0,650 · 0,733 | 0,981 · 0,741 · 0,778 |

C5 na WESAD-u, F1: RF 0,863, XGB 0,931 (najbolji F1 od svih konfiguracija). Uz obrnut smer GSR-a monotoni XGB na pilotu ima AUC 0,778 uz 9% alarma u baseline-u i 2% u oporavku; C0 XGB u istom smeru ima 26% i 13%.

Po ispitaniku (`wesad_loso_per_subject.csv`), AUC LR / RF / XGB:

| Ispitanik | C4 samo temperatura | C3 samo EDA | C0 svih 5 |
|---|---|---|---|
| S14 | 0,01 / 0,38 / 0,40 | 0,97 / 0,89 / 0,90 | 0,67 / 0,97 / 0,97 |
| S15 | 0,45 / 0,30 / 0,29 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 |
| S16 | 0,26 / 0,29 / 0,25 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 |
| S17 | 0,93 / 0,96 / 0,95 | 0,23 / 0,54 / 0,60 | 1,00 / 0,96 / 0,95 |

- S14, S15 i S16 su ispitanici kod kojih temperatura pod stresom raste (S1); model sa samo temperaturom kod njih radi obrnuto (AUC < 0,5).
- S17 je jedini ispitanik kod kog EDA pod stresom pada (S1); model sa samo EDA kod njega ne radi.
- Model sa svim atributima pokriva sve četiri, osim logističke regresije kod S14.
- U C0 je po permutacionoj važnosti najvažniji atribut EDA kod 9 od 15 ispitanika, a temperatura kod 6, za sva tri modela.

Provera hipoteza:
- H2.1 potvrđena: na WESAD-u je EDA najvažniji atribut za sva tri modela.
- **H2.2 delimično oborena:** bez temperature pilot nije na 0,5, nego zavisi od modela i smera GSR-a (0,31–0,76). Logistička regresija je bolja uz obrnut smer GSR-a, kako fiziologija predviđa (EDA raste pod stresom), a stabla obrnuto.
- H2.3 potvrđena: izbacivanje HR-a ne kvari pilot; LR uz obrnut GSR raste sa 0,824 na 0,862.
- H2.4 potvrđena: monotona ograničenja ne kvare WESAD (u odnosu na C1 čak popravljaju: RF 0,978 → 0,987, XGB 0,973 → 0,981).

## Zaključak i šta znači za sistem
1. **Modeli na WESAD-u odlučuju na osnovu EDA, a na pilotu na osnovu temperature.** To je pomeranje domena u samoj odluci modela: pilot ne daje EDA informaciju koju su modeli naučili da koriste.
2. **Stabla bez ograničenja se na pilotu ne ponašaju fiziološki:** bez temperature bolja su uz smer GSR-a koji fiziologija ne podržava. EDA u pilotu je malo (oko ±2 SD), u opsegu u kom je i WESAD baseline, pa odluka stabala tu ne prati jasno pravilo. Linearni i monotoni modeli se ponašaju dosledno i svi daju bolji rezultat uz obrnut smer GSR-a (LR C1 0,862; XGB C5 0,778). To je posredan pokazatelj da formula proizvođača možda ne važi za naš spoj, ali je izveden iz pilota, pa ne zamenjuje test smera.
3. **Monotona ograničenja su dobar izbor za dalji rad:** isti ili bolji rezultat na WESAD-u, fiziološki tumačiv model i predvidivo ponašanje na novom hardveru.
4. **Nijedan signal ne radi kod svih ljudi, a kombinacija radi:** temperatura zakaže kod 3 od 15 WESAD ispitanika, EDA kod 1, a model sa svim atributima ih pokriva. Na pilotu je praktično ostala samo temperatura, pa sistem nema tu zaštitu. Multimodalnost je suština pristupa, ne dodatak.
5. HR se može izbaciti iz modela dok se ne izračunava iz sirovog PPG-a na Pi-ju.
6. Pilot ima 157 prozora za ocenu; razlike od nekoliko stotih AUC-a između konfiguracija nisu pouzdane.

### PLanovi za budući ekspreimetn

HR može da se izbaci (C1) bez gubitka na pilotu, dok se ne bude računao na Pi-ju.
Monotoni XGBoost (C5) ima najbolji F1 na WESAD-u (0,931). Uz obrnut smer GSR-a na pilotu daje AUC 0,78 uz samo 9% alarma u baseline-u i 2% u oporavku. Trenutni XGBoost u istom smeru ima 26% i 13%. Ovo je kandidat za sledeći pilot, a ne dokazani pobednik: zaključak se zasniva na jednom ispitaniku.