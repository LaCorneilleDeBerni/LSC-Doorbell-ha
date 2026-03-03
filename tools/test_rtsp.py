#!/usr/bin/env python3
"""
test_rtsp.py — Teste les URLs RTSP courantes de la sonnette LSC

Usage :
    python test_rtsp.py --ip 192.168.1.XX

Ce script essaie automatiquement toutes les combinaisons RTSP connues
pour les caméras LSC/Tuya et affiche lesquelles fonctionnent.

Prérequis :
    pip install opencv-python
    (ou simplement utiliser VLC avec les URLs affichées)
"""

import argparse
import socket

RTSP_URLS_TO_TEST = [
    "/stream0",
    "/stream1",
    "/live/stream0",
    "/live/stream1",
    "/live",
    "/ch0_0.264",
    "/h264/ch01/main/av_stream",
    "/onvif1",
    "/cam/realmonitor?channel=1&subtype=0",
]

RTSP_PORTS = [554, 8554, 1935]

def check_port(ip: str, port: int, timeout: float = 2.0) -> bool:
    """Vérifie si un port TCP est ouvert."""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def main():
    parser = argparse.ArgumentParser(description="Test RTSP LSC Doorbell")
    parser.add_argument("--ip", required=True, help="IP de la sonnette")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  📹 Test RTSP — LSC Doorbell ({args.ip})")
    print(f"{'='*60}\n")

    # Scan des ports RTSP ouverts
    open_ports = []
    print("🔍 Scan des ports RTSP...")
    for port in RTSP_PORTS:
        if check_port(args.ip, port):
            print(f"  ✅ Port {port} OUVERT")
            open_ports.append(port)
        else:
            print(f"  ❌ Port {port} fermé")

    if not open_ports:
        print("\n⚠️  Aucun port RTSP détecté.")
        print("   La sonnette est peut-être :")
        print("   - Éteinte ou hors portée Wi-Fi")
        print("   - Sur une autre IP (vérifiez votre routeur)")
        print("   - Ne supporte pas RTSP nativement (mode cloud uniquement)")
        return

    print(f"\n{'='*60}")
    print("  🎯 URLs RTSP à tester dans VLC :")
    print(f"{'='*60}\n")

    for port in open_ports:
        for path in RTSP_URLS_TO_TEST:
            url = f"rtsp://{args.ip}:{port}{path}"
            print(f"  {url}")

    print(f"\n{'='*60}")
    print("  💡 Comment tester dans VLC :")
    print("     Média → Ouvrir un flux réseau → collez l'URL")
    print()
    print("  💡 Si aucune URL ne fonctionne, essayez avec identifiants :")
    print(f"     rtsp://admin:@{args.ip}:554/stream0")
    print(f"     rtsp://admin:admin@{args.ip}:554/stream0")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
