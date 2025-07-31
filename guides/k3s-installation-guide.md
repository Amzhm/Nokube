# Guide d'installation K3s sur AWS EC2

## Prérequis
- 3 instances EC2 t3.micro (1 vCPU, 1 GiB RAM)
- OS : Ubuntu 22.04 LTS (AMI gratuite)
- Security Groups configurés
- Clés SSH configurées

## Architecture finale
```
k3s-master   (10.0.1.10) - Master node
k3s-worker-1 (10.0.1.11) - Worker node  
k3s-worker-2 (10.0.1.12) - Worker node
```

---

## Étape 1 : Création des instances EC2

### 1.1 Lancement des instances
```bash
# Depuis AWS Console ou CLI
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \  # Ubuntu 22.04 LTS
  --count 3 \
  --instance-type t3.micro \
  --key-name ma-cle-ssh \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --associate-public-ip-address
```

### 1.2 Configuration Security Group
```bash
# Ports requis pour K3s
Port 22    (SSH)           - 0.0.0.0/0
Port 6443  (K3s API)       - VPC CIDR (10.0.0.0/16)
Port 10250 (Kubelet)       - VPC CIDR (10.0.0.0/16)
Port 8472  (Flannel VXLAN) - VPC CIDR (10.0.0.0/16)
Port 51820 (Flannel WG)    - VPC CIDR (10.0.0.0/16)
Port 80    (HTTP)          - 0.0.0.0/0
Port 443   (HTTPS)         - 0.0.0.0/0
```

### 1.3 Tag des instances
```
k3s-master   : Name=k3s-master
k3s-worker-1 : Name=k3s-worker-1  
k3s-worker-2 : Name=k3s-worker-2
```

---

## Étape 2 : Configuration système (toutes les instances)

### 2.1 Connexion SSH et mise à jour
```bash
# Pour chaque instance
ssh -i ma-cle.pem ubuntu@IP_PUBLIQUE

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation outils de base
sudo apt install -y curl wget htop net-tools
```

### 2.2 Configuration hostname et hosts
```bash
# Sur k3s-master
sudo hostnamectl set-hostname k3s-master

# Sur k3s-worker-1
sudo hostnamectl set-hostname k3s-worker-1

# Sur k3s-worker-2  
sudo hostnamectl set-hostname k3s-worker-2

# Sur TOUTES les instances, ajouter dans /etc/hosts
sudo tee -a /etc/hosts << EOF
10.0.1.10 k3s-master
10.0.1.11 k3s-worker-1
10.0.1.12 k3s-worker-2
EOF
```

### 2.3 Désactiver swap (si activé)
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

### 2.4 Configuration réseau
```bash
# Autoriser le forwarding IP
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## Étape 3 : Installation K3s Master

### 3.1 Installation sur k3s-master
```bash
# Connexion SSH sur le master
ssh -i ma-cle.pem ubuntu@IP_MASTER

# Installation K3s server
curl -sfL https://get.k3s.io | sh -s - server \
  --node-ip=10.0.1.10 \
  --cluster-init \
  --disable traefik \
  --disable servicelb \
  --write-kubeconfig-mode 644

# Vérification
sudo systemctl status k3s
```

### 3.2 Récupération du token et kubeconfig
```bash
# Token pour joindre les workers
sudo cat /var/lib/rancher/k3s/server/node-token

# Kubeconfig pour kubectl
sudo cat /etc/rancher/k3s/k3s.yaml

# Test kubectl
sudo k3s kubectl get nodes
```

### 3.3 Installation kubectl (optionnel)
```bash
# Installation kubectl standalone
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Configuration
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Test
kubectl get nodes
```

---

## Étape 4 : Installation K3s Workers

### 4.1 Installation sur k3s-worker-1
```bash
# Connexion SSH sur worker-1
ssh -i ma-cle.pem ubuntu@IP_WORKER_1

# Installation K3s agent
curl -sfL https://get.k3s.io | K3S_URL=https://10.0.1.10:6443 \
  K3S_TOKEN="TOKEN_RECUPERE_DU_MASTER" sh -s - agent \
  --node-ip=10.0.1.11

# Vérification
sudo systemctl status k3s-agent
```

### 4.2 Installation sur k3s-worker-2
```bash
# Connexion SSH sur worker-2
ssh -i ma-cle.pem ubuntu@IP_WORKER_2

# Installation K3s agent
curl -sfL https://get.k3s.io | K3S_URL=https://10.0.1.10:6443 \
  K3S_TOKEN="TOKEN_RECUPERE_DU_MASTER" sh -s - agent \
  --node-ip=10.0.1.12

# Vérification  
sudo systemctl status k3s-agent
```

---

## Étape 5 : Vérification du cluster

### 5.1 Vérification depuis le master
```bash
# Retour sur le master
ssh -i ma-cle.pem ubuntu@IP_MASTER

