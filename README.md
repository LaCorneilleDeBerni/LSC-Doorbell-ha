# 🔔 LSC Smart Connect Video Doorbell — Home Assistant Integration
NON FONCTIONAL FOR NOW

Intégration **100% locale** (sans cloud, sans appli LSC) pour la sonnette LSC Smart Connect Video Doorbell Rechargeable.

> **Modèle testé :** art. 3208999 / SI C25305 — vendue chez Action

---

## ✅ Ce que cette intégration fournit

| Fonctionnalité | Disponible |
|---|---|
| 📹 Flux vidéo en direct (RTSP) | ✅ |
| 🎤 Audio / microphone | ✅ (inclus dans le flux RTSP) |
| 🔔 Bouton sonnette (binary_sensor) | ✅ |
| 🚶 Détection de mouvement | ✅ |
| ☁️ Cloud Tuya/LSC requis | ❌ Non ! |
| 📱 Appli LSC requise après config | ❌ Non ! |

---

## 📋 Prérequis

- Home Assistant 2024.1.0 ou plus récent
- HACS installé
- Python 3.9+ sur votre PC (pour récupérer la Local Key)
- La sonnette sur le même réseau Wi-Fi que Home Assistant

---

## 🚀 Guide d'installation complet

### ÉTAPE 1 — Connecter la sonnette au Wi-Fi

> ⚠️ Il faut passer **une seule fois** par l'appli Smart Life (gratuite, générique Tuya) pour connecter la sonnette au Wi-Fi. Ensuite, l'appli n'est plus nécessaire.

1. **Téléchargez** l'application **Smart Life** (iOS ou Android) — c'est l'appli Tuya générique, pas l'appli LSC
2. **Créez un compte** Smart Life (email + mot de passe)
3. **Allumez la sonnette** (bouton power)
4. **Appuyez 5 secondes** sur le bouton de réinitialisation (trou sous la sonnette avec un trombone) jusqu'au bip
5. Dans Smart Life → **"+"** → **"Ajouter un appareil"** → suivez les instructions Wi-Fi
6. Une fois ajoutée, vérifiez que la sonnette apparaît dans l'appli avec la vidéo en direct

**Notez l'IP** attribuée par votre routeur à la sonnette (interface admin du routeur → liste des appareils connectés).

> 💡 **Conseil :** Attribuez une IP fixe (bail DHCP statique) dans votre routeur pour que l'IP ne change jamais.

---

### ÉTAPE 2 — Récupérer la Local Key avec tinytuya

C'est la clé qui permet à Home Assistant de parler directement à la sonnette **sans le cloud**.

#### 2a. Créer un compte développeur Tuya IoT (gratuit, 5 min)

1. Allez sur **https://iot.tuya.com** et créez un compte (si demandé le type de compte, choisissez "Skip this step")
2. Allez dans **Cloud** → **Create Cloud Project**
   - Nom : `mon-projet-ha` (au choix)
   - Industry : `Smart Home`
   - Development Method : `Smart Home`
   - Data Center : **Europe West** ← important pour la France
3. Cliquez **Create**
4. Dans **Service API**, cliquez **"Go to Authorize"** et abonnez-vous à :
   - `IoT Core`
   - `Authorization`
   - `Smart Home Scene Linkage`
5. Notez votre **API ID** et **API Secret** (onglet Overview du projet)

#### 2b. Lier votre compte Smart Life au projet Tuya IoT

1. Dans votre projet → **Devices** → **Link Tuya App Account**
2. Cliquez **"Add App Account"** → choisissez **Automatic** + **Read Only**
3. Un QR code s'affiche
4. Dans l'app **Smart Life** sur votre téléphone : onglet **"Me"** → icône QR code en haut à droite → scannez le QR code
5. Vos appareils apparaissent dans le projet Tuya IoT ✅

#### 2c. Récupérer la Local Key avec tinytuya

Sur votre **PC** (Windows/Mac/Linux) :

```bash
# Installer tinytuya
pip install tinytuya requests

# Lancer le wizard
python -m tinytuya wizard
```

