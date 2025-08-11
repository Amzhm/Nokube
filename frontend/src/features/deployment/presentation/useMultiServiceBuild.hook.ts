/**
 * Hook pour la gestion multi-services à l'étape Build
 */

'use client';

import { useState, useEffect } from 'react';
import type { ServiceBuildConfig, ProjectArchitecture, BuildConfig, ServiceConfig } from '@/shared/types/deployment.types';

interface UseMultiServiceBuildProps {
  serviceBuildConfigs: ServiceBuildConfig[];
  onChange: (configs: ServiceBuildConfig[]) => void;
  architecture: ProjectArchitecture | null;
}

// Configuration de base par langage
const baseLanguageConfig = {
  javascript: { baseImage: 'node:18-alpine' },
  typescript: { baseImage: 'node:18-alpine' },
  python: { baseImage: 'python:3.11-slim' },
  go: { baseImage: 'golang:1.21-alpine' },
  java: { baseImage: 'openjdk:17-jdk-slim' },
  rust: { baseImage: 'rust:1.70-slim' },
  php: { baseImage: 'php:8.2-fpm' },
  ruby: { baseImage: 'ruby:3.2-slim' },
  csharp: { baseImage: 'mcr.microsoft.com/dotnet/aspnet:7.0' },
  r: { baseImage: 'r-base:4.3.0' },
  scala: { baseImage: 'openjdk:11-jre-slim' },
  kotlin: { baseImage: 'openjdk:17-jdk-slim' },
  dart: { baseImage: 'cirrusci/flutter:stable' },
  elm: { baseImage: 'node:18-alpine' },
  hcl: { baseImage: 'hashicorp/terraform:latest' },
  gdscript: { baseImage: 'barichello/godot-ci:3.5.1' },
};

