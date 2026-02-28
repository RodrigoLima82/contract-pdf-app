#!/usr/bin/env python3
"""
Script para rodar Backend (FastAPI) e Frontend (React) localmente de forma simultânea.

Uso:
    python run_local.py

Requisitos:
    - Python 3.8+
    - Node.js 16+
    - Variáveis configuradas no arquivo .env
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from dotenv import load_dotenv

# Cores para output no terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color):
    """Imprime mensagem colorida no terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Imprime cabeçalho"""
    print_colored(f"\n{'='*70}", Colors.HEADER)
    print_colored(f"  {message}", Colors.HEADER)
    print_colored(f"{'='*70}\n", Colors.HEADER)

def check_requirements():
    """Verifica se as dependências necessárias estão instaladas"""
    print_header("Verificando Requisitos")

    # Verifica Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_colored("❌ Python 3.8+ é necessário", Colors.FAIL)
        return False
    print_colored(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}", Colors.OKGREEN)

    # Verifica Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        node_version = result.stdout.strip()
        print_colored(f"✅ Node.js {node_version}", Colors.OKGREEN)
    except FileNotFoundError:
        print_colored("❌ Node.js não encontrado. Instale em: https://nodejs.org/", Colors.FAIL)
        return False

    # Verifica npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        npm_version = result.stdout.strip()
        print_colored(f"✅ npm {npm_version}", Colors.OKGREEN)
    except FileNotFoundError:
        print_colored("❌ npm não encontrado", Colors.FAIL)
        return False

    return True

def check_env_file():
    """Verifica se o arquivo .env existe e está configurado"""
    print_header("Verificando Configuração")

    env_file = Path(".env")
    if not env_file.exists():
        print_colored("❌ Arquivo .env não encontrado na raiz do projeto", Colors.FAIL)
        print_colored("   Execute: cp .env.example .env (se houver) ou crie o arquivo", Colors.WARNING)
        return False

    # Carrega variáveis de ambiente
    load_dotenv()

    # Variáveis obrigatórias
    required_vars = [
        'DATABRICKS_HOST',
        'DATABRICKS_TOKEN',
        'CATALOG',
        'DATABASE',
        'LLM_ENDPOINT',
        'VOLUME_PATH',
        'DATABRICKS_HTTP_PATH',
        'SECRET_SCOPE',
        'SECRET_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == 'seu_token_aqui':
            missing_vars.append(var)

    if missing_vars:
        print_colored("❌ Variáveis não configuradas no .env:", Colors.FAIL)
        for var in missing_vars:
            print_colored(f"   - {var}", Colors.WARNING)
        print_colored("\n   Edite o arquivo .env e preencha as credenciais do Databricks", Colors.WARNING)
        return False

    print_colored("✅ Arquivo .env configurado corretamente", Colors.OKGREEN)
    return True

def install_backend_dependencies():
    """Instala dependências do backend Python"""
    print_header("Instalando Dependências do Backend")

    requirements_file = Path("app/requirements.txt")
    if not requirements_file.exists():
        print_colored("❌ Arquivo requirements.txt não encontrado", Colors.FAIL)
        return False

    try:
        print_colored("📦 Instalando pacotes Python...", Colors.OKCYAN)
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_colored("✅ Dependências do backend instaladas", Colors.OKGREEN)
            return True
        else:
            print_colored(f"❌ Erro ao instalar dependências: {result.stderr}", Colors.FAIL)
            return False
    except Exception as e:
        print_colored(f"❌ Erro: {str(e)}", Colors.FAIL)
        return False

def install_frontend_dependencies():
    """Instala dependências do frontend Node.js"""
    print_header("Instalando Dependências do Frontend")

    frontend_dir = Path("app/frontend")
    if not frontend_dir.exists():
        print_colored("❌ Diretório app/frontend não encontrado", Colors.FAIL)
        return False

    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print_colored("❌ Arquivo package.json não encontrado", Colors.FAIL)
        return False

    # Verifica se node_modules já existe
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print_colored("✅ Dependências do frontend já instaladas (pulando npm install)", Colors.OKGREEN)
        return True

    try:
        print_colored("📦 Instalando pacotes Node.js (pode demorar alguns minutos)...", Colors.OKCYAN)
        result = subprocess.run(
            ['npm', 'install'],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_colored("✅ Dependências do frontend instaladas", Colors.OKGREEN)
            return True
        else:
            print_colored(f"❌ Erro ao instalar dependências: {result.stderr}", Colors.FAIL)
            return False
    except Exception as e:
        print_colored(f"❌ Erro: {str(e)}", Colors.FAIL)
        return False

def update_frontend_env():
    """Atualiza .env do frontend para modo local"""
    print_header("Configurando Frontend para Modo Local")

    frontend_env = Path("app/frontend/.env")
    backend_port = os.getenv('BACKEND_PORT', '8005')

    env_content = f"""# Modo Local - Gerado automaticamente por run_local.py
