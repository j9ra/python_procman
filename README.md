
*PROCMAN*

Zarządca procesów dla programów Java napisanych w starym stylu, czyli wymagajacych konfiguracji wielu parametrów JVM czy ustawień CLASSPATH dla wielu bibliotek
Czyli dla aplikacji nie w stylu Spring Boot, gdzie mamy praktycznie jeden plik JAR do uruchomienia.
Generalnie rozwiązanie te ma na celu zastopienie skomplikowanych skryptów shell bash (linux) batch (win64) które są często używane do uruchamiania aplikacji napisanych w Java.

Konfiguracja parametrów procesu jest definiowana w pliku o formacie YAML i umożliwiaja:
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

Samym procesem uruchamiania zarządza prosta aplikacja we Flasku ktora pozwalała na zdalne:
- uruchominie procesu
- sprawdzenie statusu
- zatrzymanie procesu

Procesów do zarządzania, może być wiele, tyle ile definicji w pliku konfiguracyjnym, wyróżnianych nazwą logiczna wybraną dla danego procesu.