// Configuration spécifique par framework
const frameworkConfigs = {
  // Frontend SPA - JavaScript
  'react': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    port: '3000',
    dockerfile: 'spa'
  },
  'vue': {
    language: 'javascript', 
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run serve',
    port: '3000',
    dockerfile: 'spa'
  },
  'angular': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'ng serve --host 0.0.0.0',
    port: '4200',
    dockerfile: 'spa'
  },
  'svelte': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '5173',
    dockerfile: 'spa'
  },
  'solid.js': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '3000',
    dockerfile: 'spa'
  },
  'preact': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '3000',
    dockerfile: 'spa'
  },
  'lit': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run serve',
    port: '8000',
    dockerfile: 'spa'
  },
  'alpine.js': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run serve',
    port: '3000',
    dockerfile: 'spa'
  },
  'qwik': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '5173',
    dockerfile: 'spa'
  },

  // Frontend SPA - TypeScript
  'react-ts': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    port: '3000',
    dockerfile: 'spa'
  },
  'vue-ts': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run serve',
    port: '3000',
    dockerfile: 'spa'
  },
  'angular-ts': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'ng serve --host 0.0.0.0',
    port: '4200',
    dockerfile: 'spa'
  },
  'svelte-ts': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '5173',
    dockerfile: 'spa'
  },
  'solid.js-ts': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run dev -- --host 0.0.0.0',
    port: '3000',
    dockerfile: 'spa'
  },

  // Frontend SPA - Autres langages
  'flutter web': {
    language: 'dart',
    buildCommands: ['flutter pub get', 'flutter build web'],
    runCommand: 'flutter run -d web-server --web-port=8080 --web-hostname=0.0.0.0',
    port: '8080',
    dockerfile: 'flutter'
  },
  'elm': {
    language: 'elm',
    buildCommands: ['elm make src/Main.elm --output=main.js'],
    runCommand: 'elm reactor --port=8000',
    port: '8000',
    dockerfile: 'elm'
  },
  
  // Frontend Fullstack - JavaScript/TypeScript
  'next.js': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start', 
    port: '3000',
    dockerfile: 'nextjs'
  },
  'nuxt': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    port: '3000', 
    dockerfile: 'nodejs'
  },
  'sveltekit': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run preview -- --host 0.0.0.0',
    port: '4173',
    dockerfile: 'nodejs'
  },
  'remix': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    port: '3000',
    dockerfile: 'nodejs'
  },
  'astro': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run start -- --host 0.0.0.0',
    port: '3000',
    dockerfile: 'nodejs'
  },
  'solid-start': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm start',
    port: '3000',
    dockerfile: 'nodejs'
  },
  'qwik-city': {
    language: 'javascript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run serve -- --host 0.0.0.0',
    port: '3000',
    dockerfile: 'nodejs'
  },

  // Frontend Fullstack - Python
  'django templates': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt', 'python manage.py collectstatic --noinput', 'python manage.py migrate'],
    runCommand: 'python manage.py runserver 0.0.0.0:8000',
    port: '8000',
    dockerfile: 'python'
  },
  'flask-ssr': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python app.py',
    port: '5000',
    dockerfile: 'python'
  },

  // Frontend Fullstack - PHP
  'laravel blade': {
    language: 'php',
    buildCommands: ['composer install --no-dev', 'php artisan config:cache', 'php artisan view:cache'],
    runCommand: 'php artisan serve --host=0.0.0.0 --port=8000',
    port: '8000',
    dockerfile: 'php'
  },
  'symfony twig': {
    language: 'php',
    buildCommands: ['composer install --no-dev', 'php bin/console cache:clear', 'php bin/console assets:install'],
    runCommand: 'php -S 0.0.0.0:8000 -t public',
    port: '8000',
    dockerfile: 'php'
  },

  // Frontend Fullstack - Java
  'spring boot thymeleaf': {
    language: 'java',
    buildCommands: ['mvn clean package -DskipTests'],
    runCommand: 'java -jar target/app.jar',
    port: '8080',
    dockerfile: 'java'
  },

  // Frontend Fullstack - C#
  'asp.net core mvc': {
    language: 'csharp',
    buildCommands: ['dotnet restore', 'dotnet publish -c Release -o out'],
    runCommand: 'dotnet out/app.dll',
    port: '5000',
    dockerfile: 'dotnet'
  },
  'asp.net core razor': {
    language: 'csharp',
    buildCommands: ['dotnet restore', 'dotnet publish -c Release -o out'],
    runCommand: 'dotnet out/app.dll',
    port: '5000',
    dockerfile: 'dotnet'
  },

  // Frontend Fullstack - Ruby
  'ruby on rails views': {
    language: 'ruby',
    buildCommands: ['bundle install', 'bundle exec rake assets:precompile'],
    runCommand: 'bundle exec rails server -b 0.0.0.0',
    port: '3000',
    dockerfile: 'ruby'
  },

  // Frontend Fullstack - Go
  'go html/template': {
    language: 'go',
    buildCommands: ['go mod download', 'go build -o app .'],
    runCommand: './app',
    port: '8080',
    dockerfile: 'go'
  },
  'gin html': {
    language: 'go',
    buildCommands: ['go mod download', 'go build -o app .'],
    runCommand: './app',
    port: '8080',
    dockerfile: 'go'
  },

  // Frontend Fullstack - Rust
  'actix-web templates': {
    language: 'rust',
    buildCommands: ['cargo build --release'],
    runCommand: './target/release/app',
    port: '8080',
    dockerfile: 'rust'
  },
  
  // Backend JavaScript/TypeScript
  'express': {
    language: 'javascript',
    buildCommands: ['npm install'],
    runCommand: 'node server.js',
    port: '3000',
    dockerfile: 'nodejs'
  },
  'fastify': {
    language: 'javascript',
    buildCommands: ['npm install'],
    runCommand: 'node server.js',
    port: '3000',
    dockerfile: 'nodejs'
  },
  'nestjs': {
    language: 'typescript',
    buildCommands: ['npm install', 'npm run build'],
    runCommand: 'npm run start:prod',
    port: '3000',
    dockerfile: 'nodejs'
  },
  
  // Backend Python
  'django': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt', 'python manage.py migrate'],
    runCommand: 'python manage.py runserver 0.0.0.0:8000',
    port: '8000',
    dockerfile: 'python'
  },
  'flask': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python app.py',
    port: '5000',
    dockerfile: 'python'
  },
  'fastapi': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'uvicorn main:app --host 0.0.0.0 --port 8000',
    port: '8000',
    dockerfile: 'python'
  },
  
  // Data Science - Mainstream Python
  'jupyter': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root',
    port: '8888',
    dockerfile: 'jupyter'
  },
  'streamlit': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'streamlit run app.py --server.port=8501 --server.address=0.0.0.0',
    port: '8501',
    dockerfile: 'python'
  },
  'pandas': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python analysis.py',
    port: '8080',
    dockerfile: 'python'
  },
  'plotly': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python dashboard.py',
    port: '8050',
    dockerfile: 'python'
  },
  
  // DevOps & Monitoring  
  'grafana': {
    language: 'custom',
    buildCommands: [],
    runCommand: 'grafana-server --config=/etc/grafana/grafana.ini',
    port: '3000',
    dockerfile: 'grafana'
  },
  'prometheus': {
    language: 'custom',
    buildCommands: [],
    runCommand: 'prometheus --config.file=/etc/prometheus/prometheus.yml',
    port: '9090', 
    dockerfile: 'prometheus'
  },
  
  // Backend Go
  'gin': {
    language: 'go',
    buildCommands: ['go mod download', 'go build -o app .'],
    runCommand: './app',
    port: '8080',
    dockerfile: 'go'
  },
  'echo': {
    language: 'go', 
    buildCommands: ['go mod download', 'go build -o app .'],
    runCommand: './app',
    port: '8080',
    dockerfile: 'go'
  },
  'fiber': {
    language: 'go',
    buildCommands: ['go mod download', 'go build -o app .'], 
    runCommand: './app',
    port: '3000',
    dockerfile: 'go'
  },
  
  // Backend Java
  'spring boot': {
    language: 'java',
    buildCommands: ['mvn clean package'],
    runCommand: 'java -jar target/app.jar',
    port: '8080',
    dockerfile: 'java'
  },
  
  // Backend PHP
  'laravel': {
    language: 'php',
    buildCommands: ['composer install --no-dev', 'php artisan config:cache'],
    runCommand: 'php artisan serve --host=0.0.0.0 --port=8000',
    port: '8000',
    dockerfile: 'php'
  },
  'symfony': {
    language: 'php',
    buildCommands: ['composer install --no-dev'],
    runCommand: 'php -S 0.0.0.0:8000 -t public',
    port: '8000', 
    dockerfile: 'php'
  },
  
  // Backend Ruby
  'rails': {
    language: 'ruby',
    buildCommands: ['bundle install', 'bundle exec rake assets:precompile'],
    runCommand: 'bundle exec rails server -b 0.0.0.0',
    port: '3000',
    dockerfile: 'ruby'
  },
  'sinatra': {
    language: 'ruby',
    buildCommands: ['bundle install'],
    runCommand: 'ruby app.rb',
    port: '4567',
    dockerfile: 'ruby'
  },
  
  // Backend .NET
  'asp.net core': {
    language: 'csharp',
    buildCommands: ['dotnet restore', 'dotnet publish -c Release -o out'],
    runCommand: 'dotnet out/app.dll',
    port: '5000',
    dockerfile: 'dotnet'
  },
  
  // Backend Rust
  'actix-web': {
    language: 'rust',
    buildCommands: ['cargo build --release'],
    runCommand: './target/release/app',
    port: '8080',
    dockerfile: 'rust'
  },
  'warp': {
    language: 'rust',
    buildCommands: ['cargo build --release'],
    runCommand: './target/release/app',
    port: '3030',
    dockerfile: 'rust'
  },
  'rocket': {
    language: 'rust',
    buildCommands: ['cargo build --release'],
    runCommand: './target/release/app',
    port: '8000',
    dockerfile: 'rust'
  },
  
  // AI/ML - Mainstream Python
  'pytorch': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python train.py',
    port: '8000',
    dockerfile: 'python'
  },
  'tensorflow': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python train.py',
    port: '8000',
    dockerfile: 'python'
  },
  'scikit-learn': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python model.py',
    port: '8000',
    dockerfile: 'python'
  },
  'hugging face': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python transformers_app.py',
    port: '8000',
    dockerfile: 'python'
  },
  
  // Data Engineering - Python (mainstream)
  'apache airflow': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'airflow webserver --port 8080',
    port: '8080',
    dockerfile: 'python'
  },
  'prefect': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'prefect server start',
    port: '4200',
    dockerfile: 'python'
  },
  'dbt': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'dbt serve --host 0.0.0.0 --port 8080',
    port: '8080',
    dockerfile: 'python'
  },
  'pyspark': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python spark_job.py',
    port: '4040',
    dockerfile: 'python'
  },
  'kafka-python': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python kafka_consumer.py',
    port: '8080',
    dockerfile: 'python'
  },
  'apache-beam-python': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python beam_pipeline.py',
    port: '8080',
    dockerfile: 'python'
  },
  'superset': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'superset run -h 0.0.0.0 -p 8088',
    port: '8088',
    dockerfile: 'python'
  },

  // Data Engineering - Java (enterprise)
  'kafka': {
    language: 'java',
    buildCommands: ['mvn clean package'],
    runCommand: 'java -jar target/kafka-app.jar',
    port: '9092',
    dockerfile: 'java'
  },
  'apache flink': {
    language: 'java',
    buildCommands: ['mvn clean package'],
    runCommand: 'java -jar target/flink-app.jar',
    port: '8081',
    dockerfile: 'java'
  },
  'elasticsearch': {
    language: 'java',
    buildCommands: ['mvn clean package'],
    runCommand: 'java -jar target/elasticsearch-client.jar',
    port: '9200',
    dockerfile: 'java'
  },

  // Data Engineering - Scala (big data)
  'spark': {
    language: 'scala',
    buildCommands: ['sbt compile'],
    runCommand: 'sbt run',
    port: '4040',
    dockerfile: 'scala'
  },
  
  // Cybersecurity - Python (mainstream)
  'scapy': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python packet_analyzer.py',
    port: '8080',
    dockerfile: 'python'
  },
  'nmap-python': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python scanner.py',
    port: '8080',
    dockerfile: 'python'
  },
  'burp-suite': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'python security_scanner.py',
    port: '8080',
    dockerfile: 'python'
  },
  
  // DevOps - Mainstream tools
  'ansible': {
    language: 'python',
    buildCommands: ['pip install -r requirements.txt'],
    runCommand: 'ansible-playbook playbook.yml',
    port: '8080',
    dockerfile: 'python'
  },
  'terraform': {
    language: 'hcl',
    buildCommands: [],
    runCommand: 'terraform apply',
    port: '8080',
    dockerfile: 'terraform'
  },
  'jenkins': {
    language: 'java',
    buildCommands: ['mvn clean package'],
    runCommand: 'java -jar target/jenkins-pipeline.jar',
    port: '8080',
    dockerfile: 'java'
  },
  
  // Mobile - Mainstream
  'react native': {
    language: 'javascript',
    buildCommands: ['npm install'],
    runCommand: 'npm start',
    port: '19000',
    dockerfile: 'nodejs'
  },
  'expo': {
    language: 'javascript',
    buildCommands: ['npm install'],
    runCommand: 'expo start',
    port: '19000',
    dockerfile: 'nodejs'
  },
  'flutter': {
    language: 'dart',
    buildCommands: ['flutter pub get'],
    runCommand: 'flutter run -d web-server --web-port=8080',
    port: '8080',
    dockerfile: 'flutter'
  },
  
  // Gaming - Mainstream
  'unity': {
    language: 'csharp',
    buildCommands: ['dotnet restore', 'dotnet build'],
    runCommand: 'dotnet run',
    port: '7777',
    dockerfile: 'dotnet'
  },
  'godot': {
    language: 'gdscript',
    buildCommands: [],
    runCommand: 'godot --headless --server',
    port: '7777',
    dockerfile: 'godot'
  },
};

