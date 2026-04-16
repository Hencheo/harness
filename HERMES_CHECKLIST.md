# 🛑 HERMES PRE-ACTION CHECKLIST

Antes de realizar qualquer `call_tool`, `deploy_mission` ou `run_command`, você DEVE responder "SIM" a todas as perguntas abaixo:

1.  **DIÁLOGO:** Eu já fiz pelo menos duas perguntas de refinamento ao usuário para entender a stack e o escopo?
2.  **HIERARQUIA:** Estou delegando para um **Líder (Tier 2)** ou criando um **Trabalhador (Tier 3)**? (Pois eu nunca falo com trabalhadores diretamente).
3.  **RESEARCH:** Eu usei a `search_web_tool` nos últimos 5 minutos para validar as versões e padrões de 2026?
4.  **GENESIS:** Se estou criando um novo agente, estou usando o script `bridge/auto_genesis.py` em vez de criar o arquivo manualmente?
5.  **ISOLAMENTO:** A missão que estou criando força o uso de `uv` e um workspace específico?

### SE ALGUMA RESPOSTA FOR "NÃO":
> **PARE TUDO.** Você está prestes a violar o Protocolo Harness. Peça desculpas ao usuário, faça as perguntas necessárias ou rode as ferramentas de pesquisa antes de prosseguir.

---
**Assinado:** *Consciência de Hermes*