Le wizard vous demande :
- **API Key** : votre API ID du projet Tuya IoT
- **API Secret** : votre API Secret
- **API Region** : `eu` (pour Europe)
- **Device ID** : l'ID d'un de vos appareils (visible dans Tuya IoT → Devices)

À la fin, il crée un fichier `devices.json` avec :
```json
[
  {
    "name": "Video Doorbell",
    "id": "abcdef1234567890abcd",      ← votre Device ID
    "key": "a1b2c3d4e5f6g7h8",         ← votre Local Key
    "ip": "192.168.1.50",
    "version": "3.3"
  }
]
```

> 📌 **Notez bien** le `id` (Device ID) et le `key` (Local Key) — vous en aurez besoin à l'étape 4.

---

### ÉTAPE 3 — (Optionnel) Tester le flux RTSP

Avant d'aller dans Home Assistant, vérifiez que la vidéo fonctionne :

```bash
# Outil de diagnostic fourni dans ce dépôt
python tools/test_rtsp.py --ip 192.168.1.XX
```

Ou directement dans **VLC** : Média → Ouvrir un flux réseau :
```
rtsp://192.168.1.XX:554/stream0
```

Si vous obtenez la vidéo → ✅ parfait !

Si rien ne fonctionne, essayez le script de découverte des DPS (voir section Dépannage).

---

### ÉTAPE 4 — Installer l'intégration dans Home Assistant

#### Via HACS (recommandé)

1. Dans HACS → **Intégrations** → **⋮** → **Dépôts personnalisés**
2. Ajoutez : `https://github.com/LaCorneilleDeBerni/LSC-Doorbell-ha`
3. Catégorie : **Integration**
4. Cliquez **Télécharger** → **Redémarrez Home Assistant**

#### Installation manuelle

1. Copiez le dossier `custom_components/lsc_doorbell/` dans votre dossier `config/custom_components/`
2. Redémarrez Home Assistant

---

### ÉTAPE 5 — Configurer l'intégration

1. **Paramètres** → **Appareils et services** → **+ Ajouter une intégration**
2. Cherchez **"LSC Doorbell"**
3. Remplissez :
   - **Adresse IP** : l'IP de votre sonnette (ex: `192.168.1.50`)
   - **Device ID** : copié depuis `devices.json`
   - **Local Key** : copié depuis `devices.json`
   - **Version protocole** : `3.3` (essayez `3.4` si ça ne marche pas)
   - **Port RTSP** : `554` (défaut)
   - **Chemin RTSP** : `/stream0` (défaut)
4. Cliquez **Valider** — l'intégration teste la connexion automatiquement

---

### ÉTAPE 6 — Entités créées dans Home Assistant

Après configuration, vous aurez :

| Entité | Type | Description |
|---|---|---|
| `camera.lsc_doorbell_camera` | Camera | Flux vidéo + audio RTSP |
| `binary_sensor.lsc_doorbell_bouton_sonnette` | Binary Sensor | ON lors d'un appui |
| `binary_sensor.lsc_doorbell_detection_mouvement` | Binary Sensor | ON si mouvement détecté |

---

## 🔔 Exemple d'automatisation : notification lors d'un appui

```yaml
automation:
  - alias: "Sonnette - Notification mobile"
    trigger:
      platform: state
      entity_id: binary_sensor.lsc_doorbell_bouton_sonnette
      to: "on"
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "🔔 Quelqu'un à la porte !"
          message: "La sonnette vient d'être pressée"
```

---

## 🗺️ Carte Lovelace — Afficher la caméra

```yaml
type: picture-glance
title: Porte d'entrée
camera_image: camera.lsc_doorbell_camera
entities:
  - entity: binary_sensor.lsc_doorbell_bouton_sonnette
    name: Sonnette
  - entity: binary_sensor.lsc_doorbell_detection_mouvement
    name: Mouvement
```

---

## 🔧 Dépannage

### La connexion échoue dans HA