// Domaines qui groupent les frameworks - TOUS REMIS
const domainTemplates = {
  'web-frontend': {
    label: 'Frontend Web',
    description: 'Applications web client-side (SPA)',
    frameworks: [
      // JavaScript
      'react', 'vue', 'angular', 'svelte', 'solid.js', 'preact', 'lit', 'alpine.js', 'qwik',
      // TypeScript
      'react-ts', 'vue-ts', 'angular-ts', 'svelte-ts', 'solid.js-ts',
      // Autres langages
      'flutter web', 'elm'
    ]
  },
  'web-fullstack': {
    label: 'Frontend Fullstack', 
    description: 'Applications web avec SSR',
    frameworks: [
      // JavaScript/TypeScript SSR
      'next.js', 'nuxt', 'sveltekit', 'remix', 'astro', 'solid-start', 'qwik-city',
      // Python SSR
      'django templates', 'flask-ssr',
      // PHP SSR  
      'laravel blade', 'symfony twig',
      // Java SSR
      'spring boot thymeleaf',
      // C# SSR
      'asp.net core mvc', 'asp.net core razor',
      // Ruby SSR
      'ruby on rails views',
      // Go SSR
      'go html/template', 'gin html',
      // Rust SSR
      'actix-web templates'
    ]
  },
  'web-backend': {
    label: 'Backend API',
    description: 'APIs REST/GraphQL, microservices',
    frameworks: ['express', 'fastify', 'nestjs', 'django', 'flask', 'fastapi', 'gin', 'echo', 'fiber', 'spring boot', 'laravel', 'symfony', 'rails', 'sinatra', 'asp.net core', 'actix-web', 'warp', 'rocket']
  },
  'data-science': {
    label: 'Data Science',
    description: 'Analyse données, notebooks, visualisation',
    frameworks: ['jupyter', 'streamlit', 'pandas', 'plotly']
  },
  'ai-ml': {
    label: 'Intelligence Artificielle',
    description: 'Machine Learning, Deep Learning, AI',
    frameworks: ['pytorch', 'tensorflow', 'scikit-learn', 'hugging face']
  },
  'data-engineering': {
    label: 'Data Engineering',
    description: 'ETL, pipelines, big data',
    frameworks: [
      // Python mainstream
      'apache airflow', 'prefect', 'dbt', 'pyspark', 'kafka-python', 'apache-beam-python', 'superset',
      // Java/Scala enterprise
      'kafka', 'apache flink', 'elasticsearch', 'spark'
    ]
  },
  'cybersecurity': {
    label: 'Cybersécurité',
    description: 'Security analysis, penetration testing',
    frameworks: ['scapy', 'nmap-python', 'burp-suite']
  },
  'devops': {
    label: 'DevOps / Infrastructure',
    description: 'Automation, CI/CD, monitoring',
    frameworks: ['grafana', 'prometheus', 'ansible', 'terraform', 'jenkins']
  },
  'mobile': {
    label: 'Mobile',
    description: 'Applications mobiles cross-platform',
    frameworks: ['react native', 'expo', 'flutter']
  },
  'gaming': {
    label: 'Gaming',
    description: 'Game development engines',
    frameworks: ['unity', 'godot']
  },
  'custom': {
    label: 'Configuration Libre',
    description: 'Je configure tout manuellement',
    frameworks: []
  }
};

