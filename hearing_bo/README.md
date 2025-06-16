# Kalibrator Słuchu z Optymalizacją Bayesowską

Projekt ten jest nowoczesną, napisaną w języku Python aplikacją do pomiaru indywidualnej krzywej równej głośności (krzywej izofonicznej). Wykorzystuje on zaawansowaną technikę **Optymalizacji Bayesowskiej**, aby w inteligentny i wydajny sposób przeprowadzić użytkownika przez proces kalibracji. Aplikacja porównuje głośność tonów o różnych częstotliwościach z głośnością stałego "tonu odniesienia".

## Funkcje Aplikacji

- **Backend w Pythonie:** Serwer oparty na frameworku FastAPI, zapewniający wysoką wydajność i asynchroniczność.
- **Inteligentna Optymalizacja:** Zamiast testować częstotliwości w ustalonej kolejności, algorytm sam decyduje, który punkt jest najbardziej niepewny i wybiera go do następnego testu. Minimalizuje to liczbę potrzebnych prób.
- **Wstępna Kalibracja:** Test rozpoczyna się od kilku losowo wybranych punktów, aby zapewnić modelowi solidny punkt wyjścia.
- **Interfejs w Przeglądarce:** Minimalistyczny i responsywny interfejs użytkownika, który działa w każdej nowoczesnej przeglądarce bez potrzeby kompilacji czy instalacji dodatkowych narzędzi.
- **Automatyczne Odtwarzanie:** Pętla A/B automatycznie przełącza między tonem odniesienia a tonem testowym, ułatwiając precyzyjne porównanie głośności.
- **Wizualizacja w Czasie Rzeczywistym:** Obserwuj na żywo, jak budowana jest Twoja krzywa słuchu wraz z zaznaczonym obszarem niepewności modelu.
- **Wieloplatformowość:** Działa na systemach Windows, macOS i Linux.

## Jak to działa? Metoda Optymalizacji

Problem znalezienia krzywej równej głośności można traktować jako aproksymację nieznanej funkcji `Głośność = f(Częstotliwość)`. Zamiast "ręcznie" przeszukiwać całe spektrum, aplikacja wykorzystuje **Optymalizację Bayesowską** opartą na **Procesach Gaussowskich (Gaussian Processes)**.

1.  **Modelowanie Niepewności:** Po zebraniu kilku początkowych punktów (np. `(1000 Hz, -25 dB)`), aplikacja buduje model matematyczny (Proces Gaussowski), który nie tylko przewiduje najbardziej prawdopodobny kształt krzywej, ale także określa **niepewność** swoich przewidywań w każdym punkcie spektrum. Niepewność jest największa w obszarach, gdzie mamy mało danych.

2.  **Inteligentny Wybór Następnego Punktu:** Aplikacja używa tzw. **funkcji akwizycji** (w tym przypadku *Upper Confidence Bound*), aby znaleźć częstotliwość, dla której niepewność modelu jest **maksymalna**. To właśnie ten punkt jest wybierany do następnego testu.

3.  **Minimalizacja Pracy Użytkownika:** Dzięki takiemu podejściu, zamiast testować dziesiątki punktów po kolei, użytkownik testuje tylko te, które dostarczają algorytmowi najwięcej nowych informacji. To znacznie skraca cały proces i pozwala uzyskać dokładną krzywą przy niewielkiej liczbie (10-15) testów.

## Wymagania

- Python w wersji 3.7+
- `pip` (menedżer pakietów dla Pythona)
- Nowoczesna przeglądarka internetowa (Chrome, Firefox, Edge, Safari)

## Instalacja

1.  **Sklonuj repozytorium lub pobierz pliki.**
    Umieść foldery `backend` i `frontend` w jednym katalogu głównym projektu.

2.  **Utwórz wirtualne środowisko Pythona.**
    Jest to zalecana praktyka, aby odizolować zależności projektu. Otwórz terminal lub wiersz poleceń w głównym katalogu projektu.

    ```bash
    # Przejdź do katalogu backend
    cd backend

    # Utwórz wirtualne środowisko o nazwie venv
    python -m venv venv

    # Aktywuj wirtualne środowisko
    # W systemie Windows:
    venv\Scripts\activate
    # W systemach macOS/Linux:
    source venv/bin/activate
    ```

3.  **Zainstaluj wymagane pakiety Pythona.**
    Upewnij się, że wirtualne środowisko jest aktywne, a następnie uruchom polecenie:

    ```bash
    pip install -r requirements.txt
    ```

## Uruchamianie Aplikacji

1.  **Uruchom serwer backendu.**
    Będąc w katalogu `backend` z aktywnym środowiskiem wirtualnym, uruchom:

    ```bash
    uvicorn main:app --reload
    ```
    Flaga `--reload` jest przydatna podczas developmentu, ponieważ serwer automatycznie uruchomi się ponownie po każdej zmianie w kodzie.

2.  **Otwórz aplikację w przeglądarce.**
    Serwer poinformuje Cię, na jakim adresie działa. Zazwyczaj jest to `http://127.0.0.1:8000`. Otwórz ten adres URL w swojej przeglądarce.

## Jak Korzystać z Programu

1.  **Konfiguracja:**
    - Aplikacja automatycznie wykryje dostępne urządzenia audio. Wybierz to, którego chcesz użyć (np. słuchawki).
    - Ustaw liczbę **Początkowych Punktów Kalibracyjnych**. Domyślna wartość `5` jest dobrym punktem startowym.
    - Ustaw **Częstotliwość Odniesienia** (Root Frequency) oraz **Głośność Odniesienia** (Root Volume). Będzie to stały ton, do którego porównywane będą wszystkie inne. Domyślne `1000 Hz` i `-25 dBFS` to bezpieczne i komfortowe ustawienia.
    - Kliknij **"Start Test"**.

2.  **Pętla Testowa:**
    - Interfejs przełączy się na ekran testowy. Najpierw zostaniesz przeprowadzony przez zadaną liczbę punktów kalibracji wstępnej.
    - Kliknij **"Start Auto-Cycle"**. Aplikacja zacznie na przemian odtwarzać ton odniesienia i aktualnie testowany ton. Możesz regulować prędkość przełączania.
    - Twoim zadaniem jest dostosowanie suwaka **"Test Volume"** tak, aby głośność tonu testowego była identyczna z głośnością tonu odniesienia.
    - Gdy będziesz zadowolony z dopasowania, kliknij **"Confirm and Go to Next Point"**. Jeśli automatyczne odtwarzanie było włączone, uruchomi się ono ponownie dla kolejnego punktu.

3.  **Powtarzaj:**
    - Po zakończeniu kalibracji wstępnej, aplikacja przejdzie do fazy **"Optymalizacji"**, gdzie algorytm będzie inteligentnie dobierał kolejne częstotliwości.
    - Dla każdego nowego punktu dopasuj głośność i zatwierdź.
    - Wykres będzie aktualizował się w czasie rzeczywistym. Niebieska linia to najlepsze przybliżenie krzywej, zacieniony obszar to niepewność modelu, a czerwone kropki to zmierzone przez Ciebie punkty.
    - Powtarzaj proces, aż uzyskasz łącznie 10-15 punktów lub do momentu, gdy krzywa się ustabilizuje, a obszar niepewności będzie wąski.

4.  **Sterowanie Wykresem:**
    - Użyj przycisku **"Toggle X-Axis"**, aby przełączać skalę osi częstotliwości między logarytmiczną (domyślnie) a liniową.