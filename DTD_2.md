Hier findest du das vollständige Proof-of-Concept als Markdown-Dokument mit korrekt eingerücktem Code:

---

# Proof-of-Concept: Automatisierte DevOps-Infrastruktur für n8n Workflows

Dieses Proof-of-Concept demonstriert die automatisierte Installation von Abhängigkeiten auf einem frischen Windows-System, das Starten von Containern via Docker Compose und eine webbasierte Steuerung mittels einer React-App. Zudem wird die Visualisierung von Systemmetriken mit Python gezeigt.

---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Verzeichnisstruktur](#verzeichnisstruktur)
3. [PowerShell Bootstrap-Skript](#powershell-bootstrap-skript)
4. [Docker Compose-Konfiguration](#docker-compose-konfiguration)
5. [React Dashboard – Webbasierte UI](#react-dashboard–webbasierte-ui)
   - [App.js](#appjs)
   - [ServiceCard-Komponente](#servicecard-komponente)
   - [index.html](#indexhtml)
   - [styles.css](#stylescss)
6. [Python Visualisierungsskript](#python-visualisierungsskript)
7. [Ausführung des Proof-of-Concept](#ausführung-des-proof-of-concept)
8. [Schlussfolgerung](#schlussfolgerung)

---

## 1. Projektübersicht

Das System übernimmt folgende Aufgaben:

- **Bootstrap & Installation:**  
  Prüft, ob Git, Docker Desktop und Python installiert sind, und installiert fehlende Komponenten via Winget (mit Retry und Logging).

- **Container-Orchestrierung:**  
  Startet Container für n8n, PostgreSQL und MQTT mittels Docker Compose. Persistente Volumes und automatische Neustarts sichern den stabilen Betrieb.

- **Webbasierte Steuerung:**  
  Eine React-App stellt ein Dashboard mit Service-Karten und einem Onboarding-Assistenten bereit.

- **Visualisierung:**  
  Ein Python-Skript zeigt, wie Systemmetriken (z. B. CPU-Auslastung) in einem Diagramm dargestellt werden.

---

## 2. Verzeichnisstruktur

```
/devops-infra-poc
├── bootstrap_optimized.ps1    # PowerShell-Skript für Installation & Abhängigkeitsprüfung
├── docker-compose.yml         # Docker Compose-Konfiguration
├── ui
│   ├── public
│   │   └── index.html         # HTML-Datei für die React-App
│   ├── src
│   │   ├── App.js             # Hauptkomponente der React-App
│   │   ├── ServiceCard.js     # Service-Karte-Komponente
│   │   └── styles.css         # CSS-Datei für die UI
│   └── package.json           # React App Konfiguration
└── metrics.py                 # Python-Skript zur Visualisierung von Systemmetriken
```

---

## 3. PowerShell Bootstrap-Skript

```powershell
# bootstrap_optimized.ps1
# Als Administrator ausführen!

function Check-Dependency {
    param(
        [string]$command,
        [string]$name
    )
    if (Get-Command $command -ErrorAction SilentlyContinue) {
        Write-Host "$name gefunden."
        return $true
    } else {
        Write-Host "$name NICHT gefunden."
        return $false
    }
}

function Install-Package {
    param(
        [string]$id,
        [string]$name,
        [int]$maxRetries = 3
    )
    $attempt = 0
    do {
        Write-Host "Versuche, $name über winget zu installieren... (Versuch $($attempt+1))"
        winget install --id $id --silent
        Start-Sleep -Seconds 5  # Wartezeit nach Installation
        $attempt++
    } while (-not (Check-Dependency $name $name) -and ($attempt -lt $maxRetries))
    
    if (Check-Dependency $name $name) {
        Write-Host "$name erfolgreich installiert."
    } else {
        Write-Host "Fehler bei der Installation von $name nach $maxRetries Versuchen. Bitte manuell nachinstallieren."
    }
}

$dependencies = @(
    @{ Name = "Git for Windows"; Command = "git"; WingetId = "Git.Git" },
    @{ Name = "Docker Desktop"; Command = "docker"; WingetId = "Docker.DockerDesktop" },
    @{ Name = "Python 3"; Command = "python"; WingetId = "Python.Python.3" }
)

$missing = @()

foreach ($dep in $dependencies) {
    if (-not (Check-Dependency $dep.Command $dep.Name)) {
        $missing += $dep
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Folgende Abhängigkeiten fehlen:" -ForegroundColor Yellow
    foreach ($dep in $missing) {
        Write-Host "- $($dep.Name)"
    }
    $response = Read-Host "Möchtest du die fehlenden Komponenten automatisch installieren? (J/N)"
    if ($response -match "^(J|j)") {
        foreach ($dep in $missing) {
            Install-Package -id $dep.WingetId -name $dep.Name
        }
    } else {
        Write-Host "Bitte installiere die fehlenden Komponenten manuell, bevor du fortfährst."
        exit 1
    }
} else {
    Write-Host "Alle erforderlichen Abhängigkeiten sind vorhanden."
}

Write-Host "Starte nun Docker Desktop und warte, bis es vollständig hochgefahren ist."
Read-Host "Drücke Enter, wenn Docker bereit ist..."

Write-Host "Starte die Containerumgebung..."
docker-compose -f .\docker-compose.yml up -d

# Log-Datei zur zentralen Fehlerdiagnose
$logPath = ".\install_log.txt"
"Installation abgeschlossen am $(Get-Date)" | Out-File $logPath -Append
```

---

## 4. Docker Compose-Konfiguration

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: securepassword
      POSTGRES_DB: n8n_db
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  mqtt:
    image: eclipse-mosquitto
    ports:
      - "1883:1883"
    volumes:
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log
    restart: always

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n_db
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=securepassword
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=user
      - N8N_BASIC_AUTH_PASSWORD=password
    depends_on:
      - postgres
      - mqtt
    volumes:
      - n8n_data:/root/.n8n
    restart: always

volumes:
  pgdata:
  mosquitto_data:
  mosquitto_log:
  n8n_data:
```

---

## 5. React Dashboard – Webbasierte UI

Im Ordner `ui` befindet sich eine React-App, die das Dashboard bereitstellt.

### App.js

```javascript
// ui/src/App.js
import React, { useState, useEffect } from 'react';
import ServiceCard from './ServiceCard';
import './styles.css';

const App = () => {
  const [status, setStatus] = useState({
    n8n: 'Lade...',
    postgres: 'Lade...',
    mqtt: 'Lade...'
  });

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulierter API-Call zur Status-Aktualisierung
      fetch('/api/status')
        .then(res => res.json())
        .then(data => setStatus(data))
        .catch(err => console.error("Status-Update fehlgeschlagen:", err));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <header>
        <h1>DevOps Dashboard</h1>
        <nav>
          <a href="#home">Home</a>
          <a href="#logs">Logs</a>
          <a href="#settings">Einstellungen</a>
          <a href="#help">Hilfe</a>
        </nav>
      </header>
      <main>
        <section className="status-panel">
          <ServiceCard service="n8n" status={status.n8n} lastActivity="10:32 Uhr" />
          <ServiceCard service="PostgreSQL" status={status.postgres} lastActivity="09:45 Uhr" />
          <ServiceCard service="MQTT" status={status.mqtt} lastActivity="11:05 Uhr" />
        </section>
        <section className="onboarding">
          <h2>Onboarding-Assistent</h2>
          <p>Willkommen! Hier erfährst du die ersten Schritte zur Nutzung der Umgebung.</p>
          <button onClick={() => alert("Starte Onboarding...")}>Onboarding starten</button>
        </section>
      </main>
      <footer>
        <p>Version 1.0 | Support: support@example.com</p>
      </footer>
    </div>
  );
};

export default App;
```

### ServiceCard-Komponente

```javascript
// ui/src/ServiceCard.js
import React from 'react';

const ServiceCard = ({ service, status, lastActivity }) => (
  <div className="service-card">
    <h3>{service}</h3>
    <p>Status: <strong>{status}</strong></p>
    <p>Letzte Aktivität: {lastActivity}</p>
    <button onClick={() => alert(`Details zu ${service} anzeigen...`)}>Details anzeigen</button>
  </div>
);

export default ServiceCard;
```

### index.html

```html
<!-- ui/public/index.html -->
<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DevOps Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <!-- React-Skripte werden hier eingebunden -->
  </body>
</html>
```

### styles.css

```css
/* ui/src/styles.css */
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f0f0f0;
}

.dashboard header {
  background: #333;
  color: #fff;
  padding: 1em;
}

.dashboard header nav a {
  color: #fff;
  margin-right: 1em;
  text-decoration: none;
}

.status-panel {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-around;
  padding: 1em;
}

.service-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 90%;
}

@media (min-width: 768px) {
  .service-card {
    width: 30%;
  }
}

.onboarding {
  text-align: center;
  padding: 1em;
}

footer {
  background: #333;
  color: #fff;
  text-align: center;
  padding: 0.5em;
}
```

---

## 6. Python Visualisierungsskript

```python
# metrics.py
import matplotlib.pyplot as plt

# Beispiel-Daten: CPU-Auslastung in Prozent für verschiedene Dienste
services = ['n8n', 'PostgreSQL', 'MQTT']
cpu_usage = [30, 45, 20]

plt.figure(figsize=(6, 4))
plt.bar(services, cpu_usage)
plt.title("Systemauslastung der Dienste")
plt.xlabel("Dienst")
plt.ylabel("CPU-Auslastung (%)")
plt.show()
```

---

## 7. Ausführung des Proof-of-Concept

### Voraussetzungen

- Windows 10/11 mit aktivierter Virtualisierung und Winget.
- Administratorrechte zur Ausführung des PowerShell-Skripts.
- Installierter Docker Desktop.
- Node.js und npm (für die React-App).

### Schritte

1. **Bootstrap starten:**  
   Führe als Administrator das Skript `bootstrap_optimized.ps1` aus. Dieses Skript prüft und installiert (falls erforderlich) alle Abhängigkeiten und startet Docker Desktop sowie die Container-Umgebung.

2. **Container-Umgebung hochfahren:**  
   Das Skript startet automatisch die Container mittels `docker-compose up -d`.

3. **React-App starten:**  
   Wechsle in den `ui`-Ordner, installiere die Abhängigkeiten und starte die App:
   ```bash
   cd ui
   npm install
   npm start
   ```
   Die App ist dann unter [http://localhost:3000](http://localhost:3000) erreichbar.

4. **Systemmetriken visualisieren:**  
   Führe das Python-Skript `metrics.py` aus, um die Diagrammdarstellung zu sehen:
   ```bash
   python metrics.py
   ```

---

## 8. Schlussfolgerung

Dieses Proof-of-Concept zeigt einen vollständigen Programmablauf zur automatisierten Einrichtung einer DevOps-Infrastruktur:

- **Bootstrap & Installation:**  
  Automatische Prüfung und Installation der notwendigen Tools mit Retry-Mechanismen und zentralem Logging.

- **Container-Orchestrierung:**  
  Docker Compose startet und verwaltet Container für n8n, PostgreSQL und MQTT mit persistenter Datenspeicherung und automatischen Neustarts.

- **Webbasierte Steuerung:**  
  Eine React-App bietet ein Dashboard mit Service-Karten und einem Onboarding-Assistenten.

- **Visualisierung:**  
  Ein Python-Skript stellt Systemmetriken grafisch dar.

Dieses modulare Konzept bildet die Grundlage für den produktiven Einsatz in einer agilen DevOps-Umgebung. Falls weitere Anpassungen oder Detailfragen auftreten, stehe ich gern zur Verfügung!

---