// Fonction pour obtenir un template vide
const getEmptyTemplate = () => {
  return {
    framework: '',
    buildCommands: [],
    runCommand: '',
    dependencies: [],
  };
};

// Fonction pour obtenir les options de domaine
const getDomainOptions = () => {
  return Object.entries(domainTemplates).map(([id, config]) => ({
    id,
    label: config.label,
    description: config.description,
  }));
};

export const useMultiServiceBuild = ({ serviceBuildConfigs, onChange, architecture }: UseMultiServiceBuildProps) => {
  const [activeServiceIndex, setActiveServiceIndex] = useState(0);
  const [serviceDomains, setServiceDomains] = useState<Record<number, string>>({});

  // Services qui nécessitent une configuration de build (excluant les BDD)
  const buildableServices = architecture?.services.filter(service => 
    service.type !== 'database'
  ) || [];

  // Initialiser les configs de build pour chaque service buildable
  useEffect(() => {
    if (buildableServices.length > 0 && serviceBuildConfigs.length === 0) {
      const initialConfigs = buildableServices.map(service => {
        const defaultLanguage = getDefaultLanguageForService(service);
        const langConfig = baseLanguageConfig[defaultLanguage];
        const emptyTemplate = getEmptyTemplate();
        
        return {
          serviceName: service.name,
          buildConfig: {
            language: defaultLanguage,
            framework: emptyTemplate.framework,
            buildCommands: emptyTemplate.buildCommands,
            runCommand: emptyTemplate.runCommand,
            dependencies: emptyTemplate.dependencies,
            environmentVars: [],
          },
          dockerConfig: {
            baseImage: langConfig.baseImage,
            dockerfile: '',
            buildArgs: [],
          },
        };
      });
      
      onChange(initialConfigs);
    }
  }, [buildableServices, serviceBuildConfigs.length]);

  const getDefaultLanguageForService = (service: ServiceConfig): keyof typeof baseLanguageConfig => {
    switch (service.type) {
      case 'web':
        return 'javascript';
      case 'api':
        return 'python';
      case 'worker':
        return 'python';
      default:
        return 'javascript';
    }
  };

  const updateServiceBuildConfig = (serviceIndex: number, updates: Partial<ServiceBuildConfig>) => {
    const updatedConfigs = serviceBuildConfigs.map((config, index) =>
      index === serviceIndex ? { ...config, ...updates } : config
    );
    onChange(updatedConfigs);
  };

  const updateBuildConfig = (serviceIndex: number, buildConfig: BuildConfig) => {
    const dockerConfig = {
      baseImage: baseLanguageConfig[buildConfig.language as keyof typeof baseLanguageConfig]?.baseImage || 'node:18-alpine',
      dockerfile: generateDockerfile(buildConfig),
      buildArgs: [],
    };
    
    updateServiceBuildConfig(serviceIndex, { 
      buildConfig,
      dockerConfig,
    });
  };
  
  const setSelectedDomainForService = (serviceIndex: number, domain: string) => {
    setServiceDomains(prev => ({
      ...prev,
      [serviceIndex]: domain
    }));
  };
  
  const getSelectedDomainForService = (serviceIndex: number): string => {
    return serviceDomains[serviceIndex] || '';
  };
  
  const applyDomainTemplate = (serviceIndex: number, domain: string) => {
    // Sauvegarder le domaine pour ce service spécifique
    setSelectedDomainForService(serviceIndex, domain);
    
    if (domain === 'custom') {
      // Mode libre - champs vides
      updateBuildConfig(serviceIndex, {
        language: 'javascript',
        framework: '',
        buildCommands: [],
        runCommand: '',
        dependencies: [],
        environmentVars: [],
      });
    } else {
      // Prendre le premier framework du domaine
      const frameworks = domainTemplates[domain as keyof typeof domainTemplates]?.frameworks || [];
      if (frameworks.length > 0) {
        const firstFramework = frameworks[0];
        applyFrameworkConfig(serviceIndex, firstFramework);
      }
    }
  };

  const applyFrameworkConfig = (serviceIndex: number, frameworkName: string) => {
    const config = frameworkConfigs[frameworkName as keyof typeof frameworkConfigs];
    if (config) {
      updateBuildConfig(serviceIndex, {
        language: config.language,
        framework: frameworkName,
        buildCommands: [...config.buildCommands],
        runCommand: config.runCommand,
        dependencies: [],
        environmentVars: [],
      });
    }
  };
  
  const updateFrameworkSuggestions = (serviceIndex: number, framework: string) => {
    // Utiliser la nouvelle fonction pour appliquer les configs spécifiques
    applyFrameworkConfig(serviceIndex, framework);
  };

  const getDockerfileConfig = (buildConfig: BuildConfig) => {
    const frameworkName = buildConfig.framework.toLowerCase();
    const config = frameworkConfigs[frameworkName as keyof typeof frameworkConfigs];
    
    if (config) {
      return {
        port: config.port,
        dockerfileType: config.dockerfile,
        language: config.language
      };
    }
    
    // Fallback pour les configs non trouvées
    return {
      port: '3000',
      dockerfileType: 'generic',
      language: buildConfig.language
    };
  };
  
  const generateDockerfile = (buildConfig: BuildConfig): string => {
    const langConfig = baseLanguageConfig[buildConfig.language as keyof typeof baseLanguageConfig];
    if (!langConfig) return '';

    const dockerConfig = getDockerfileConfig(buildConfig);
    
    // Utiliser des templates Dockerfile optimises selon le framework
    return generateOptimizedDockerfile(buildConfig, langConfig, dockerConfig);
  };

  const generateOptimizedDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    // Générer selon le type de Dockerfile spécifique au framework
    switch (dockerConfig.dockerfileType) {
      case 'spa':
        return generateSPADockerfile(buildConfig, langConfig, dockerConfig);
      case 'nextjs':
        return generateNextJSDockerfile(buildConfig, langConfig, dockerConfig);
      case 'nodejs':
        return generateNodeJSDockerfile(buildConfig, langConfig, dockerConfig);
      case 'python':
        return generatePythonDockerfile(buildConfig, langConfig, dockerConfig);
      case 'jupyter':
        return generateJupyterDockerfile(buildConfig, langConfig, dockerConfig);
      case 'go':
        return generateGoDockerfile(buildConfig, langConfig, dockerConfig);
      case 'java':
        return generateJavaDockerfile(buildConfig, langConfig, dockerConfig);
      case 'php':
        return generatePHPDockerfile(buildConfig, langConfig, dockerConfig);
      case 'ruby':
        return generateRubyDockerfile(buildConfig, langConfig, dockerConfig);
      case 'rust':
        return generateRustDockerfile(buildConfig, langConfig, dockerConfig);
      case 'dotnet':
        return generateDotNetDockerfile(buildConfig, langConfig, dockerConfig);
      case 'r':
        return generateRDockerfile(buildConfig, langConfig, dockerConfig);
      case 'scala':
        return generateScalaDockerfile(buildConfig, langConfig, dockerConfig);
      case 'grafana':
        return generateGrafanaDockerfile(buildConfig, langConfig, dockerConfig);
      case 'prometheus':
        return generatePrometheusDockerfile(buildConfig, langConfig, dockerConfig);
      case 'terraform':
        return generateTerraformDockerfile(buildConfig, langConfig, dockerConfig);
      case 'godot':
        return generateGodotDockerfile(buildConfig, langConfig, dockerConfig);
      case 'flutter':
        return generateFlutterDockerfile(buildConfig, langConfig, dockerConfig);
      case 'elm':
        return generateElmDockerfile(buildConfig, langConfig, dockerConfig);
      default:
        return generateGenericDockerfile(buildConfig, langConfig, dockerConfig);
    }
  };

  // SPA (React, Vue, Angular)
  const generateSPADockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    const workdir = buildConfig.workingDirectory || '/app';
    return `FROM ${langConfig.baseImage} AS build
WORKDIR ${workdir}

COPY package*.json ./
RUN npm ci

COPY . .
${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

FROM nginx:alpine
COPY --from=build ${workdir}/dist /usr/share/nginx/html
COPY --from=build ${workdir}/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]`;
  };

  // Next.js
  const generateNextJSDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    const workdir = buildConfig.workingDirectory || '/app';
    const port = buildConfig.containerPort || dockerConfig.port;
    return `FROM ${langConfig.baseImage}
WORKDIR ${workdir}

COPY package*.json ./
RUN npm ci

COPY . .
${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Node.js Backend
  const generateNodeJSDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    const workdir = buildConfig.workingDirectory || '/app';
    const port = buildConfig.containerPort || dockerConfig.port;
    return `FROM ${langConfig.baseImage}