1. Vérifiez que la sonnette est bien allumée et sur le réseau
2. Essayez `python tools/discover_dps.py --ip 192.168.1.XX --id DEVICE_ID --key LOCAL_KEY`
3. Essayez une autre version de protocole : `3.1`, `3.3`, `3.4`
4. Vérifiez que votre pare-feu autorise les ports TCP 6668 et UDP 6666/6667

### La vidéo ne s'affiche pas

1. Testez d'abord l'URL RTSP dans VLC
2. Essayez les variantes : `/stream0`, `/stream1`, `/live/stream0`
3. Assurez-vous que l'add-on **go2rtc** est installé dans Home Assistant (recommandé pour le streaming en direct)

### Les DPS ne correspondent pas

Si les événements de sonnette ou de mouvement ne fonctionnent pas, lancez le script de découverte :

```bash
python tools/discover_dps.py --ip 192.168.1.XX --id DEVICE_ID --key LOCAL_KEY --listen 60
```

Appuyez sur le bouton et passez devant la caméra. Notez quels DP changent et mettez à jour `const.py`.

### Activer les logs de debug

Dans `configuration.yaml` de Home Assistant :

```yaml
logger:
  default: info
  logs:
    custom_components.lsc_doorbell: debug
```

---

## 📐 Architecture technique

### Fonctionnement en deux phases

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE 1 — Setup unique (à faire une seule fois)            ║
║                                                              ║
║  Application Smart Life ──► Cloud Tuya ──► Local Key        ║
║  (connexion initiale Wi-Fi)   (stockage)    (récupérée avec ║
║                                              tinytuya wizard)║
╚══════════════════════════════════════════════════════════════╝
                          │
                          ▼  Local Key copiée dans Home Assistant
╔══════════════════════════════════════════════════════════════╗
║  PHASE 2 — Fonctionnement quotidien (100% local, sans cloud)║
║                                                              ║
║  Home Assistant ◄─────────────────► Sonnette LSC            ║
║                   réseau Wi-Fi local                         ║
║                   port TCP 6668                              ║
║                                                              ║
║  • Flux vidéo + audio  →  RTSP direct      (port 554)        ║
║  • Bouton sonnette     →  push Tuya local  (port 6668)       ║
║  • Détection mouvement →  push Tuya local  (port 6668)       ║
║                                                              ║
║  ☁️  Aucune connexion vers les serveurs Tuya/LSC             ║
╚══════════════════════════════════════════════════════════════╝
```

> **Pourquoi passer par Tuya IoT Platform une fois ?**
> La Local Key est générée et stockée dans le cloud Tuya lors de la première
> connexion de l'appareil. On doit y accéder une seule fois pour en faire une
> copie locale. Ensuite, le compte Tuya IoT peut être ignoré — Home Assistant
> utilise uniquement la clé locale pour communiquer directement avec la sonnette.

### Structure du dépôt

```
lsc_doorbell_ha/
├── custom_components/
│   └── lsc_doorbell/
│       ├── __init__.py         # Coordinateur principal + boucle push Tuya local
│       ├── manifest.json       # Métadonnées de l'intégration
│       ├── config_flow.py      # Configuration via l'UI HA
│       ├── camera.py           # Entité caméra (flux RTSP vidéo + audio)
│       ├── binary_sensor.py    # Bouton sonnette + détection mouvement
│       ├── const.py            # Constantes et numéros de DP (datapoints)
│       └── strings.json        # Textes UI en français
├── tools/
│   ├── discover_dps.py         # Outil de découverte des datapoints Tuya
│   └── test_rtsp.py            # Outil de test du flux vidéo RTSP
├── hacs.json                   # Compatibilité HACS
└── README.md                   # Ce fichier
```

---

## 📜 Licence

MIT — libre d'utilisation, modification et distribution.

---

## 🙏 Crédits

- [jasonacox/tinytuya](https://github.com/jasonacox/tinytuya) — communication Tuya locale
- [jurgenmahn/ha_tuya_doorbell](https://github.com/jurgenmahn/ha_tuya_doorbell) — inspiration
- Communauté Home Assistant France
