# Instrucciones para Push a GitHub

## Estado Actual ✅
- 2 commits creados localmente:
  1. `cc2942b` - feat: Implementar core models y CVaR risk metrics (Phase 1)
  2. `c4620e4` - docs: Add comprehensive README with CVaR explanation and Fintual alignment
- 31 archivos comprometidos
- 58 tests pasando

## Pasos para Subir a GitHub

### 1. Crear Repositorio en GitHub.com

1. Ve a: https://github.com/new
2. Configura:
   - **Repository name**: `fintual-portfolio-showcase`
   - **Description**: `Sistema avanzado de rebalanceo de portfolios con CVaR Risk Metrics - Showcase técnico para Fintual`
   - **Visibility**: Public
   - **NO marques** ninguna opción de inicialización (README, .gitignore, license)
3. Click "Create repository"

### 2. Conectar y Pushear

Después de crear el repositorio, copia la URL que aparecerá (algo como `https://github.com/gfdiazc/fintual-portfolio-showcase.git`)

Luego ejecuta estos comandos desde la terminal en `/Users/gfdiazc/Projects/claude/fintual/`:

```bash
# Agregar el remote (reemplaza <TU_USERNAME> con tu usuario de GitHub)
git remote add origin https://github.com/<TU_USERNAME>/fintual-portfolio-showcase.git

# Verificar que se agregó correctamente
git remote -v

# Push del código (branch master)
git push -u origin master
```

### 3. Verificar

Después del push, ve a tu repositorio en GitHub y deberías ver:
- README.md bien formateado con badges
- Estructura de carpetas completa
- 2 commits en el historial

## Alternativa: Con GitHub CLI

Si tienes GitHub CLI instalado (`gh`), puedes hacer todo en un solo comando:

```bash
gh repo create fintual-portfolio-showcase --public --source=. --remote=origin --push
```

## Troubleshooting

### Error: "remote origin already exists"
```bash
git remote remove origin
# Luego ejecuta de nuevo el comando git remote add
```

### Error de autenticación
Si te pide contraseña, necesitas usar un Personal Access Token:
1. Ve a: https://github.com/settings/tokens
2. "Generate new token (classic)"
3. Permisos: `repo` (todos los sub-permisos)
4. Copia el token y úsalo como contraseña

### Cambiar de master a main (opcional)
Si prefieres usar `main` como branch principal:
```bash
git branch -M main
git push -u origin main
```

## Próximos Pasos Después del Push

1. ✅ Verificar que el README se vea bien en GitHub
2. 📧 Compartir el link del repositorio con Fintual en tu postulación
3. 🚀 Continuar con Phase 2: SimpleRebalanceStrategy
4. 📝 Documentar conversaciones LLM en `docs/llm_conversations/`

---

**¿Necesitas ayuda?** Si tienes algún problema con el push, avísame y te ayudo a resolverlo.