WORKDIR ${workdir}

COPY package*.json ./
RUN npm ci

COPY . .
${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Python (général)
  const generatePythonDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    const workdir = buildConfig.workingDirectory || '/app';
    const port = buildConfig.containerPort || dockerConfig.port;
    return `FROM ${langConfig.baseImage}
WORKDIR ${workdir}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Jupyter (spécifique)
  const generateJupyterDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage}
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888
${formatCMD('jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root')}`;
  };

  // Go
  const generateGoDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage} AS builder
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o app .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /app

COPY --from=builder /app/app .

EXPOSE ${dockerConfig.port}
${formatCMD('./app')}`;
  };

  // Java
  const generateJavaDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage} AS build
WORKDIR /app

COPY pom.xml .
COPY src ./src

${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

FROM openjdk:17-jre-slim
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE ${dockerConfig.port}
${formatCMD('java -jar app.jar')}`;
  };

  // Rust
  const generateRustDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage} AS builder
WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app

COPY --from=builder /app/target/release/app .

EXPOSE ${dockerConfig.port}
${formatCMD('./app')}`;
  };

  // PHP
  const generatePHPDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage}
WORKDIR /var/www/html

COPY composer.json composer.lock ./
RUN composer install --no-dev

COPY . .
${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Ruby
  const generateRubyDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage}
WORKDIR /app

COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY . .
${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // .NET
  const generateDotNetDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY *.csproj ./
RUN dotnet restore

COPY . ./
RUN dotnet publish -c Release -o out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app

COPY --from=build /src/out .

EXPOSE ${dockerConfig.port}
${formatCMD('dotnet App.dll')}`;
  };

  // Grafana (spécifique)
  const generateGrafanaDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM grafana/grafana:latest

