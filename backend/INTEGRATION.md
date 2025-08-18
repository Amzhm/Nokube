# Intégration Build Service ↔ Monitor Service

## 🔄 Workflow Utilisateur Complet

### Phase 1: Build
```
Frontend → API Gateway → Build Service → GitHub Actions → GHCR
```

**1. User initie le build**
- Frontend envoie `POST /api/v1/builds`
- Build Service retourne `BuildResponse` avec `build_id` et `image_full_name`

**2. Suivi du build**  
- Frontend poll `GET /api/v1/builds/{build_id}` 
- Status: `pending` → `building` → `success`/`failed`

**3. Build réussi**
- Status = `success`
- `image_full_name` disponible (ex: `ghcr.io/amzhm/user-project-service:latest`)

### Phase 2: Deploy (Manuel via Bouton)
```
Frontend → API Gateway → Monitor Service → Kubernetes
```

**4. User clique "Deploy"**
- Frontend affiche formulaire de déploiement
- Champs pré-remplis depuis le build + configuration utilisateur

**5. User configure le déploiement**
- Replicas, CPU, RAM, ports, exposition, variables d'env, etc.
- `image_name` = `image_full_name` du build réussi

**6. Déploiement Kubernetes**
- Frontend envoie `POST /api/v1/deploy`
- Monitor Service génère manifests + déploie sur K8s

## 📋 Données Échangées

### Build Service → Frontend
```json
{
  "build_id": "abc-123",
  "project_id": 1,
  "status": "success",
  "image_full_name": "ghcr.io/amzhm/testuser-myapp-frontend:latest",
  "service_name": "frontend",
  "completed_at": "2025-08-18T10:30:00Z"
}
```

### Frontend → Monitor Service  
```json
{
  "project_id": 1,
  "project_name": "myapp",
  "username": "testuser",
  "service_name": "frontend",
  "image_name": "ghcr.io/amzhm/testuser-myapp-frontend:latest",
  "replicas": 2,
  "container_port": 3000,
  "service_port": 8000,
  "exposure_type": "external",
  "cpu_request": "100m",
  "memory_request": "256Mi"
}
```

## 🎯 Avantages de cette Architecture

### ✅ Contrôle Utilisateur
- User voit le build terminé avant de décider de déployer
- Configuration de déploiement personnalisable
- Pas de déploiement automatique non désiré

### ✅ Découplage des Services  
- Build Service se concentre sur le build uniquement
- Monitor Service se concentre sur le déploiement uniquement  
- Frontend orchestre le workflow

### ✅ Gestion d'Erreurs
- Build échoué ≠ pas de déploiement
- Déploiement échoué ≠ rebuild requis
- Chaque phase indépendante

### ✅ Flexibilité
- Possible de redéployer la même image avec config différente
- Possible de déployer des images externes (pas buildées par NoKube)
- User peut choisir quand déployer

## 🔗 Interface Frontend

### Page Build
```
✅ Build réussi! 
Image: ghcr.io/amzhm/testuser-myapp-frontend:latest
Durée: 2m 34s

[Voir les logs] [🚀 Déployer maintenant]
```

### Page Deploy  
```
Déployer: testuser-myapp-frontend:latest

Configuration:
- Replicas: [2] 
- CPU: [100m] / [500m]
- RAM: [256Mi] / [512Mi]
- Port container: [3000]
- Exposition: [✓] Internet [ ] Interne seulement

Variables d'environnement:
NODE_ENV=production
API_URL=http://backend-service:8000

[Annuler] [🚀 Déployer sur Kubernetes]
```

## 🏗️ État Actuel

### ✅ Implémenté
- **Build Service**: Endpoint `/builds` opérationnel  
- **Monitor Service**: Endpoint `/deploy` opérationnel
- **Schémas compatibles**: `image_full_name` partagée
- **Génération manifests**: Validée avec tests complets
- **API Gateway**: Routage Build/Monitor opérationnel

### 🔄 À implémenter (Frontend)
- Interface "Build réussi" avec bouton Deploy
- Formulaire configuration déploiement
- Intégration Monitor Service pour déploiement
- Suivi du statut de déploiement

**L'intégration backend est complète et prête pour le Frontend !**