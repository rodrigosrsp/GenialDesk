# GenialDesk — Lista de Tarefas

Fork do RustDesk v1.4.6 customizado para identidade Genial Care.  
Repositório de trabalho: `https://github.com/rodrigosrsp/rustdesk.git`  
Upstream: `https://github.com/rustdesk/rustdesk.git`

---

## Estado Atual (2026-04-17)

- **Rebranding visual:** ~40% concluído
- **3 commits** não pushados para o repositório
- **15 arquivos** modificados não commitados (ver seção de commit abaixo)
- **Arquivos novos** não rastreados: `genie/`, `genial-agent-zerotrust.py`, `src/telemetry.rs`

---

## FASE 1 — Commit e Repositório

### 1.1 Commitar mudanças pendentes
```bash
cd /srv/GenialDesk
git add Cargo.toml flutter/pubspec.yaml flutter/android/ flutter/ios/ \
        flutter/macos/ flutter/windows/ flutter/lib/ src/flutter_ffi.rs \
        src/lib.rs src/rendezvous_mediator.rs src/server.rs libs/hbb_common
git commit -m "chore: rebranding parcial GenialDesk v1.4.6"

# Arquivos novos (framework genie + agent)
git add genie/ genial-agent-zerotrust.py src/telemetry.rs
git commit -m "feat: adiciona genie framework, zero-trust agent e telemetria customizada"
```

### 1.2 Criar repositório dedicado no GitHub
- Criar `genialcare/genialdesk` (ou `rodrigosrsp/genialdesk`) no GitHub
- Configurar como privado
- Adicionar novo remote:
```bash
git remote rename origin old-origin
git remote add origin https://github.com/NOVO_REPO.git
git push -u origin master
```
- Manter `upstream` apontando para o RustDesk oficial

---

## FASE 2 — Rebranding Completo

### 2.1 Cargo.toml (Rust) — PENDENTE
- [ ] Linha `name = "rustdesk"` → `name = "genialdesk"`
- [ ] `ProductName = "RustDesk"` → `ProductName = "GenialDesk"`
- [ ] Verificar todas as referências a "rustdesk" no Cargo.toml
- [ ] Testar que o build Rust ainda funciona após rename

### 2.2 Package IDs / Bundle Identifiers — PENDENTE
- [ ] Android: `com.carriez.flutter_hbb` → `com.genialcare.genialdesk`
  - `flutter/android/app/build.gradle` (applicationId)
  - `flutter/android/app/src/main/AndroidManifest.xml`
- [ ] iOS: `com.carriez.flutterHbb` → `com.genialcare.GenialDesk`
  - `flutter/ios/Runner/Info.plist` (CFBundleIdentifier)
  - URL scheme: `rustdesk` → `genialdesk`
- [ ] macOS: `com.carriez.flutterHbb` → `com.genialcare.GenialDesk`
  - `flutter/macos/Runner/Configs/AppInfo.xcconfig`
- [ ] Windows: verificar registry/installer IDs

### 2.3 Copyright e Metadados — PENDENTE
- [ ] macOS: `Copyright © 2025 Purslane Ltd.` → `Copyright © 2025 Genial Care`
- [ ] Windows: resources do Runner.rc (FileDescription, LegalCopyright)
- [ ] Cargo.toml: `authors`, `description`, `homepage`
- [ ] pubspec.yaml: adicionar `homepage`, `description`

### 2.4 Ícones e Assets — PENDENTE
- [ ] Verificar se `res/` contém ícones ainda do RustDesk vanilla
- [ ] Substituir ícones em `res/` pelo logo Genial
- [ ] Android: `flutter/android/app/src/main/res/mipmap-*/` → ícones Genial
- [ ] iOS: `flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/`
- [ ] macOS: `flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/`
- [ ] Windows: `flutter/windows/runner/resources/app_icon.ico`
- [ ] Linux: ícone em `res/`

### 2.5 Strings e Internacionalização — PENDENTE
- [ ] Verificar `src/lang/*.rs` para strings com "RustDesk"
- [ ] Verificar strings em `flutter/lib/` referenciando "RustDesk"
- [ ] `flutter/lib/common.dart`: confirmar que `isCustomClient()` está configurado
- [ ] Definir strings customizadas no mecanismo de custom client

### 2.6 Deep Links e URL Schemes — PENDENTE
- [ ] iOS `Info.plist`: scheme `rustdesk` → `genialdesk`
- [ ] Android `AndroidManifest.xml`: intent-filter scheme → `genialdesk`
- [ ] Atualizar lógica de tratamento de deep links no Dart

