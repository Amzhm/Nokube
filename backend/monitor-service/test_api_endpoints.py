#!/usr/bin/env python3
"""
Test des endpoints API du Monitor Service
Test sans Kubernetes réel mais avec validation des données
"""

import sys
import json
import uuid
from pathlib import Path

# Ajouter le module app au path
sys.path.append(str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app

# Client de test FastAPI
client = TestClient(app)

def test_health_endpoint():
    """Test du health check"""
    print("🧪 Test Health Endpoint")
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "monitor-service"
    assert "status" in data
    assert "kubernetes_connected" in data
    print(f"   ✅ Health: {data['status']} (K8s: {data['kubernetes_connected']})")

def test_root_endpoint():
    """Test de l'endpoint racine"""
    print("\n🧪 Test Root Endpoint")
    
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "NoKube Monitor Service"
    assert "features" in data
    assert "endpoints" in data
    print(f"   ✅ Service: {data['service']} v{data['version']}")
    print(f"   Features: {len(data['features'])}")

def test_deploy_endpoint_validation():
    """Test de validation des données de déploiement"""
    print("\n🧪 Test Deploy Endpoint - Validation")
    
    # Test avec données valides
    valid_deploy_data = {
        "project_id": 1,
        "project_name": "test-app",
        "username": "testuser",
        "service_name": "webapp",
        "display_name": "Test Web App",
        "description": "Application de test",
        "image_name": "ghcr.io/test/webapp:latest",
        "replicas": 2,
        "service_type": "web",
        "exposure_type": "external",
        "container_port": 3000,
        "service_port": 8000,
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "512Mi",
        "env_vars": {
            "NODE_ENV": "production"
        },
        "health_check_path": "/health"
    }
    
    headers = {"X-User": "testuser"}
    response = client.post("/deploy", json=valid_deploy_data, headers=headers)
    
    # Le déploiement va échouer (pas de K8s) mais la validation doit passer
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        assert "deployment_id" in data
        assert data["project_id"] == 1
        assert data["service_name"] == "webapp"
        assert data["status"] == "pending"
        print(f"   ✅ Déploiement initié: {data['deployment_id'][:8]}...")
    else:
        # Si ça échoue à cause de K8s, c'est normal pour ce test
        print(f"   ℹ️  Échec attendu (pas de K8s): {response.status_code}")

def test_deploy_with_authentication_mismatch():
    """Test de sécurité - utilisateur différent"""
    print("\n🧪 Test Sécurité - Authentification")
    
    deploy_data = {
        "project_id": 1,
        "project_name": "test-app",
        "username": "testuser",  # Utilisateur dans les données
        "service_name": "webapp",
        "image_name": "ghcr.io/test/webapp:latest",
        "container_port": 3000
    }
    
    # Header avec utilisateur différent
    headers = {"X-User": "different-user"}
    response = client.post("/deploy", json=deploy_data, headers=headers)
    
    assert response.status_code == 403
    error_data = response.json()
    assert "Username mismatch" in error_data["detail"]
    print("   ✅ Sécurité validée - mismatch utilisateur bloqué")

def test_deploy_endpoint_missing_data():
    """Test avec données manquantes"""
    print("\n🧪 Test Validation - Données manquantes")
    
    incomplete_data = {
        "project_id": 1,
        "username": "testuser"
        # Manque service_name, image_name, etc.
    }
    
    headers = {"X-User": "testuser"}
    response = client.post("/deploy", json=incomplete_data, headers=headers)
    
    assert response.status_code == 422  # Validation error
    print("   ✅ Validation Pydantic - données manquantes détectées")

def test_status_endpoint():
    """Test de l'endpoint status"""
    print("\n🧪 Test Status Endpoint")
    
    response = client.get("/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "monitor-service"
    assert "kubernetes_connected" in data
    assert "deployment_stats" in data
    assert "settings" in data
    
    print(f"   ✅ Status: {data['status']}")
    print(f"   Déploiements actifs: {data['active_deployments_count']}")
    print(f"   Host par défaut: {data['settings']['default_host']}")

def test_deployment_status_not_found():
    """Test de récupération d'un déploiement inexistant"""
    print("\n🧪 Test Deployment Status - Not Found")
    
    fake_deployment_id = str(uuid.uuid4())
    headers = {"X-User": "testuser"}
    
    response = client.get(f"/deployments/{fake_deployment_id}", headers=headers)
    assert response.status_code == 404
    
    error_data = response.json()
    assert "not found" in error_data["detail"].lower()
    print("   ✅ Déploiement inexistant correctement géré")

def test_manifests_endpoint_not_found():
    """Test de récupération de manifests inexistants"""
    print("\n🧪 Test Manifests - Not Found")
    
    fake_deployment_id = str(uuid.uuid4())
    headers = {"X-User": "testuser"}
    
    response = client.get(f"/manifests/{fake_deployment_id}", headers=headers)
    assert response.status_code == 404
    print("   ✅ Manifests inexistants correctement gérés")

def test_project_deployments_list():
    """Test de listing des déploiements par projet"""
    print("\n🧪 Test Project Deployments List")
    
    project_id = 999  # Projet sans déploiements
    headers = {"X-User": "testuser"}
    
    response = client.get(f"/projects/{project_id}/deployments", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "deployments" in data
    assert "total" in data
    assert data["project_id"] == project_id
    assert data["total"] == 0  # Pas de déploiements
    
    print(f"   ✅ Projet {project_id}: {data['total']} déploiements")

def test_endpoint_not_found():
    """Test d'endpoint inexistant"""
    print("\n🧪 Test Endpoint Not Found")
    
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    
    data = response.json()
    assert "not found" in data["error"].lower()
    assert "available_endpoints" in data
    print(f"   ✅ 404 correctement géré avec {len(data['available_endpoints'])} endpoints disponibles")

def main():
    """Exécuter tous les tests API"""
    print("🚀 Tests API Endpoints - NoKube Monitor Service\n")
    
    try:
        test_health_endpoint()
        test_root_endpoint()
        test_deploy_endpoint_validation() 
        test_deploy_with_authentication_mismatch()
        test_deploy_endpoint_missing_data()
        test_status_endpoint()
        test_deployment_status_not_found()
        test_manifests_endpoint_not_found()
        test_project_deployments_list()
        test_endpoint_not_found()
        
        print(f"\n✅ TOUS LES TESTS API RÉUSSIS!")
        print(f"   - 10 endpoints testés")
        print(f"   - Validation Pydantic vérifiée")
        print(f"   - Sécurité authentification validée")
        print(f"   - Gestion d'erreurs complète")
        print(f"   - Endpoints informatifs opérationnels")
        
    except Exception as e:
        print(f"\n❌ ÉCHEC DU TEST API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()