COPY grafana.ini /etc/grafana/grafana.ini
COPY dashboards/ /var/lib/grafana/dashboards/

EXPOSE 3000
CMD ["grafana-server", "--config=/etc/grafana/grafana.ini"]`;
  };

  // Prometheus (spécifique)
  const generatePrometheusDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM prom/prometheus:latest

COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY rules/ /etc/prometheus/rules/

EXPOSE 9090
CMD ["prometheus", "--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus"]`;
  };

  // R
  const generateRDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM r-base:4.3.0
WORKDIR /app

${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

COPY . .

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Scala
  const generateScalaDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM openjdk:11-jre-slim AS build
WORKDIR /app

COPY build.sbt .
COPY project/ ./project/
RUN sbt update

COPY . .
${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

FROM openjdk:11-jre-slim
WORKDIR /app

COPY --from=build /app/target/scala-*/app.jar .

EXPOSE ${dockerConfig.port}
${formatCMD('java -jar app.jar')}`;
  };

  // Terraform (spécifique)
  const generateTerraformDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM hashicorp/terraform:latest
WORKDIR /app

COPY . .

RUN terraform init

EXPOSE ${dockerConfig.port}
${formatCMD('terraform apply -auto-approve')}`;
  };

  // Godot (spécifique)
  const generateGodotDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM barichello/godot-ci:3.5.1
WORKDIR /app

COPY . .

RUN godot --export "Linux/X11" game.x86_64

EXPOSE ${dockerConfig.port}
${formatCMD('./game.x86_64')}`;
  };

  // Flutter Web (spécifique)
  const generateFlutterDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM cirrusci/flutter:stable
WORKDIR /app

COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get

COPY . .
${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Elm (spécifique)
  const generateElmDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM node:18-alpine
WORKDIR /app

RUN npm install -g elm

COPY elm.json ./
RUN elm make --docs=docs.json

COPY . .
${buildConfig.buildCommands.map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  // Generic fallback
  const generateGenericDockerfile = (buildConfig: BuildConfig, langConfig: any, dockerConfig: any): string => {
    return `FROM ${langConfig.baseImage}
WORKDIR /app

COPY . .
${buildConfig.buildCommands.filter(cmd => cmd.trim()).map(cmd => `RUN ${cmd}`).join('\n')}

EXPOSE ${dockerConfig.port}
${formatCMD(buildConfig.runCommand)}`;
  };

  const formatCMD = (command: string): string => {
    if (!command.trim()) {
      return 'CMD ["echo", "Please configure your run command"]';
    }
    
    // Handle complex commands with pipes, &&, etc.
    if (command.includes('&&') || command.includes('|') || command.includes(';')) {
      return `CMD ["sh", "-c", "${command.replace(/"/g, '\\"')}"]`;
    }
    
    // Handle simple commands
    const cmdParts = command.trim().split(/\s+/);
    if (cmdParts.length === 1) {
      return `CMD ["${cmdParts[0]}"]`;
    }
    
    // Properly escape arguments
    const escapedParts = cmdParts.map(part => part.replace(/"/g, '\\"'));
    return `CMD ["${escapedParts.join('", "')}"]`;
  };

  const getServiceConfigStatus = (index: number) => {
    const config = serviceBuildConfigs[index];
    if (!config) return 'pending';
    
    const { buildConfig } = config;
    if (buildConfig.language && buildConfig.runCommand && buildConfig.buildCommands.length > 0) {
      return 'configured';
    }
    
    return 'partial';
  };

  return {
    buildableServices,
    activeServiceIndex,
    activeService: buildableServices[activeServiceIndex],
    activeServiceBuildConfig: serviceBuildConfigs[activeServiceIndex],
    serviceBuildConfigs,
    availableLanguages: Object.keys(baseLanguageConfig),
    selectedDomain: getSelectedDomainForService(activeServiceIndex),
    domainOptions: getDomainOptions(),
    setSelectedDomain: (domain: string) => setSelectedDomainForService(activeServiceIndex, domain),
    applyDomainTemplate,
    getAvailableLanguagesForDomain: (domain: string) => {
      if (domain === 'custom') return Object.keys(baseLanguageConfig);
      
      // Extraire les langages uniques des frameworks du domaine
      const frameworks = domainTemplates[domain as keyof typeof domainTemplates]?.frameworks || [];
      const languages = new Set<string>();
      
      frameworks.forEach(fw => {
        const config = frameworkConfigs[fw as keyof typeof frameworkConfigs];
        if (config) {
          languages.add(config.language);
        }
      });
      
      return Array.from(languages);
    },
    getFrameworkSuggestions: (domain: string, language: string) => {
      if (domain === 'custom') return [];
      
      // Retourner les frameworks du domaine qui correspondent au langage
      const frameworks = domainTemplates[domain as keyof typeof domainTemplates]?.frameworks || [];
      return frameworks.filter(fw => {
        const config = frameworkConfigs[fw as keyof typeof frameworkConfigs];
        return config && config.language === language;
      });
    },
    updateFrameworkSuggestions,
    setActiveServiceIndex,
    updateBuildConfig,
    generateDockerfile,
    getServiceConfigStatus,
  };
};