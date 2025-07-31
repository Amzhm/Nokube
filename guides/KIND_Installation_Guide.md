# Guide d'installation de Kind sur macOS

## Vue d'ensemble
Kind (Kubernetes in Docker) permet de créer des clusters Kubernetes locaux en utilisant des conteneurs Docker comme nœuds. Ce guide détaille l'installation complète sur macOS et la création d'un cluster avec 1 master et 2 workers.

## Prérequis

### 1. Vérification de Docker
```bash
# Vérifier que Docker est installé et fonctionne
docker --version
docker info
```

### 2. Vérification des ressources système
```bash
# Vérifier l'espace disque disponible (minimum 10GB recommandé)
df -h

# Vérifier la mémoire disponible (minimum 4GB recommandé)
free -m  # ou sur macOS: vm_stat
```

## Installation de Kind

### Option 1: Installation avec Homebrew (Recommandée)
```bash
# Installer Kind via Homebrew
brew install kind

# Vérifier l'installation
kind version
```

### Option 2: Installation manuelle
```bash
# Télécharger le binaire Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-darwin-amd64

# Rendre le binaire exécutable
chmod +x ./kind

# Déplacer vers un répertoire dans le PATH
sudo mv ./kind /usr/local/bin/kind

# Vérifier l'installation
kind version
```

## Installation de kubectl

### Via Homebrew
```bash
# Installer kubectl
brew install kubectl

# Vérifier l'installation
kubectl version --client
```

### Installation manuelle
```bash
# Télécharger kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"

# Rendre exécutable
chmod +x ./kubectl

# Déplacer vers le PATH
sudo mv ./kubectl /usr/local/bin/kubectl

# Vérifier
kubectl version --client
```

## Configuration du cluster multi-nœuds

### 1. Créer le fichier de configuration
```bash
# Créer le fichier kind-config.yaml
cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: Local-cluster
nodes:
- role: control-plane
  image: kindest/node:v1.28.0
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
  image: kindest/node:v1.28.0
- role: worker
  image: kindest/node:v1.28.0
EOF
```

### 2. Créer le cluster
```bash
# Créer le cluster avec la configuration
kind create cluster --config kind-config.yaml

# Attendre que le cluster soit prêt (peut prendre quelques minutes)
kubectl wait --for=condition=Ready nodes --all --timeout=300s
```

## Tests de vérification

### 1. Vérification de l'état du cluster
```bash
# Vérifier les nœuds
kubectl get nodes -o wide

# Vérifier les pods système
kubectl get pods -A

# Vérifier la santé du cluster
kubectl cluster-info

# Vérifier les composants du control plane
kubectl get componentstatuses
```

### 2. Test de déploiement simple
```bash
# Déployer une application de test
kubectl create deployment nginx-test --image=nginx:latest

# Exposer le service
kubectl expose deployment nginx-test --port=80 --type=NodePort

# Vérifier le déploiement
kubectl get deployments
kubectl get services
kubectl get pods

# Obtenir l'URL du service
kubectl get svc nginx-test
```

### 3. Test de connectivité réseau
```bash
# Tester la communication inter-pods
kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default

# Tester l'accès aux services
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- curl nginx-test
```

### 4. Test de persistance des données
```bash
# Créer un PVC de test
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Vérifier le PVC
kubectl get pvc
```

## Commandes utiles

### Gestion du cluster
```bash
# Lister les clusters
kind get clusters

# Obtenir la configuration kubeconfig
kind get kubeconfig --name dev-cluster

# Supprimer le cluster
kind delete cluster --name dev-cluster

# Charger une image Docker dans le cluster
kind load docker-image <image-name> --name dev-cluster
```

### Debugging
```bash
# Logs des conteneurs Kind
docker logs <container-name>

# Accéder à un nœud
docker exec -it <node-container> bash

# Vérifier les logs des pods
kubectl logs <pod-name> -n <namespace>

# Décrire un objet Kubernetes
kubectl describe <resource> <name>
```

## Dépannage courant

### 1. Erreur "Cannot connect to the Docker daemon"
```bash
# Vérifier que Docker est démarré
brew services start docker
# ou redémarrer Docker Desktop
```

### 2. Erreur de port déjà utilisé
```bash
# Vérifier les ports utilisés
lsof -i :80
lsof -i :443

# Tuer les processus si nécessaire
sudo kill -9 <PID>
```

### 3. Problème de ressources insuffisantes
```bash
# Nettoyer les images Docker inutilisées
docker system prune -a

# Augmenter les ressources Docker (via Docker Desktop)
```

### 4. Problème de résolution DNS
```bash
# Redémarrer le service DNS du cluster
kubectl rollout restart deployment/coredns -n kube-system
```

## Nettoyage

### Supprimer les ressources de test
```bash
# Supprimer les déploiements de test
kubectl delete deployment nginx-test
kubectl delete service nginx-test
kubectl delete pvc test-pvc
```

### Supprimer complètement le cluster
```bash
# Supprimer le cluster Kind
kind delete cluster --name dev-cluster

# Nettoyer les images Docker (optionnel)
docker system prune -f
```

## Conseils de performance

1. **Ressources système** : Allouez au moins 4GB de RAM et 2 CPU à Docker
2. **Stockage** : Utilisez un SSD pour de meilleures performances
3. **Images** : Pré-téléchargez les images couramment utilisées
4. **Monitoring** : Utilisez `kubectl top nodes` et `kubectl top pods` pour surveiller les ressources

## Ressources supplémentaires

- [Documentation officielle Kind](https://kind.sigs.k8s.io/)
- [Guide Kubernetes](https://kubernetes.io/docs/)
- [Référence kubectl](https://kubernetes.io/docs/reference/kubectl/)