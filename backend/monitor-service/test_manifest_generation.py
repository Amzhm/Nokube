#!/usr/bin/env python3
"""
Script de test pour valider la génération des manifests Kubernetes
Cas d'usage réels du Monitor Service NoKube
"""

import sys
import json
import yaml
from pathlib import Path

# Ajouter le module app au path
sys.path.append(str(Path(__file__).parent))

from app.schemas import DeployRequest, ServiceType, ExposureType
from app.manifest_generator import manifest_generator

def test_web_frontend_deployment():
    """Test 1: Déploiement d'un frontend React/Next.js exposé publiquement"""
    print("🧪 Test 1: Frontend React exposé (avec Ingress)")
    
    deploy_request = DeployRequest(
        # Informations projet
        project_id=1,
        project_name="ecommerce-app", 
        username="testuser2",
        service_name="frontend",
        display_name="E-commerce Frontend",
        description="Interface React pour l'application e-commerce",
        
        # Image buildée par Build Service
        image_name="ghcr.io/amzhm/testuser2-ecommerce-app-frontend:latest",
        
        # Configuration déploiement
        replicas=2,
        service_type=ServiceType.WEB,
        exposure_type=ExposureType.EXTERNAL,
        
        # Ports : Container écoute sur 3000, Service sur 8000
        container_port=3000,
        service_port=8000,
        
        # Ressources
        cpu_request="200m",
        cpu_limit="1000m", 
        memory_request="256Mi",
        memory_limit="1Gi",
        
        # Variables d'environnement
        env_vars={
            "NODE_ENV": "production",
            "API_BASE_URL": "http://backend-service:8000/api",
            "NEXT_PUBLIC_APP_NAME": "NoKube E-commerce"
        },
        
        # Health checks
        health_check_path="/",
        startup_timeout=60,
        
        # DNS et exposition
        custom_domain="nokube.local",
        enable_https=False
    )
    
    # Générer les manifests
    deployment_id = "test-frontend-001"
    manifests = manifest_generator.generate_manifests(deploy_request, deployment_id)
    
    print(f"✅ Générés: {list(manifests.keys())}")
    
    # Valider le namespace
    assert "namespace" in manifests
    ns_manifest = yaml.safe_load(manifests["namespace"])
    expected_namespace = "testuser2-ecommerce-app"
    assert ns_manifest["metadata"]["name"] == expected_namespace
    print(f"   Namespace: {expected_namespace}")
    
    # Valider l'Ingress (exposition externe)
    assert "ingress" in manifests
    ingress_manifest = yaml.safe_load(manifests["ingress"])
    expected_path = "/testuser2/ecommerce-app/frontend"
    rules = ingress_manifest["spec"]["rules"][0]["http"]["paths"]
    assert rules[0]["path"] == f"{expected_path}/(.*)"
    print(f"   URL d'accès: http://nokube.local{expected_path}")
    
    # Valider le ConfigMap
    assert "configmap" in manifests
    cm_manifest = yaml.safe_load(manifests["configmap"])
    assert cm_manifest["data"]["NODE_ENV"] == "production"
    assert "INTERNAL_SERVICE_URL" in cm_manifest["data"]
    print(f"   Variables env: {len(deploy_request.env_vars)} configurées")
    
    return manifests, expected_namespace

def test_backend_api_deployment():
    """Test 2: Déploiement d'un backend API exposé seulement en interne"""
    print("\n🧪 Test 2: Backend API interne (sans Ingress)")
    
    deploy_request = DeployRequest(
        # Informations projet (même projet que le frontend)
        project_id=1,
        project_name="ecommerce-app",
        username="testuser2", 
        service_name="backend",
        display_name="E-commerce API",
        description="API REST pour l'application e-commerce",
        
        # Image
        image_name="ghcr.io/amzhm/testuser2-ecommerce-app-backend:latest",
        
        # Configuration
        replicas=3,
        service_type=ServiceType.API,
        exposure_type=ExposureType.INTERNAL,  # Pas d'Ingress
        
        # Ports
        container_port=8000,
        service_port=8000,
        
        # Ressources plus importantes pour l'API
        cpu_request="300m",
        cpu_limit="1500m",
        memory_request="512Mi", 
        memory_limit="2Gi",
        
        # Variables d'environnement
        env_vars={
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://user:pass@db:5432/ecommerce"
        },
        
        # Secrets (données sensibles)
        secrets={
            "JWT_SECRET": "am13dF9zZWNyZXRfa2V5XzEyMw==",  # Base64 encoded
            "DB_PASSWORD": "c2VjdXJlX3Bhc3N3b3JkXzQ1Ng=="
        },
        
        # Health checks
        health_check_path="/health",
        startup_timeout=45,
        
        # Stockage pour logs/cache
        storage_size="5Gi",
        storage_path="/app/data",
        
        # Autoscaling
        enable_autoscaling=True,
        min_replicas=2,
        max_replicas=8,
        target_cpu_percent=75
    )
    
    deployment_id = "test-backend-001" 
    manifests = manifest_generator.generate_manifests(deploy_request, deployment_id)
    
    print(f"✅ Générés: {list(manifests.keys())}")
    
    # Doit être dans le même namespace que le frontend
    ns_manifest = yaml.safe_load(manifests["namespace"])
    assert ns_manifest["metadata"]["name"] == "testuser2-ecommerce-app"
    
    # PAS d'Ingress (exposition interne seulement)
    assert "ingress" not in manifests
    print("   ✅ Pas d'Ingress (exposition interne)")
    
    # Valider Service interne
    assert "service" in manifests
    svc_manifest = yaml.safe_load(manifests["service"])
    assert svc_manifest["metadata"]["name"] == "backend-service"
    assert svc_manifest["spec"]["type"] == "ClusterIP"
    print("   Service interne: backend-service:8000")
    
    # Valider Secret
    assert "secret" in manifests 
    secret_manifest = yaml.safe_load(manifests["secret"])
    assert "JWT_SECRET" in secret_manifest["data"]
    print(f"   Secrets: {len(deploy_request.secrets)} configurés")
    
    # Valider PVC
    assert "pvc" in manifests
    pvc_manifest = yaml.safe_load(manifests["pvc"])
    assert pvc_manifest["spec"]["resources"]["requests"]["storage"] == "5Gi"
    print("   Stockage: 5Gi PVC configuré")
    
    # Valider HPA
    assert "hpa" in manifests
    hpa_manifest = yaml.safe_load(manifests["hpa"])
    assert hpa_manifest["spec"]["minReplicas"] == 2
    assert hpa_manifest["spec"]["maxReplicas"] == 8
    print("   Autoscaling: 2-8 replicas (75% CPU)")
    
    return manifests

