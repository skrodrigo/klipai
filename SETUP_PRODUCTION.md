# Setup Produção - Kastraclip

## Estrutura

```bash
c:\Users\r\codes\
├── kastraclip/
│   ├── backend/          # PIP (venv)
│   ├── web/              # Frontend (pnpm)
│   └── docker-compose.yml
└── FunClip/              # PIP (venv do backend)
```

## 1. Iniciar Docker (PostgreSQL + RabbitMQ)

```bash
cd kastraclip
docker-compose up -d
```

Verifica se está rodando:
```bash
docker-compose ps
```

## 2. Instalar Backend (PIP + venv)

```bash
cd kastraclip/backend
python -m venv venv
source venv/bin/activate 
```

## 3. Instalar FunClip (PIP - Mesma Venv)

```bash
cd c:\Users\r\codes\FunClip
pip install -r ./requirements.txt
```

## 4. Instalar Dependências do Sistema

```bash

# Ubuntu/Debian
apt-get -y update && apt-get -y install ffmpeg imagemagick

```

## 5. Gerar Migrations

```bash
cd kastraclip/backend
source venv/bin/activate  
python manage.py makemigrations clips
python manage.py migrate
```

## 6. Configurar Variáveis de Ambiente

Atualizar `backend/.env`:

```env
# Database (Docker)
DATABASE_URL=postgres://kastra:kastra@localhost:5432/kastraclip

# Celery + RabbitMQ (Docker)
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=rpc://

# FunClip
FUNCLIP_ENABLED=true
FFMPEG_PATH=ffmpeg
FFMPEG_TIMEOUT=600
```

## 7. Iniciar Serviços

```bash
# Terminal 1: Docker (já rodando)
docker compose up -d

# Terminal 2: Backend Django
cd kastraclip/backend
source venv/bin/activate  
python manage.py runserver 

# Terminal 3: Celery Worker
cd kastraclip/backend
source venv/bin/activate 
celery -A core worker -l info

# Terminal 4: Frontend
cd kastraclip/web
pnpm dev
```


## Logs

Verificar logs do Celery:

```bash
# Terminal 3 mostra logs em tempo real
celery -A core worker -l info

# Ou arquivo de log
tail -f celery.log
```


## Próximas Etapas

- [ ] Integrar S3 para armazenamento
- [ ] Implementar autenticação/autorização
- [ ] Adicionar suporte a múltiplos idiomas
- [ ] Implementar agendamento de clips
- [ ] Integrar com redes sociais (TikTok, Instagram, YouTube)