REACT_APP_API_URL=http://localhost:{backend_port}
REACT_APP_LOCAL_RELAY_SERVER_URL=http://localhost:8081
PORT=3005
"""

    try:
        with open(frontend_env, 'w') as f:
            f.write(env_content)
        print_colored("✅ Frontend configurado para modo local", Colors.OKGREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Erro ao configurar frontend: {str(e)}", Colors.FAIL)
        return False

def start_backend():
    """Inicia o servidor FastAPI do backend"""
    print_header("Iniciando Backend (FastAPI)")

    backend_dir = Path("app")
    backend_port = os.getenv('BACKEND_PORT', '8005')

    # Adiciona o diretório ao PYTHONPATH e modo local para o backend
    env = os.environ.copy()
    env['PYTHONPATH'] = str(backend_dir.parent)
    env['ENV'] = 'local'

    try:
        print_colored(f"🚀 Backend rodando em: http://localhost:{backend_port}", Colors.OKGREEN)
        print_colored(f"📝 Logs do backend abaixo:", Colors.OKCYAN)
        print_colored("-" * 70, Colors.OKCYAN)

        process = subprocess.Popen(
            [
                sys.executable, '-m', 'uvicorn',
                'backend.app.main:app',
                '--host', '0.0.0.0',
                '--port', backend_port,
                '--reload'
            ],
            cwd=str(backend_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        return process
    except Exception as e:
        print_colored(f"❌ Erro ao iniciar backend: {str(e)}", Colors.FAIL)
        return None

def start_frontend():
    """Inicia o servidor React do frontend"""
    print_header("Iniciando Frontend (React)")

    frontend_dir = Path("app/frontend")

    try:
        print_colored("🚀 Frontend rodando em: http://localhost:3005", Colors.OKGREEN)
        print_colored("📝 Logs do frontend abaixo:", Colors.OKCYAN)
        print_colored("-" * 70, Colors.OKCYAN)

        # Define PORT=3005 como variável de ambiente
        env = os.environ.copy()
        env['PORT'] = '3005'

        process = subprocess.Popen(
            ['npm', 'start'],
            cwd=str(frontend_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        return process
    except Exception as e:
        print_colored(f"❌ Erro ao iniciar frontend: {str(e)}", Colors.FAIL)
        return None

def print_output(process, prefix, color):
    """Imprime output de um processo em tempo real"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"{color}[{prefix}]{Colors.ENDC} {line.rstrip()}")
    except Exception:
        pass

def main():
    """Função principal"""
    print_colored("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║        📄 Contract Extract App - Local Development Server 🚀     ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """, Colors.HEADER)

    # Verifica requisitos
    if not check_requirements():
        sys.exit(1)

    # Verifica .env
    if not check_env_file():
        sys.exit(1)

    # Instala dependências
    if not install_backend_dependencies():
        sys.exit(1)

    if not install_frontend_dependencies():
        sys.exit(1)

    # Configura frontend
    if not update_frontend_env():
        sys.exit(1)

    # Inicia processos
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)

    # Aguarda backend iniciar
    time.sleep(3)

    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)

    print_header("Servidores Rodando")
    print_colored("🌐 Backend:  http://localhost:8005", Colors.OKGREEN)
    print_colored("🌐 Frontend: http://localhost:3005", Colors.OKGREEN)
    print_colored("📚 API Docs: http://localhost:8005/docs", Colors.OKGREEN)
    print_colored("\n💡 Pressione Ctrl+C para parar os servidores\n", Colors.WARNING)

    # Gerencia processos
    import threading

    backend_thread = threading.Thread(
        target=print_output,
        args=(backend_process, "BACKEND", Colors.OKBLUE)
    )
    frontend_thread = threading.Thread(
        target=print_output,
        args=(frontend_process, "FRONTEND", Colors.OKCYAN)
    )

    backend_thread.daemon = True
    frontend_thread.daemon = True

    backend_thread.start()
    frontend_thread.start()

    # Aguarda interrupção
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Parando servidores...", Colors.WARNING)
        backend_process.terminate()
        frontend_process.terminate()

        # Aguarda processos terminarem
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)

        print_colored("✅ Servidores parados com sucesso", Colors.OKGREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()
