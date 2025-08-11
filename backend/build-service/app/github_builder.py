import asyncio
import uuid
import json
import base64
from datetime import datetime
from typing import Optional, Dict
from github import Github, GithubException
import httpx
import time

from app.config import settings
from app.schemas import BuildStatus, BuildRequest, BuildStatusResponse


class GitHubActionsBuilder:
    """Service de build avec GitHub Actions au lieu de Docker Buildx"""
    
    def __init__(self):
        # GitHub API client avec le token NoKube
        self.github_client = Github(settings.GITHUB_TOKEN)
        self.build_repo = settings.GITHUB_BUILD_REPO  # "Amzhm/nokube-builds"
        self.http_client = httpx.AsyncClient()
        self.active_builds: Dict[str, asyncio.Task] = {}
        
        # Vérifier l'accès au repo de build
        try:
            self.repo = self.github_client.get_repo(self.build_repo)
            print(f"Connected to GitHub repo: {self.build_repo}")
        except GithubException as e:
            print(f"Failed to access GitHub repo {self.build_repo}: {e}")
            raise e
    
    async def start_build(self, build_request: BuildRequest, status_callback=None, username: str = None) -> str:
        """Démarrer un nouveau build avec GitHub Actions"""
        build_id = str(uuid.uuid4())
        
        # Créer la tâche de build
        task = asyncio.create_task(
            self._execute_github_build(build_id, build_request, status_callback, username)
        )
        
        # Stocker la tâche active
        self.active_builds[build_id] = task
        
        return build_id
    
    async def cancel_build(self, build_id: str) -> bool:
        """Annuler un build en cours (cancellation du workflow GitHub)"""
        if build_id in self.active_builds:
            task = self.active_builds[build_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_builds[build_id]
            
            # TODO: Implémenter l'annulation du workflow GitHub si nécessaire
            return True
        return False
    
    async def _execute_github_build(
        self, 
        build_id: str, 
        build_request: BuildRequest, 
        status_callback=None,
        username: str = None
    ) -> BuildStatusResponse:
        """Exécuter le build avec GitHub Actions"""
        
        # Image complète avec registry
        image_full_name = f"{settings.DOCKER_REGISTRY}/{settings.DOCKER_NAMESPACE}/{build_request.image_name}:{build_request.image_tag}"
        
        build_status = BuildStatusResponse(
            build_id=build_id,
            project_id=build_request.project_id,
            status=BuildStatus.BUILDING,
            image_full_name=image_full_name,
            created_at=datetime.now(),
            started_at=datetime.now()
        )
        
        try:
            print(f"Starting GitHub Actions build {build_id} for {build_request.repository_url}")
            
            # Étape 1: Créer/mettre à jour le Dockerfile dans nokube-builds
            dockerfile_path = await self._upload_dockerfile(build_id, build_request, username)
            print(f"Dockerfile uploaded to: {dockerfile_path}")
            
            # Étape 2: Déclencher le workflow GitHub Actions
            workflow_run_id = await self._trigger_workflow(build_id, build_request, dockerfile_path)
            print(f"GitHub workflow triggered: {workflow_run_id}")
            
            # Étape 3: Démarrer le monitoring en arrière-plan (ne pas attendre)
            asyncio.create_task(self._monitor_workflow_background(workflow_run_id, build_id, build_status, status_callback))
            
            # Retourner immédiatement avec le statut "building"
            print(f"Build {build_id} started, monitoring in background")
                
        except asyncio.CancelledError:
            build_status.status = BuildStatus.CANCELLED
            build_status.completed_at = datetime.now()
            print(f"Build {build_id} cancelled")
        except Exception as e:
            build_status.status = BuildStatus.FAILED
            build_status.error_message = str(e)
            build_status.completed_at = datetime.now()
            print(f"Build {build_id} error: {e}")
            # Nettoyer la tâche active en cas d'erreur immédiate
            if build_id in self.active_builds:
                del self.active_builds[build_id]
            # Mettre à jour le storage en cas d'erreur
            if status_callback:
                status_callback(build_status)
        
        return build_status
    
    async def _upload_dockerfile(self, build_id: str, build_request: BuildRequest, username: str = None) -> str:
        """Upload du Dockerfile dans le repo nokube-builds organisé par utilisateur/projet"""
        
        # Path organisé par utilisateur et nom d'image
        username = username or "anonymous"
        project_name = build_request.image_name
        dockerfile_path = f"projects/{username}/{project_name}/Dockerfile"
        
        # Contenu du Dockerfile (fourni par le frontend ou par défaut)
        dockerfile_content = build_request.dockerfile_content or "FROM alpine:latest\nCMD echo 'No Dockerfile provided'"
        
        # Créer ou mettre à jour le fichier dans le repo
        try:
            # Vérifier si le fichier existe déjà
            try:
                existing_file = self.repo.get_contents(dockerfile_path)
                # Mettre à jour le fichier existant
                self.repo.update_file(
                    path=dockerfile_path,
                    message=f"Update Dockerfile for {username}/{project_name}",
                    content=dockerfile_content,
                    sha=existing_file.sha
                )
            except GithubException:
                # Le fichier n'existe pas, le créer
                self.repo.create_file(
                    path=dockerfile_path,
                    message=f"Add Dockerfile for {username}/{project_name}",
                    content=dockerfile_content
                )
            
            print(f"Dockerfile uploaded to {self.build_repo}:{dockerfile_path}")
            return dockerfile_path
            
        except GithubException as e:
            raise Exception(f"Failed to upload Dockerfile: {e}")
    
    async def _trigger_workflow(self, build_id: str, build_request: BuildRequest, dockerfile_path: str) -> int:
        """Déclencher le workflow GitHub Actions"""
        
        # Inputs pour le workflow
        workflow_inputs = {
            "build_id": build_id,
            "dockerfile_path": dockerfile_path,
            "source_repo": str(build_request.repository_url).replace("https://github.com/", ""),
            "source_branch": build_request.branch or "main",
            "image_name": build_request.image_name,
            "image_tag": build_request.image_tag or "latest",
            "registry": settings.DOCKER_REGISTRY,
            "namespace": settings.DOCKER_NAMESPACE,
            "build_args": json.dumps(build_request.build_args) if build_request.build_args else "{}"
        }
        
        try:
            # Déclencher le workflow via l'API GitHub
            workflow = self.repo.get_workflow("build-image.yml")
            workflow_dispatch = workflow.create_dispatch(
                ref="main",
                inputs=workflow_inputs
            )
            
            # Attendre quelques secondes pour que le run soit créé
            await asyncio.sleep(3)
            
            # Récupérer le workflow run ID le plus récent
            runs = workflow.get_runs()
            latest_run = runs[0]
            
            print(f"Workflow dispatched: {latest_run.id}")
            return latest_run.id
            
        except GithubException as e:
            raise Exception(f"Failed to trigger GitHub workflow: {e}")
    
    async def _monitor_workflow(self, workflow_run_id: int, build_id: str, timeout: int = 600) -> bool:
        """Surveiller le statut du workflow GitHub Actions"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Récupérer le statut du workflow run
                workflow_run = self.repo.get_workflow_run(workflow_run_id)
                status = workflow_run.status
                conclusion = workflow_run.conclusion
                
                print(f"Build {build_id} status: {status}, conclusion: {conclusion}")
                
                if status == "completed":
                    return conclusion == "success"
                
                # Attendre avant le prochain check
                await asyncio.sleep(10)
                
            except GithubException as e:
                print(f"Error checking workflow status: {e}")
                await asyncio.sleep(5)
        
        # Timeout atteint
        print(f"Build {build_id} timed out after {timeout}s")
        return False
    
    async def _monitor_workflow_background(self, workflow_run_id: int, build_id: str, build_status: BuildStatusResponse, status_callback):
        """Surveiller le workflow en arrière-plan sans bloquer l'event loop principal"""
        
        try:
            success = await self._monitor_workflow(workflow_run_id, build_id)
            
            if success:
                build_status.status = BuildStatus.SUCCESS
                build_status.completed_at = datetime.now()
                build_status.duration = int((build_status.completed_at - build_status.started_at).total_seconds())
                print(f"Build {build_id} completed successfully")
            else:
                build_status.status = BuildStatus.FAILED
                build_status.error_message = "GitHub Actions workflow failed"
                build_status.completed_at = datetime.now()
                print(f"Build {build_id} failed")
                
        except Exception as e:
            build_status.status = BuildStatus.FAILED
            build_status.error_message = str(e)
            build_status.completed_at = datetime.now()
            print(f"Build {build_id} monitoring error: {e}")
        
        finally:
            # Nettoyer la tâche active
            if build_id in self.active_builds:
                del self.active_builds[build_id]
                
            # Appeler la callback pour mettre à jour le storage
            if status_callback:
                status_callback(build_status)
    
    def get_active_builds(self) -> Dict[str, str]:
        """Retourner la liste des builds actifs"""
        return {build_id: "building" for build_id in self.active_builds.keys()}
    
    async def get_build_logs(self, build_id: str):
        """Récupérer les logs d'un build (depuis GitHub Actions)"""
        # Pour l'instant, retourne un message basique
        # TODO: Implémenter la récupération des logs GitHub Actions
        yield f"GitHub Actions build {build_id} - logs streaming from GitHub API not implemented yet"


# Instance globale du service
github_builder = GitHubActionsBuilder()