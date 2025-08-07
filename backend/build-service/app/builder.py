import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, AsyncGenerator
import docker
from docker.errors import DockerException

from app.config import settings
from app.schemas import BuildStatus, BuildRequest, BuildStatusResponse

class DockerBuildxService:
    """Service de build avec Docker Buildx"""
    
    def __init__(self):
        import time
        # Retry logic pour Docker-in-Docker qui met du temps à démarrer
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                self.client = docker.from_env()
                self.client.ping()  # Test de connexion
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    # Dernière tentative échouée, on lève l'exception
                    raise e
                print(f"Docker connection attempt {attempt + 1} failed, retrying in 2s: {e}")
                time.sleep(2)
        
        self.active_builds: Dict[str, asyncio.Task] = {}
        
    async def start_build(self, build_request: BuildRequest, status_callback=None) -> str:
        """Démarrer un nouveau build"""
        build_id = str(uuid.uuid4())
        
        # Créer la tâche de build
        task = asyncio.create_task(
            self._execute_build(build_id, build_request, status_callback)
        )
        
        # Stocker la tâche active
        self.active_builds[build_id] = task
        
        return build_id
    
    async def cancel_build(self, build_id: str) -> bool:
        """Annuler un build en cours"""
        if build_id in self.active_builds:
            task = self.active_builds[build_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_builds[build_id]
            return True
        return False
    
    async def _execute_build(self, build_id: str, build_request: BuildRequest, status_callback=None) -> BuildStatusResponse:
        """Exécuter le build avec Docker Buildx"""
        
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
            print(f"Starting build {build_id} for {build_request.repository_url}")
            
            # Authentification GHCR si configurée
            if settings.GHCR_TOKEN and settings.GHCR_USERNAME:
                print(f"Build {build_id}: Authenticating with GHCR")
                await self._docker_login()
            
            # Choisir la stratégie de build
            if build_request.dockerfile_content:
                # Cas 1: Dockerfile fourni par le frontend
                print(f"Build {build_id}: Using custom Dockerfile")
                await self._build_with_custom_dockerfile(build_id, build_request, image_full_name)
            else:
                # Cas 2: Utiliser le Dockerfile existant du repo
                print(f"Build {build_id}: Using existing Dockerfile from repo")
                await self._build_with_existing_dockerfile(build_id, build_request, image_full_name)
            
            # Build réussi
            build_status.status = BuildStatus.SUCCESS
            build_status.completed_at = datetime.now()
            build_status.duration = int((build_status.completed_at - build_status.started_at).total_seconds())
            
        except asyncio.CancelledError:
            build_status.status = BuildStatus.CANCELLED
            build_status.completed_at = datetime.now()
        except Exception as e:
            build_status.status = BuildStatus.FAILED
            build_status.error_message = str(e)
            build_status.completed_at = datetime.now()
        
        finally:
            # Nettoyer la tâche active
            if build_id in self.active_builds:
                del self.active_builds[build_id]
                
            # Appeler la callback pour mettre à jour le storage
            if status_callback:
                status_callback(build_status)
        
        return build_status
    
    async def _build_with_custom_dockerfile(self, build_id: str, build_request: BuildRequest, image_full_name: str):
        """Build avec Dockerfile personnalisé (créé par le frontend)"""
        
        # Build avec Dockerfile en stdin et context GitHub
        await self._run_buildx_command_with_stdin(
            build_id=build_id,
            context_url=str(build_request.repository_url),
            dockerfile_content=build_request.dockerfile_content,
            image_name=image_full_name,
            build_args=build_request.build_args,
            branch=build_request.branch
        )
    
    async def _build_with_existing_dockerfile(self, build_id: str, build_request: BuildRequest, image_full_name: str):
        """Build avec Dockerfile existant dans le repo"""
        
        # Build directement depuis le repo GitHub
        await self._run_buildx_command(
            build_id=build_id,
            context_url=str(build_request.repository_url),
            dockerfile_path="Dockerfile",  # Dockerfile par défaut du repo
            image_name=image_full_name,
            build_args=build_request.build_args,
            branch=build_request.branch
        )
    
    async def _run_buildx_command(
        self, 
        build_id: str, 
        context_url: str, 
        dockerfile_path: str,
        image_name: str,
        build_args: Dict[str, str],
        branch: str = "main"
    ):
        """Exécuter la commande Docker Buildx"""
        
        # Construire la commande buildx
        cmd = [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",  # Platform pour Kind/K8s
            "--push",  # Push directement vers le registry
            "-f", dockerfile_path,
            "-t", image_name,
        ]
        
        # Ajouter les build args
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])
        
        # Context depuis GitHub avec branche spécifique
        github_context = f"{context_url}#{branch}" if branch else context_url
        cmd.append(github_context)
        
        # Exécuter la commande avec logs
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Collecter les logs (pour l'instant basique, on peut améliorer avec streaming)
        stdout, _ = await process.communicate()
        
        if process.returncode != 0:
            stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else "No output"
            raise DockerException(f"Docker buildx failed: {stdout_str}")
    
    async def _run_buildx_command_with_stdin(
        self, 
        build_id: str, 
        context_url: str, 
        dockerfile_content: str,
        image_name: str,
        build_args: Dict[str, str],
        branch: str = "main"
    ):
        """Exécuter Docker Buildx avec Dockerfile en stdin"""
        
        # Construire la commande buildx avec stdin  
        cmd = [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",  # Platform pour Kind/K8s
            # "--push",  # Désactivé temporairement pour test
            "-f", "-",  # Dockerfile depuis stdin
            "-t", image_name,
        ]
        
        # Ajouter les build args
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])
        
        # Context depuis GitHub avec branche spécifique
        github_context = f"{context_url}#{branch}" if branch else context_url
        cmd.append(github_context)
        
        print(f"Build {build_id}: Running buildx with stdin: {' '.join(cmd)}")
        
        # Exécuter la commande avec Dockerfile en stdin
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        # Envoyer le Dockerfile via stdin et collecter les logs
        stdout, _ = await process.communicate(input=dockerfile_content.encode('utf-8'))
        
        if process.returncode != 0:
            stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else "No output"
            raise DockerException(f"Docker buildx failed: {stdout_str}")
    
    async def _docker_login(self):
        """Authentification avec GHCR"""
        cmd = [
            "docker", "login", settings.DOCKER_REGISTRY,
            "-u", settings.GHCR_USERNAME,
            "-p", settings.GHCR_TOKEN
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        if process.returncode != 0:
            raise DockerException("Failed to authenticate with GHCR")
    
    async def get_build_logs(self, build_id: str) -> AsyncGenerator[str, None]:
        """Stream des logs d'un build en cours (à implémenter plus tard)"""
        # Pour l'instant, retourne un message basique
        yield f"Build {build_id} logs streaming not implemented yet"
    
    def get_active_builds(self) -> Dict[str, str]:
        """Retourner la liste des builds actifs"""
        return {build_id: "building" for build_id in self.active_builds.keys()}

# Instance globale du service
docker_service = DockerBuildxService()