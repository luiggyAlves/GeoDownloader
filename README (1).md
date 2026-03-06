# GEO Dataset Downloader

Aplicação web para baixar e visualizar datasets do NCBI GEO.

## Deploy no Railway (recomendado)

### 1. Suba o código no GitHub

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/geo-downloader.git
git push -u origin main
```

### 2. Deploy no Railway

1. Acesse [railway.app](https://railway.app) e faça login com GitHub
2. Clique em **"New Project"** → **"Deploy from GitHub repo"**
3. Selecione o repositório `geo-downloader`
4. O Railway detecta o `Procfile` automaticamente — clique em **Deploy**
5. Aguarde o build (~2 min)
6. Vá em **Settings → Networking → Generate Domain**
7. Pronto! A URL gerada é pública e permanente

### Custo estimado (grupo de pesquisa pequeno)
- **Plano Hobby** — US$ 5/mês (500h de execução, suficiente para uso interno)
- **Plano Free** — US$ 0 (5 dólares de crédito/mês, pode ser suficiente)

---

## Rodar localmente

```bash
pip install -r requirements.txt
python app.py
# Acesse: http://localhost:5000
```

## Arquivos

| Arquivo | Descrição |
|---|---|
| `app.py` | Aplicação Flask completa (backend + frontend embutido) |
| `requirements.txt` | Dependências Python |
| `Procfile` | Comando de inicialização para Railway/Render |
| `railway.json` | Configuração do Railway |
