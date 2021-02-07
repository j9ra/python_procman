
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

### Plik konfiguracyjny
```
# Nazwa serwisu
name: service_name

# Parametry 
procman:
  java:
    vmpath: /path/to/java_binary
    debug: true/false
    memory:
      min: 1234k/m/g
      max: 1234k/m/g
      meta: 1234k/m/g
    gc: serial/parallel/cms/g1
    classpath: 
      - path
      - path*
      - jar
    sysprops:
      - pl.grabojan.test=true
      - java.awt.headless=true
    main: some.main.class.Main
    args: [a,b,c,d]
    streamout: /path/to/dir
```

***

### TEST 

*uruchomienie flask*  
export PROCMAN_USER=procman  
export PROCMAN_PASSWORD=secret  
python -m flask run --host=0.0.0.0  

*zarządzanie serwisem*  
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"start"}'  http://localhost:5000/service  
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"status"}'  http://localhost:5000/service  
curl -u procman:secret --header "Content-Type: application/json" --request POST --data '{"service":"echo","command":"stop"}'  http://localhost:5000/service  