def test_worker_deployment():
    """Test 3: Déploiement d'un worker/job sans réseau"""
    print("\n🧪 Test 3: Worker/Job (aucune exposition réseau)")
    
    deploy_request = DeployRequest(
        # Nouveau projet pour un worker
        project_id=2,
        project_name="data-pipeline",
        username="devuser",
        service_name="processor",
        display_name="Data Processor",
        description="Worker pour traitement des données",
        
        # Image
        image_name="ghcr.io/amzhm/devuser-data-pipeline-processor:latest",
        
        # Configuration worker
        replicas=1,
        service_type=ServiceType.WORKER,
        exposure_type=ExposureType.NONE,  # Aucun Service ni Ingress
        
        # Ports (pas utilisés mais requis par le schéma)
        container_port=8080,
        
        # Ressources pour traitement intensif
        cpu_request="500m",
        cpu_limit="2000m",
        memory_request="1Gi",
        memory_limit="4Gi",
        
        # Variables d'environnement
        env_vars={
            "WORKER_MODE": "batch",
            "BATCH_SIZE": "1000",
            "REDIS_URL": "redis://redis:6379/0"
        },
        
        # Stockage important pour les données
        storage_size="20Gi", 
        storage_path="/data",
        
        # Health check modifié (pas de réseau)
        health_check_path="/health",
        startup_timeout=30
    )
    
    deployment_id = "test-worker-001"
    manifests = manifest_generator.generate_manifests(deploy_request, deployment_id)
    
    print(f"✅ Générés: {list(manifests.keys())}")
    
    # Nouveau namespace pour ce projet
    ns_manifest = yaml.safe_load(manifests["namespace"])
    expected_namespace = "devuser-data-pipeline"
    assert ns_manifest["metadata"]["name"] == expected_namespace
    print(f"   Namespace: {expected_namespace}")
    
    # PAS de Service ni Ingress (worker sans réseau)
    assert "service" not in manifests
    assert "ingress" not in manifests
    print("   ✅ Aucune exposition réseau (worker)")
    
    # Valider Deployment
    assert "deployment" in manifests
    deploy_manifest = yaml.safe_load(manifests["deployment"])
    assert deploy_manifest["spec"]["replicas"] == 1
    
    # Valider PVC (stockage important)
    assert "pvc" in manifests
    pvc_manifest = yaml.safe_load(manifests["pvc"])
    assert pvc_manifest["spec"]["resources"]["requests"]["storage"] == "20Gi"
    print("   Stockage: 20Gi PVC pour données")
    
    return manifests

