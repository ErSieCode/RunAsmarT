# RunAsmarT
# Automatisierte, containerisierte Infrastruktur mit Proxmox und Ansible

Hier ist eine umfassende Dokumentation für ein containerisiertes Setup basierend auf Proxmox, Ansible und Docker mit allen angeforderten Diensten.

---

## Inhaltsverzeichnis
- [Architekturübersicht](#architekturübersicht)
- [Infrastrukturdesign](#infrastrukturdesign)
- [Automatisierte Bereitstellung mit Ansible](#automatisierte-bereitstellung-mit-ansible)
- [Docker Compose Setup](#docker-compose-setup)
- [Custom Development Environment](#custom-development-environment)
- [Integration und Konfiguration der Services](#integration-und-konfiguration-der-services)

---

## Architekturübersicht
![Controller Toolbox Screenshot](https://github.com/ErSieCode/RunAsmarT/blob/main/Ungebungsübersicht.jpg)

     ```
    graph TD
    %% Hardware-Layer
    subgraph HardwareLayer["Hardware-Layer"]
        PHYSICAL["Physische Server"]
    end
    
    %% Proxmox-Cluster
    subgraph ProxmoxCluster["Proxmox-Cluster"]
        PROXMOX_MASTER["Proxmox Master Node"]
        PROXMOX_NODE1["Proxmox Node 1"]
        PROXMOX_NODE2["Proxmox Node 2"]
        PROXMOX_MASTER --- PROXMOX_NODE1
        PROXMOX_MASTER --- PROXMOX_NODE2
    end
    
    PHYSICAL --> PROXMOX_MASTER
    PHYSICAL --> PROXMOX_NODE1
    PHYSICAL --> PROXMOX_NODE2
    
    %% VM-Layer
    subgraph VMLayer["VM-Layer"]
        ANSIBLE_VM["Ansible Control Node VM"]
        DOCKER_VM1["Docker Host VM 1"]
        DOCKER_VM2["Docker Host VM 2 (Standby)"]
        STORAGE_VM["Storage VM (NFS)"]
    end
    
    PROXMOX_MASTER --> ANSIBLE_VM
    PROXMOX_NODE1 --> DOCKER_VM1
    PROXMOX_NODE2 --> DOCKER_VM2
    PROXMOX_NODE1 --> STORAGE_VM
    
    %% Docker-Services
    subgraph DockerServices["Docker-Services"]
        DOCKER["Docker Engine"]
        COMPOSE["Docker Compose Stack"]
        
        %% Core Services
        subgraph CoreServices["Core Services"]
            POSTGRES["PostgreSQL"]
            NGINX["NGINX Reverse Proxy"]
        end
        
        %% Anwendungen
        subgraph Applications["Anwendungen"]
            N8N["n8n Workflows"]
            NEXTCLOUD["Nextcloud"]
            CODESERVER["code-server (VS Code)"]
            WORDPRESS["WordPress"]
            MYSQL["MySQL"]
        end
        
        %% Entwicklung
        subgraph Development["Entwicklung"]
            DEV_ENV["Dev Environment Container"]
            NODE["Node.js"]
            VUE["Vue CLI"]
            PYTHON["Python"]
        end
        
        DOCKER --> COMPOSE
        COMPOSE --> POSTGRES
        COMPOSE --> NGINX
        COMPOSE --> N8N
        COMPOSE --> NEXTCLOUD
        COMPOSE --> CODESERVER
        COMPOSE --> WORDPRESS
        COMPOSE --> MYSQL
        COMPOSE --> DEV_ENV
        DEV_ENV --> NODE
        DEV_ENV --> VUE
        DEV_ENV --> PYTHON
        WORDPRESS --> MYSQL
        NEXTCLOUD --> POSTGRES
        N8N --> POSTGRES
    end
    
    DOCKER_VM1 --> DOCKER
    DOCKER_VM2 -.->|Failover| DOCKER
    STORAGE_VM -->|"Persistente Daten"| COMPOSE
    ANSIBLE_VM -->|"Orchestrierung"| DOCKER_VM1
    ANSIBLE_VM -->|"Orchestrierung"| DOCKER_VM2
    
    %% Benutzer-Layer
    subgraph UserLayer["Benutzer-Layer"]
        USER["Endbenutzer"]
        WEB_UI["Web-Interface"]
    end
    
    USER --> WEB_UI
    WEB_UI --> NGINX

    ```

---

## Infrastrukturdesign

### Komponenten und ihre Rollen

#### 1. Proxmox VE
- **Rolle**: Hypervisor für die Virtualisierung
- **Aufgaben**:
  - Bereitstellung virtueller Maschinen für Docker-Hosts
  - Ressourcenverwaltung und -isolation
  - High-Availability-Funktionen für kritische Services
  - Snapshots und Backups der virtuellen Maschinen

#### 2. Ansible Control Node
- **Rolle**: Zentraler Orchestrator für die Infrastruktur
- **Aufgaben**:
  - Automatisierte Bereitstellung von VMs auf Proxmox
  - Konfigurationsmanagement aller Hosts
  - Deployment und Updates der Docker-Container
  - Continuous Deployment der gesamten Infrastruktur

#### 3. Docker Hosts
- **Rolle**: Ausführung der containerisierten Anwendungen
- **Aufgaben**:
  - Bereitstellung der Container-Runtime
  - Isolierung von Anwendungen
  - Ressourcenbegrenzung für Container
  - Optimale Verteilung der Workloads

#### 4. Containerisierte Services
- **PostgreSQL**:
  - Zentrale Datenbank für Nextcloud und n8n
  - Persistente Datenspeicherung
- **n8n**:
  - Automatisierung von Workflows
  - Integration mit externen Diensten
- **Nextcloud**:
  - Dateispeicherung und Zusammenarbeit
  - Kalender, Kontakte, Aufgabenverwaltung
- **code-server**:
  - Webbasierte Entwicklungsumgebung
  - Remote-Zugriff auf Entwicklungsprojekte
- **Dev-Environment**:
  - Vorbereitete Entwicklungsumgebung
  - Node.js, Vue CLI und Python
- **WordPress**:
  - Content-Management-System
  - MySQL-Datenbank für WordPress-Inhalte

---

## Automatisierte Bereitstellung mit Ansible

### Ansible-Verzeichnisstruktur

```
ansible/
├── inventory/
│   ├── hosts.yml               # Host-Definitionen
│   └── group_vars/
│       ├── all.yml             # Globale Variablen
│       ├── docker_hosts.yml    # Variablen für Docker-Hosts
│       └── control_node.yml    # Variablen für Control-Node
├── roles/
│   ├── common/                 # Grundlegende Server-Konfiguration
│   ├── proxmox_vm/             # VM-Erstellung auf Proxmox
│   ├── docker/                 # Docker-Installation und -Konfiguration
│   ├── postgres/               # PostgreSQL-Container-Setup
│   ├── nextcloud/              # Nextcloud-Container-Setup
│   ├── n8n/                    # n8n-Container-Setup
│   ├── code_server/            # Code-Server-Container-Setup
│   ├── dev_environment/        # Dev-Environment-Container-Setup
│   ├── wordpress/              # WordPress-Container-Setup
│   └── nginx/                  # Nginx Reverse Proxy
├── playbooks/
│   ├── site.yml                # Hauptplaybook
│   ├── provision_vms.yml       # VM-Bereitstellung
│   ├── deploy_docker.yml       # Docker-Installation
│   └── deploy_services.yml     # Containerdienste bereitstellen
└── ansible.cfg                 # Ansible-Konfiguration
```

### Ansible-Beispiel-Playbooks

#### 1. Hauptplaybook (site.yml)

```yaml
---
# site.yml - Hauptplaybook, das den vollständigen Bereitstellungsprozess orchestriert

- name: Prepare Control Node
  hosts: control_node
  become: true
  roles:
    - common
    - ansible_controller

- name: Provision VMs in Proxmox
  hosts: proxmox
  roles:
    - proxmox_vm

- name: Configure Docker Hosts
  hosts: docker_hosts
  become: true
  roles:
    - common
    - docker

- name: Deploy Database Services
  hosts: db_hosts
  become: true
  roles:
    - postgres

- name: Deploy Application Services
  hosts: app_hosts
  become: true
  roles:
    - nextcloud
    - n8n
    - code_server
    - dev_environment
    - wordpress
    - nginx
```

#### 2. VM-Bereitstellung in Proxmox (roles/proxmox_vm/tasks/main.yml)

```yaml
---
# VM-Bereitstellung auf Proxmox

- name: Create Docker Host VMs
  proxmox_kvm:
    api_host: "{{ proxmox_host }}"
    api_user: "{{ proxmox_user }}"
    api_password: "{{ proxmox_password }}"
    node: "{{ proxmox_node }}"
    name: "{{ item.name }}"
    memory: "{{ item.memory }}"
    cores: "{{ item.cores }}"
    disk: "{{ item.disk }}"
    ostemplate: "{{ item.template }}"
    netif: "{{ item.network }}"
    state: present
  with_items: "{{ docker_vms }}"
  delegate_to: localhost

- name: Wait for VMs to boot
  wait_for:
    host: "{{ item.ip }}"
    port: 22
    state: started
    timeout: 300
  with_items: "{{ docker_vms }}"
  delegate_to: localhost

- name: Add new VMs to inventory
  add_host:
    name: "{{ item.name }}"
    groups: docker_hosts
    ansible_host: "{{ item.ip }}"
  with_items: "{{ docker_vms }}"
```

#### 3. Docker-Installation (roles/docker/tasks/main.yml)

```yaml
---
# Docker-Installation und -Konfiguration

- name: Install required packages
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg-agent
      - software-properties-common
    state: present
    update_cache: true

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present

- name: Install Docker Engine
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-compose-plugin
    state: present
    update_cache: true

- name: Add user to docker group
  user:
    name: "{{ ansible_user }}"
    groups: docker
    append: true

- name: Create Docker Compose directory
  file:
    path: /opt/docker-compose
    state: directory
    mode: '0755'

- name: Copy Docker Compose files
  template:
    src: "templates/{{ item }}-compose.yml.j2"
    dest: "/opt/docker-compose/{{ item }}-compose.yml"
    mode: '0644'
  with_items: "{{ docker_compose_services }}"
  when: "'{{ item }}' in host_services"
```

#### 4. Service-Deployment (roles/nextcloud/tasks/main.yml)

```yaml
---
# Nextcloud-Bereitstellung

- name: Create data directories for Nextcloud
  file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
    owner: 82
    group: 82
  with_items:
    - /opt/nextcloud/data
    - /opt/nextcloud/config
    - /opt/nextcloud/apps

- name: Generate Nextcloud Docker Compose file
  template:
    src: nextcloud-compose.yml.j2
    dest: /opt/docker-compose/nextcloud-compose.yml
    mode: '0644'

- name: Deploy Nextcloud stack
  community.docker.docker_compose:
    project_src: /opt/docker-compose
    files:
      - nextcloud-compose.yml
    state: present
```

---

## Docker Compose Setup

### 1. PostgreSQL (postgres-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-securedbpassword}
      POSTGRES_DB: ${POSTGRES_DB:-postgres}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  backend:
    driver: bridge

volumes:
  postgres-data:
    driver: local
```

### 2. Nextcloud mit NGINX (nextcloud-compose.yml)

```yaml
version: '3.8'

services:
  nextcloud-app:
    image: nextcloud:latest
    container_name: nextcloud-app
    restart: unless-stopped
    depends_on:
      - postgres
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=${NEXTCLOUD_DB:-nextcloud}
      - POSTGRES_USER=${NEXTCLOUD_DB_USER:-nextcloud}
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD:-nextcloud_password}
      - NEXTCLOUD_ADMIN_USER=${NEXTCLOUD_ADMIN:-admin}
      - NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD:-admin_password}
      - NEXTCLOUD_TRUSTED_DOMAINS=${NEXTCLOUD_DOMAIN:-nextcloud.example.com}
    volumes:
      - nextcloud-data:/var/www/html
      - nextcloud-config:/var/www/html/config
      - nextcloud-apps:/var/www/html/custom_apps
    networks:
      - frontend
      - backend

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - nextcloud-data:/var/www/html:ro
    depends_on:
      - nextcloud-app
    networks:
      - frontend

networks:
  frontend:
    driver: bridge
  backend:
    external: true

volumes:
  nextcloud-data:
  nextcloud-config:
  nextcloud-apps:
```

### 3. n8n (n8n-compose.yml)

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_HOST=${N8N_HOST:-n8n.example.com}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB:-n8n}
      - DB_POSTGRESDB_USER=${N8N_DB_USER:-n8n}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD:-n8n_password}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY:-random_encryption_key}
    volumes:
      - n8n-data:/home/node/.n8n
    networks:
      - frontend
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    external: true

volumes:
  n8n-data:
```

### 4. Code-Server (code-server-compose.yml)

```yaml
version: '3.8'

services:
  code-server:
    image: codercom/code-server:latest
    container_name: code-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PASSWORD=${CODE_SERVER_PASSWORD:-password}
      - HASHED_PASSWORD=${CODE_SERVER_HASHED_PASSWORD}
    volumes:
      - code-server-data:/home/coder/project
      - code-server-config:/home/coder/.config
    networks:
      - frontend
    command: --auth password --user-data-dir /home/coder/.config

networks:
  frontend:
    driver: bridge

volumes:
  code-server-data:
  code-server-config:
```

### 5. WordPress mit MySQL (wordpress-compose.yml)

```yaml
version: '3.8'

services:
  wordpress-db:
    image: mysql:5.7
    container_name: wordpress-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
      MYSQL_DATABASE: ${WORDPRESS_DB_NAME:-wordpress}
      MYSQL_USER: ${WORDPRESS_DB_USER:-wordpress}
      MYSQL_PASSWORD: ${WORDPRESS_DB_PASSWORD:-wordpress_password}
    volumes:
      - wordpress-db-data:/var/lib/mysql
    networks:
      - wp-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  wordpress:
    image: wordpress:latest
    container_name: wordpress
    restart: unless-stopped
    depends_on:
      - wordpress-db
    environment:
      WORDPRESS_DB_HOST: wordpress-db
      WORDPRESS_DB_NAME: ${WORDPRESS_DB_NAME:-wordpress}
      WORDPRESS_DB_USER: ${WORDPRESS_DB_USER:-wordpress}
      WORDPRESS_DB_PASSWORD: ${WORDPRESS_DB_PASSWORD:-wordpress_password}
      WORDPRESS_TABLE_PREFIX: ${WORDPRESS_TABLE_PREFIX:-wp_}
    volumes:
      - wordpress-data:/var/www/html
    ports:
      - "8000:80"
    networks:
      - wp-network
      - frontend

networks:
  wp-network:
    driver: bridge
  frontend:
    external: true

volumes:
  wordpress-db-data:
  wordpress-data:
```

---

## Custom Development Environment

### Development Environment Dockerfile

```dockerfile
# Dev-Environment Dockerfile mit Node.js, Vue CLI und Python
FROM ubuntu:22.04

# Nicht-interaktive Installation
ENV DEBIAN_FRONTEND=noninteractive

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gnupg \
    sudo \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Node.js auf die neueste LTS-Version aktualisieren
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Global npm-Pakete installieren
RUN npm install -g \
    @vue/cli \
    typescript \
    yarn

# Python-Pakete installieren
RUN pip3 install --no-cache-dir \
    virtualenv \
    jupyter \
    numpy \
    pandas \
    matplotlib \
    requests

# Nicht-Root-Benutzer erstellen
RUN useradd -m -s /bin/bash developer \
    && echo "developer ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/developer

# Arbeitsverzeichnis einrichten
WORKDIR /home/developer/projects
RUN chown -R developer:developer /home/developer

# Benutzer wechseln
USER developer

# Umgebungsvariablen setzen
ENV PATH="/home/developer/.local/bin:${PATH}"

# Standard-Startbefehl
CMD ["/bin/bash"]
```

### Dev-Environment-Compose-Datei (dev-environment-compose.yml)

```yaml
version: '3.8'

services:
  dev-environment:
    build:
      context: ./dev-environment
      dockerfile: Dockerfile
    container_name: dev-environment
    restart: unless-stopped
    volumes:
      - dev-projects:/home/developer/projects
      - ~/.ssh:/home/developer/.ssh:ro
    working_dir: /home/developer/projects
    ports:
      - "8081:8081"  # Für Anwendungsentwicklung
    environment:
      - TERM=xterm-256color
    networks:
      - frontend
    command: tail -f /dev/null  # Container laufend halten

networks:
  frontend:
    driver: bridge

volumes:
  dev-projects:
```

---

## Integration und Konfiguration der Services

### NGINX Reverse Proxy Konfiguration

```nginx
# /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name nextcloud.example.com;
    
    ssl_certificate /etc/nginx/ssl/nextcloud.crt;
    ssl_certificate_key /etc/nginx/ssl/nextcloud.key;
    
    location / {
        proxy_pass http://nextcloud-app:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name code.example.com;
    
    ssl_certificate /etc/nginx/ssl/code-server.crt;
    ssl_certificate_key /etc/nginx/ssl/code-server.key;
    
    location / {
        proxy_pass http://code-server:8080;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_set_header Accept-Encoding gzip;
    }
}

server {
    listen 443 ssl;
    server_name n8n.example.com;
    
    ssl_certificate /etc/nginx/ssl/n8n.crt;
    ssl_certificate_key /etc/nginx/ssl/n8n.key;
    
    location / {
        proxy_pass http://n8n:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl;
    server_name wp.example.com;
    
    ssl_certificate /etc/nginx/ssl/wordpress.crt;
    ssl_certificate_key /etc/nginx/ssl/wordpress.key;
    
    location / {
        proxy_pass http://wordpress:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Service-Kommunikationsmatrix

| Service     | Kommuniziert mit  | Port  | Protokoll | Zweck                      |
|-------------|-------------------|-------|-----------|----------------------------|
| Nextcloud   | PostgreSQL        | 5432  | TCP       | Datenbankverbindung        |
| n8n         | PostgreSQL        | 5432  | TCP       | Datenbankverbindung        |
| WordPress   | MySQL             | 3306  | TCP       | Datenbankverbindung        |
| Nginx       | Alle Webservices  | 80/443| TCP       | Reverse Proxy              |
| code-server | Git-Repositories  | 22    | TCP/SSH   | Code-Versionierung         |
| Dev-Env     | code-server       | 8081  | TCP       | Anwendungsentwicklung      |

### Sicherheitskonfiguration

1. **Docker Netzwerksicherheit**:
   - Trennung von Frontend- und Backend-Netzwerken
   - Expose nur notwendiger Ports nach außen

2. **Verschlüsselung**:
   - SSL/TLS für alle Webservices
   - Datenbankverschlüsselung für sensible Daten

3. **Benutzerauthentifizierung**:
   - Starke Passwörter für alle Services
   - Verwendung von Umgebungsvariablen für Anmeldeinformationen

4. **Volume-Sicherheit**:
   - Korrekte Berechtigungen für alle Container-Volumes
   - Regelmäßige Backups der persistenten Daten

### Backup-Strategie

1. **Proxmox-Backups**:
   - Regelmäßige VM-Snapshots
   - Vollständige VM-Backups

2. **Docker-Volume-Backups**:
   - Automatisierte Sicherung mit Ansible
   - Skript-Beispiel:

```bash
#!/bin/bash
# Backup Docker-Volumes

BACKUP_DIR="/backups/docker-volumes"
DATE=$(date +%Y-%m-%d)

mkdir -p $BACKUP_DIR/$DATE

# Postgres Backup
docker exec postgres pg_dumpall -U postgres > $BACKUP_DIR/$DATE/postgres_all.sql

# Nextcloud-Daten
docker run --rm -v nextcloud-data:/source -v $BACKUP_DIR/$DATE:/backup \
  ubuntu tar -czf /backup/nextcloud-data.tar.gz -C /source .

# WordPress-Daten
docker run --rm -v wordpress-data:/source -v $BACKUP_DIR/$DATE:/backup \
  ubuntu tar -czf /backup/wordpress-data.tar.gz -C /source .

# n8n-Daten
docker run --rm -v n8n-data:/source -v $BACKUP_DIR/$DATE:/backup \
  ubuntu tar -czf /backup/n8n-data.tar.gz -C /source .

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
```

---

## Implementierungsleitfaden

1. **Proxmox-Installation**:
   - Proxmox VE auf dem Hostsystem installieren
   - Netzwerk und Speicher konfigurieren

2. **Control Node einrichten**:
   - Ubuntu-VM erstellen
   - Ansible und Git installieren
   - Repository mit allen Playbooks und Konfigurationen klonen

3. **Ansible-Playbooks ausführen**:
   ```bash
   # VM-Bereitstellung
   ansible-playbook playbooks/provision_vms.yml
   
   # Docker-Installation
   ansible-playbook playbooks/deploy_docker.yml
   
   # Services-Deployment
   ansible-playbook playbooks/deploy_services.yml
   ```

4. **Dienste testen und konfigurieren**:
   - Alle Webschnittstellen über die konfigurierten Domain-Namen prüfen
   - Integrationen zwischen den Diensten einrichten
   - Backup-Strategie implementieren

Diese Dokumentation bietet einen umfassenden Leitfaden für die Implementierung einer automatisierten, containerisierten Infrastruktur mit Proxmox, Ansible und Docker. Die bereitgestellten Code-Beispiele, Konfigurationen und Diagramme ermöglichen eine strukturierte und nachhaltige Umsetzung des gesamten Projekts.