# Vérifier tous les nodes
kubectl get nodes -o wide

# Doit afficher :
# NAME           STATUS   ROLES                  AGE   VERSION
# k3s-master     Ready    control-plane,master   5m    v1.28.x+k3s1
# k3s-worker-1   Ready    <none>                 3m    v1.28.x+k3s1  
# k3s-worker-2   Ready    <none>                 2m    v1.28.x+k3s1

# Vérifier les pods système
kubectl get pods -A

# Test de déploiement
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=NodePort
kubectl get services
```

---

## Étape 6 : Installation composants essentiels

### 6.1 NGINX Ingress Controller
```bash
# Installation
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Vérification
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 6.2 Metrics Server (pour HPA)
```bash
# Installation
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch pour ignorer TLS (développement)
kubectl patch deployment metrics-server -n kube-system --type='merge' -p='{"spec":{"template":{"spec":{"containers":[{"name":"metrics-server","args":["--cert-dir=/tmp","--secure-port=4443","--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname","--kubelet-use-node-status-port","--metric-resolution=15s","--kubelet-insecure-tls"]}]}}}}'

# Test
kubectl top nodes
```

---

## Étape 7 : Configuration accès externe

### 7.1 Kubeconfig local (sur ton Mac)
```bash
# Copier le kubeconfig depuis le master
scp -i ma-cle.pem ubuntu@IP_MASTER:/etc/rancher/k3s/k3s.yaml ./k3s-config.yaml

# Modifier l'IP dans le fichier
sed -i 's/127.0.0.1/IP_PUBLIQUE_MASTER/g' k3s-config.yaml

# Utiliser le config
export KUBECONFIG=./k3s-config.yaml
kubectl get nodes
```

### 7.2 Dashboard K8s (optionnel)
```bash
# Installation
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Création utilisateur admin (DÉVELOPPEMENT SEULEMENT)
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Récupérer le token
kubectl -n kubernetes-dashboard create token admin-user

# Port-forward pour accès
kubectl proxy --port=8080 &
# Accès via : http://localhost:8080/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

---

## Étape 8 : Tests et dépannage

### 8.1 Tests de base
```bash
# Test déploiement multi-répliques
kubectl create deployment test-app --image=nginx --replicas=3
kubectl get pods -o wide
kubectl scale deployment test-app --replicas=6

# Test networking
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
# Dans le pod : nslookup kubernetes.default.svc.cluster.local
```

### 8.2 Commandes de dépannage
```bash
# Logs K3s master
sudo journalctl -u k3s -f

# Logs K3s workers
sudo journalctl -u k3s-agent -f

# État des services
sudo systemctl status k3s        # Sur master
sudo systemctl status k3s-agent  # Sur workers

# Redémarrage si nécessaire
sudo systemctl restart k3s       # Sur master
sudo systemctl restart k3s-agent # Sur workers

# Vérification réseau
sudo ss -tulpn | grep :6443
sudo iptables -L -n | grep 6443
```

---

## Étape 9 : Optimisations pour t3.micro

### 9.1 Configuration memory/CPU limits
```bash
# Éditer la configuration K3s pour optimiser
sudo nano /etc/systemd/system/k3s.service

# Ajouter dans ExecStart :
--kube-apiserver-arg=--max-requests-inflight=100 \
--kube-apiserver-arg=--max-mutating-requests-inflight=50 \
--kubelet-arg=--max-pods=50

# Recharger et redémarrer
sudo systemctl daemon-reload
sudo systemctl restart k3s
```

### 9.2 Monitoring ressources
```bash
# Script de monitoring (créer monitoring.sh)
#!/bin/bash
echo "=== NODES RESOURCES ==="
kubectl top nodes

echo "=== PODS RESOURCES ==="
kubectl top pods -A

echo "=== SYSTEM MEMORY ==="
free -h

echo "=== SYSTEM CPU ==="
uptime
```

---

## Troubleshooting courants

### Problème : Nodes pas Ready
```bash
# Vérifier logs
sudo journalctl -u k3s -n 50
# Souvent : problème réseau ou DNS
```

### Problème : Pods en Pending
```bash
# Vérifier ressources
kubectl describe node k3s-worker-1
# Souvent : pas assez de CPU/RAM
```

### Problème : Connexion refusée
```bash
# Vérifier Security Groups AWS
# Vérifier firewall Ubuntu
sudo ufw status
```

## Conclusion

Ton cluster K3s est maintenant prêt ! Tu peux commencer à déployer tes microservices pour le portail.

**Prochaines étapes :**
1. Installer ArgoCD
2. Configurer Tekton  
3. Déployer ton premier microservice

Les ressources sont justes mais suffisantes pour un projet de développement. Surveille la consommation avec `kubectl top nodes` !