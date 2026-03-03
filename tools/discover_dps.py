#!/usr/bin/env python3
"""
discover_dps.py — Outil de diagnostic pour la sonnette LSC (art. 3208999)

Usage :
    python discover_dps.py --ip 192.168.1.XX --id DEVICE_ID --key LOCAL_KEY

Ce script :
1. Se connecte à la sonnette en local via Tuya
2. Affiche tous les DPS (datapoints) disponibles
3. Écoute pendant 60s les événements en temps réel (appui sonnette, mouvement...)
4. Aide à identifier les bons numéros de DP pour votre modèle

Prérequis :
    pip install tinytuya
"""

import argparse
import time
import json
import tinytuya

def main():
    parser = argparse.ArgumentParser(description="Diagnostic LSC Doorbell")
    parser.add_argument("--ip",  required=True, help="IP de la sonnette")
    parser.add_argument("--id",  required=True, help="Device ID Tuya")
    parser.add_argument("--key", required=True, help="Local Key")
    parser.add_argument("--version", default="3.3", help="Version protocole (3.1/3.3/3.4)")
    parser.add_argument("--listen", type=int, default=60, help="Secondes d'écoute (défaut: 60)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  🔍 LSC Doorbell — Découverte des DPS")
    print(f"{'='*60}")
    print(f"  IP      : {args.ip}")
    print(f"  ID      : {args.id}")
    print(f"  Version : {args.version}")
    print(f"{'='*60}\n")

    dev = tinytuya.Device(
        dev_id=args.id,
        address=args.ip,
        local_key=args.key,
        version=float(args.version),
    )
    dev.set_socketTimeout(10)

    # --- Statut initial ---
    print("📡 Connexion et lecture du statut initial...")
    status = dev.status()
    if not status:
        print("❌ Impossible de se connecter. Vérifiez l'IP, l'ID et la Local Key.")
        return

    if "Error" in str(status):
        print(f"❌ Erreur : {status}")
        return

    print(f"\n✅ Connexion réussie ! DPS trouvés :\n")
    dps = status.get("dps", {})
    for dp_id, value in sorted(dps.items(), key=lambda x: int(str(x[0]))):
        print(f"  DP {str(dp_id):>5} : {value}")

    print(f"\n{'='*60}")
    print(f"  🎧 Écoute des événements pendant {args.listen}s...")
    print(f"  → Appuyez sur le bouton de la sonnette !")
    print(f"  → Passez devant la caméra pour tester le mouvement !")
    print(f"{'='*60}\n")

    dev.set_socketPersistent(True)
    start = time.time()

    while time.time() - start < args.listen:
        data = dev.receive()
        if data and "dps" in data:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] 📨 Événement reçu :")
            for dp_id, value in data["dps"].items():
                print(f"        DP {str(dp_id):>5} = {value}")
            print()

    dev.close()
    print("\n✅ Fin de l'écoute. Notez les DP qui ont changé lors de vos tests !")
    print("   → Mettez à jour const.py avec les bons numéros de DP si nécessaire.\n")


if __name__ == "__main__":
    main()