---

## FASE 3 — Infra e Servidor

### 3.1 Servidor de Rendezvous (HBBS/HBBR) — VALIDAR
- [ ] Confirmar que `rendezvous_mediator.rs` aponta para o servidor Genial (não para o RustDesk público)
- [ ] Validar configuração de `RENDEZVOUS_SERVER` em produção
- [ ] Confirmar que os containers `hbbs` e `hbbr` do Docker Compose do GenialHub estão operacionais

### 3.2 Custom Client Build — PENDENTE
- [ ] Configurar `custom-client.toml` ou equivalente para `isCustomClient()` retornar true
- [ ] Definir servidor padrão, logo, e configurações de branding no custom client config
- [ ] Documentar como gerar builds customizados (custom-server flag)

### 3.3 CI/CD — REVISAR
- [ ] `.github/workflows/flutter-build.yml` — Verificar se targets de build estão corretos para GenialDesk
- [ ] Atualizar `bridge.yml` se necessário
- [ ] Configurar secrets do GitHub para novo repositório (chaves de assinatura, etc.)
- [ ] Configurar release automático por tag (`flutter-tag.yml`)

---

## FASE 4 — Integração com GenialHub

### 4.1 Zero-Trust Agent
- [ ] Integrar `genial-agent-zerotrust.py` como daemon no agente desktop
- [ ] Configurar autenticação via Bearer `genial-agent-secret`
- [ ] Implementar checkin periódico com o GenialHub 2.0 backend
- [ ] Implementar kill switch: se retornar 403 → desconectar e parar

### 4.2 Telemetria
- [ ] Revisar `src/telemetry.rs` — definir quais métricas coletar
- [ ] Integrar telemetria com endpoint do GenialHub 2.0 (`/api/agents/heartbeat`)
- [ ] Garantir que dados de telemetria não saem para servidores externos

### 4.3 genial_id e agent_id
- [ ] Verificar que `agent_id = hex(SHA256(serial_number + MAC))` está implementado
- [ ] Garantir que o agente nunca gera `genial_id` — apenas recebe do Hub
- [ ] Implementar fluxo: pending_login → active → removed (trust_state)

### 4.4 OAuth Zero Trust
- [ ] Callback local: `http://localhost:47821/callback`
- [ ] Domínio OAuth: `genialcare.com.br`
- [ ] Fluxo de autorização documentado e testado

---

## FASE 5 — Genie Framework (Agents)

### 5.1 Estado atual (`genie/`)
- `agent.py` — GenieAgent com force-continue
- `skills.py` — ForceContinueUntilDone skill
- `SKILL.md`, `README.md` — documentação em pt-BR

### 5.2 Próximos passos
- [ ] Integrar Ollama local como backend LLM para os agents
- [ ] Criar skills de diagnóstico (read-only): logs, disk, services, DB
- [ ] Criar skill de "proposta de ação" — agent propõe, Rodrigo aprova, então executa
- [ ] Implementar skill de monitoramento do GenialHub backend
- [ ] Criar skill de restart controlado de serviços (com confirmação)
- [ ] Documentar protocolo de segurança: sem alterar dados sem confirmação

---

## FASE 6 — Distribuição

### 6.1 Plataformas-alvo
- [ ] Linux (AppImage / Flatpak) — principal para o ambiente de produção Genial
- [ ] Windows — agentes nos dispositivos de clientes
- [ ] macOS — se necessário
- [ ] Android/iOS — depende do roadmap

### 6.2 Auto-update
- [ ] Definir mecanismo de atualização (update server do GenialDesk ou GenialHub)
- [ ] Configurar `update-server` no custom client config
- [ ] Testar fluxo de atualização automática

---

## Regras de Negócio (não alterar sem confirmação de Rodrigo)

| Regra | Valor |
|-------|-------|
| `agent_id` | `hex(SHA256(serial_number + MAC))` — âncora física, nunca muda |
| `genial_id` | 8 chars [A-Z0-9] — gerado PELO Hub, nunca pelo agente |
| `trust_state` | pending_login → active → removed |
| Kill switch | 403 = dispositivo removed, desconectar imediatamente |
| Person-device | exclusivo 1:1 — desvincula o antigo automaticamente |
| OAuth domain | `genialcare.com.br` |
| Agent secret | `Bearer genial-agent-secret` |
| OAuth callback local | `http://localhost:47821/callback` |
