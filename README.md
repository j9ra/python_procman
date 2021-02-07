
# PROCMAN

### Opis projektu
Zarządca procesów dla programów Java napisanych w starym stylu, czyli wymagajacych konfiguracji wielu parametrów JVM czy ustawień CLASSPATH dla wielu bibliotek
Czyli dla aplikacji nie w stylu Spring Boot, gdzie mamy praktycznie jeden plik JAR do uruchomienia.
Generalnie rozwiązanie te ma na celu zastopienie skomplikowanych skryptów shell bash (linux) batch (win64) które są często używane do uruchamiania aplikacji napisanych w Java.

Konfiguracja parametrów procesu jest definiowana w pliku o formacie YAML i umożliwia:
- ustawienia rozmiarów pamięci JVM
- uruchomienia debuger przy pomocy prostej flagi True/False
- budowanie classpath z użyciem wyrażeń wieloznacznych dla plików (*,?,[])
- wyspecyfikowanie parametrow systemowych
- wybór parametrow GC przy pomocy prostej nazwy mechanizmy
- wskazanie klasy głownej programu
- wskazanie argumentow stałych programu
- przekierowanie STDOUT / STERR do pliku loga

Podczas parsowania pliku konfiguracyjnego następuje wygenerowanie pełnej komendy do uruchomienia procesu JAVA dla danej aplikacji

Dodatkowo podczas konstruowania CLASSPATH program wykrywa duplikaty plików JAR, pod kątem różnych wersji tych samych artefaktów, po warunkiem jeżeli biblioteki były zbudowane przy pomocy MAVEN i zawieraja plik pom.properties w META-INF

Procesem zarządza prosta aplikacja we Flasku ktora pozwala na zdalne:
- uruchomienie procesu
- zatrzymanie procesu
- sprawdzenie statusu

Procesów do zarządzania, może być wiele, tyle ile definicji w pliku konfiguracyjnym, wyróżnianych nazwą logiczna wybraną dla danego procesu.

***

### Plik konfiguracyjny services.xml

Plik zawiera konfiguracje dla wybranego procesu java

```
# Nazwa serwisu
name: service_name

# Parametry 
procman:
  java:
    # Ścieżka do JVM (opcjonalny)
    vmpath: /path/to/java_binary
    # Uruchomienie debug-era (opcjonalny)
    debug: true/false
    # Ustawienie pamieci dla JVM (opcjonalny)
    memory:
      min: 1234k/m/g
      max: 1234k/m/g
      meta: 1234k/m/g
    # Ustawienie typu Garbage Collectora (opcjonalny)
    gc: serial/parallel/cms/g1
    # Wskazanie plików JAR lub katalogów (obowiązkowy)
    classpath: 
      - path
      - path*
      - jar
    # Ustawienie parametrów systemowych JVM (opcjonalny)
    sysprops:
      - pl.grabojan.test=true
      - java.awt.headless=true
    # Wskazanie klasy startowej (obowiązkowy)
    main: some.main.class.Main
    # Argumenty przekazane do programu
    args: [a,b,c,d]
    # Przekierowanie wyjścia do pliku (opcjonalny)
    streamout: /path/to/dir$$
```

Parametr classpath przyjmuje symbole wieloznaczne (*,?,[]) do budowania listy plików/katalogów
Parametr streamout może zawierać na końcu dwa znaki $$ oznaczajace, że do ścieżki zostanie doklejony znacznik czasu.


***

### TEST 

*konfiguracja pliku services.xml*
Plik konfiguracyjny musi zawierać definicje parametrów

*uruchomienie flask*  

export PROCMAN_USER=procman  
export PROCMAN_PASSWORD=secret  
python -m flask run --host=0.0.0.0   

_w zmiennych PROCMAN_USER i PROCMAN_PASSWORD wskazujemy dane użytkownika uprawnionego do wysyłania żądań do kontrolera aplikacji Flask_  

*zarządzanie serwisem*  
- uruchomienie
```
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"start"}'  http://localhost:5000/service  
```
- sprawdzenie statusu
```
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"status"}'  http://localhost:5000/service  
```

- zatrzymanie
```
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"stop"}'  http://localhost:5000/service  
```

- przeładowanie konfiguracji
```
curl -u procman:secret http://localhost:5000/reload
```

- lista serwisow
```
curl -u procman:secret http://localhost:5000/service
```

### Przykładowe aplikacja Java

W repozytorium znajduja sie dwie aplikacje
- camel-echo - serwis typu echo słuchający na porcie 9998/tcp, w katalogu java_lib/java_app
- batch - program dzialajacy w tle wypisujacy wartosc swojego argumentu na wyście, w katalogu java_test (przykład specjalnie zawiera duplikat biblioteki JAR)

Obie usługi są dostępne do zarządzania przez Flask:
```
{"services":["echo","batch"]}
```
