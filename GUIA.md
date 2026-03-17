# 🐍 Guia Completo — Memórias com Flask + Python

## Estrutura do projeto

```
memorias-python/
├── app.py                  ← Ponto de entrada Flask
├── extensions.py           ← Supabase, Cloudinary, LoginManager
├── models.py               ← Modelo de usuário (Flask-Login)
├── routes/
│   ├── auth.py             ← Login, cadastro, logout
│   ├── albums.py           ← Dashboard, criar/abrir álbuns
│   └── photos.py           ← Upload (Cloudinary + Supabase), deletar
├── templates/
│   ├── base.html           ← Layout base (header, toast, lightbox)
│   ├── auth.html           ← Tela de login/cadastro
│   ├── dashboard.html      ← Grade de álbuns
│   └── gallery.html        ← Galeria de fotos com upload AJAX
├── requirements.txt
├── Procfile                ← Para o Render fazer o deploy
├── .env                    ← 🔑 Suas chaves (nunca commitar!)
└── .gitignore
```

---

## PASSO 1 — Criar ambiente virtual e instalar dependências

```bash
cd memorias-python

# Cria o ambiente virtual (boa prática em todo projeto Python)
python -m venv venv

# Configuracao apolice
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Ativa o ambiente
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Instala as dependências
pip install -r requirements.txt
```

---

## PASSO 2 — Configurar o Supabase #davidleles_project khQtK7fVGQbekk2p 

### 2.1 — Criar conta e projeto

1. Acesse **supabase.com** → crie uma conta gratuita
2. Clique em **"New Project"**, dê um nome (ex: `memorias`) e uma senha
3. Aguarde ~2 minutos até ficar pronto

### 2.2 — Criar as tabelas

Vá em **SQL Editor** → **New query** e rode:

```sql
-- Tabela de álbuns
CREATE TABLE albums (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  cover_url   TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de fotos
CREATE TABLE photos (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  album_id       UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  url            TEXT NOT NULL,
  cloudinary_id  TEXT NOT NULL,
  caption        TEXT,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Segurança: cada usuário só vê os próprios dados (Row Level Security)
ALTER TABLE albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE photos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_albums" ON albums
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "users_own_photos" ON photos
  FOR ALL USING (auth.uid() = user_id);
```

Clique em **Run** ✅

### 2.3 — Pegar as chaves

**Settings → API** no painel do Supabase:
- **Project URL** → `SUPABASE_URL` **https://atfjivbykgyuqrlxxlyn.supabase.co**
- **service_role** (não o anon!) → `SUPABASE_KEY` **sb_publishable_VTVriMgU2aCxbC8bBwPHiA_gGAAYIXJ**
  > ⚠️ Use a chave `service_role` no backend Flask porque ele roda no servidor,
  > não no browser. Ela tem permissão total — por isso nunca exponha no frontend.

---

## PASSO 3 — Configurar o Cloudinary

1. Acesse **cloudinary.com** → crie uma conta gratuita (25 GB grátis)
2. No dashboard você verá as 3 credenciais:
   - **Cloud Name** → `CLOUDINARY_CLOUD_NAME` **dghcmfgdy**
   - **API Key** → `CLOUDINARY_API_KEY` **958862988454923**
   - **API Secret** → `CLOUDINARY_API_SECRET` **c1GTtWg_AWGv98u2NTVfN93mg1E**

---

## PASSO 4 — Preencher o .env

Edite o arquivo `.env` com suas chaves reais:

```env
SECRET_KEY=cole_aqui_uma_string_aleatoria_longa
SUPABASE_URL=https://abcdefghij.supabase.co
SUPABASE_KEY=eyJhbGci...service_role_key...
CLOUDINARY_CLOUD_NAME=meu_cloud
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=AbCdEfGhIjKlMnOp
```

Para gerar um SECRET_KEY seguro:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## PASSO 5 — Rodar localmente

```bash
# Certifique-se que o venv está ativo
source venv/bin/activate

python app.py
```

Acesse **http://localhost:5000** 🎉

---

## PASSO 6 — Deploy no Render (grátis)

### 6.1 — Subir no GitHub

```bash
git init
git add .
git commit -m "primeiro commit"

# Crie um repositório em github.com e:
git remote add origin https://github.com/SEU_USUARIO/memorias-python.git
git push -u origin main
```

### 6.2 — Criar serviço no Render

1. Acesse **render.com** → crie uma conta (pode logar com GitHub)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte o repositório `memorias-python`
4. Configure:
   - **Name:** memorias (ou o nome que quiser)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

5. Vá em **"Environment"** e adicione as variáveis:

```
SECRET_KEY              = sua_chave_secreta
SUPABASE_URL            = https://xxx.supabase.co
SUPABASE_KEY            = eyJ...
CLOUDINARY_CLOUD_NAME   = seu_cloud
CLOUDINARY_API_KEY      = 000...
CLOUDINARY_API_SECRET   = xxx...
```

6. Clique em **"Create Web Service"** → em ~3 minutos estará no ar! 🚀

### 6.3 — Atualizações futuras

```bash
git add .
git commit -m "minha alteração"
git push
# Render detecta o push e faz re-deploy automaticamente ✨
```

---

## Comparação: Flask vs Next.js

| | Flask (Python) | Next.js (JS) |
|---|---|---|
| **Frontend** | Jinja2 (HTML no servidor) | React (SPA no cliente) |
| **Deploy** | Render | Vercel |
| **Aprendizado** | Mais simples se já sabe Python | Requer conhecer React |
| **Performance** | Boa para uso pessoal | Melhor para escala |
| **Custo** | Grátis (Render free tier dorme após inatividade*) | Grátis (Vercel não dorme) |

> *O plano free do Render "hiberna" após 15 min sem acesso. O primeiro acesso
> demora ~30s para acordar. Para evitar isso, use **Render Cron Job** gratuito
> fazendo ping a cada 10 minutos, ou faça upgrade ($7/mês).

---

## Resumo de custos

| Serviço     | Plano Gratuito             | Custo |
|-------------|----------------------------|-------|
| Flask       | Open source                | R$ 0  |
| Render      | 750h/mês grátis            | R$ 0  |
| Supabase    | 500 MB banco               | R$ 0  |
| Cloudinary  | 25 GB storage              | R$ 0  |
| **Total**   |                            | **R$ 0** |

---

## Próximas features para adicionar

- [ ] Editar nome/descrição do álbum
- [ ] Adicionar legenda às fotos no upload
- [ ] Compartilhar álbum com link público
- [ ] Baixar álbum como ZIP
- [ ] Ordenar fotos por data