def test_custom_domain_deployment():
    """Test 4: Déploiement avec domaine personnalisé et HTTPS"""
    print("\n🧪 Test 4: Service avec domaine personnalisé + HTTPS")
    
    deploy_request = DeployRequest(
        project_id=3,
        project_name="blog", 
        username="blogger",
        service_name="webapp",
        display_name="Personal Blog",
        
        image_name="ghcr.io/amzhm/blogger-blog-webapp:latest",
        
        replicas=1,
        service_type=ServiceType.WEB,
        exposure_type=ExposureType.EXTERNAL,
        
        container_port=3000,
        service_port=8000,
        
        cpu_request="100m",
        cpu_limit="500m",
        memory_request="128Mi",
        memory_limit="512Mi",
        
        # Domaine personnalisé avec HTTPS
        custom_domain="myblog.example.com",
        custom_path="/",  # Path racine
        enable_https=True,
        
        health_check_path="/health"
    )
    
    deployment_id = "test-custom-domain-001"
    manifests = manifest_generator.generate_manifests(deploy_request, deployment_id)
    
    print(f"✅ Générés: {list(manifests.keys())}")
    
    # Valider Ingress avec HTTPS
    assert "ingress" in manifests
    ingress_manifest = yaml.safe_load(manifests["ingress"])
    
    # Vérifier domaine personnalisé
    assert ingress_manifest["spec"]["rules"][0]["host"] == "myblog.example.com"
    print("   Domaine: myblog.example.com")
    
    # Vérifier HTTPS/TLS
    assert "tls" in ingress_manifest["spec"]
    assert ingress_manifest["spec"]["tls"][0]["hosts"][0] == "myblog.example.com"
    print("   ✅ HTTPS activé avec cert-manager")
    
    # Vérifier path personnalisé  
    path = ingress_manifest["spec"]["rules"][0]["http"]["paths"][0]["path"]
    expected_path = "/(.*)"  # Path racine avec regex
    assert path == expected_path, f"Expected {expected_path}, got {path}"
    print("   Path: / (racine)")
    
    return manifests

def validate_yaml_syntax(manifests: dict, test_name: str):
    """Valider que tous les manifests sont du YAML valide"""
    print(f"\n🔍 Validation YAML - {test_name}")
    
    for manifest_type, manifest_yaml in manifests.items():
        try:
            parsed = yaml.safe_load(manifest_yaml)
            assert parsed is not None
            assert "apiVersion" in parsed
            assert "kind" in parsed
            assert "metadata" in parsed
            assert "name" in parsed["metadata"]
            print(f"   ✅ {manifest_type}: YAML valide")
        except Exception as e:
            print(f"   ❌ {manifest_type}: Erreur YAML - {e}")
            raise

def test_namespace_isolation():
    """Test 5: Vérifier l'isolation des namespaces entre projets"""
    print("\n🧪 Test 5: Isolation des namespaces")
    
    # 3 utilisateurs différents, 2 projets différents
    configs = [
        ("user1", "project-a", "user1-project-a"),
        ("user1", "project-b", "user1-project-b"), 
        ("user2", "project-a", "user2-project-a"),
    ]
    
    namespaces = []
    for username, project_name, expected_ns in configs:
        calculated_ns = manifest_generator._generate_namespace_name(username, project_name)
        namespaces.append(calculated_ns)
        assert calculated_ns == expected_ns, f"Expected {expected_ns}, got {calculated_ns}"
        print(f"   {username}/{project_name} → {calculated_ns}")
    
    # Vérifier que tous les namespaces sont uniques
    assert len(namespaces) == len(set(namespaces)), "Namespaces ne sont pas uniques!"
    print("   ✅ Isolation des namespaces validée")

def main():
    """Exécuter tous les tests de génération de manifests"""
    print("🚀 Tests de Génération des Manifests Kubernetes - NoKube Monitor Service\n")
    
    try:
        # Test isolation namespaces
        test_namespace_isolation()
        
        # Test 1: Frontend exposé publiquement
        frontend_manifests, shared_namespace = test_web_frontend_deployment()
        validate_yaml_syntax(frontend_manifests, "Frontend")
        
        # Test 2: Backend API interne (même namespace)
        backend_manifests = test_backend_api_deployment() 
        validate_yaml_syntax(backend_manifests, "Backend")
        
        # Test 3: Worker sans réseau
        worker_manifests = test_worker_deployment()
        validate_yaml_syntax(worker_manifests, "Worker")
        
        # Test 4: Domaine personnalisé + HTTPS
        custom_manifests = test_custom_domain_deployment()
        validate_yaml_syntax(custom_manifests, "Custom Domain")
        
        print(f"\n✅ TOUS LES TESTS RÉUSSIS!")
        print(f"   - 4 scénarios de déploiement testés")
        print(f"   - {len(frontend_manifests) + len(backend_manifests) + len(worker_manifests) + len(custom_manifests)} manifests générés")
        print(f"   - Validation YAML complète")
        print(f"   - Isolation namespaces validée")
        print(f"   - Patterns DNS path-based testés")
        
        # Sauvegarder des exemples
        print(f"\n💾 Sauvegarde d'exemples dans ./examples/")
        examples_dir = Path("./examples")
        examples_dir.mkdir(exist_ok=True)
        
        # Frontend example
        with open(examples_dir / "frontend-manifests.yaml", "w") as f:
            f.write("# Frontend React - Exposition publique avec Ingress\n")
            for name, manifest in frontend_manifests.items():
                f.write(f"---\n# {name.upper()}\n{manifest}\n\n")
        
        # Backend example  
        with open(examples_dir / "backend-manifests.yaml", "w") as f:
            f.write("# Backend API - Exposition interne avec stockage et autoscaling\n")
            for name, manifest in backend_manifests.items():
                f.write(f"---\n# {name.upper()}\n{manifest}\n\n")
                
        print(f"   ✅ Exemples sauvegardés pour référence")
        
    except Exception as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()